import os
import json
import random
import argparse
import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer, AutoConfig, Trainer, TrainingArguments, DataCollatorWithPadding
import datasets
import evaluate
from peft import LoraConfig, TaskType, get_peft_model, PeftModel

parser = argparse.ArgumentParser()
parser.add_argument('--data', type=str, default='../data', help='data set directory')
parser.add_argument('--ckpt', type=str, default='../model', help='path to store checkpoint')
parser.add_argument('--pred', type=str, default='../data/pred/generalisation2', help='directory path to store predictions')
parser.add_argument('--seed', type=int, default=42, help='random seed')

parser.add_argument('-n', '--name', type=str, required=True, help='language model')
parser.add_argument('-b', '--batch', type=int, default=8, help='batch size')
parser.add_argument('-e', '--epoch', type=int, default=3, help='training epoch.')
parser.add_argument('--lr', type=float, default=1e-4, help='learning rate')

parser.add_argument('-t', '--template', type=str, required=True, help='which template')
parser.add_argument('-d1', '--ft_description', type=str, required=True, help='finetune description type')
parser.add_argument('-d2', '--test_description', type=str, required=True, help='test description type')
parser.add_argument('-q', '--question', type=str, required=True, help='question type')

parser.add_argument('--rank', type=int, default=8, help='lora rank dimension')
parser.add_argument('--alpha', type=int, default=16, help='lora alpha')
parser.add_argument('--dropout', type=float, default=0.1, help='lora dropout')
args = parser.parse_args()

SURVEY_DIRECTIONS = ['north', 'northeast', 'east', 'southeast', 'south', 'southwest', 'west', 'northwest']
ROUTE_DIRECTIONS = ['left', 'right', 'front', 'back']

random.seed(args.seed)
np.random.seed(args.seed)
torch.manual_seed(args.seed)
torch.cuda.manual_seed(args.seed)
torch.cuda.manual_seed_all(args.seed)


def model_name(name):
    if name == 'llama':
        model_name = 'meta-llama/Llama-3.1-8B-Instruct'
    elif name == 'qwen':
        model_name = 'Qwen/Qwen3.5-9B'
    else:
        raise ValueError('Please choose a name from llama or qwen!')
    return model_name


def data_process(data):
    # we only need to consider the description type of the test set
    if args.test_description == 'route' and args.question == 'survey':
        additional_info = f' Assume that at the start of the description you are facing {data["route_initial"]}. Use this information to answer the following question.'
    else:
        additional_info = ''

    text = data[args.test_description] + additional_info + ' ' + data['question']
    enc = tokenizer(text, truncation=True)
    enc['labels'] = SURVEY_DIRECTIONS.index(data['answer']) if args.question == 'survey' else ROUTE_DIRECTIONS.index(data['answer'])
    return enc


def compute_metrics(eval_preds):
    metric = evaluate.load('accuracy')
    logits, labels = eval_preds
    predictions = np.argmax(logits, axis=-1)
    return metric.compute(predictions=predictions, references=labels)


device = torch.device('cuda:0' if torch.cuda.is_available() else 'mps')
tokenizer = AutoTokenizer.from_pretrained(model_name(args.name), use_fast=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = 'right'

if args.name == 'qwen':
    id2label = {i: ROUTE_DIRECTIONS[i] for i in range(len(ROUTE_DIRECTIONS))} if args.question == 'route' else \
        {i: SURVEY_DIRECTIONS[i] for i in range(len(SURVEY_DIRECTIONS))}
    config = AutoConfig.from_pretrained(model_name(args.name), num_labels=4 if args.question == 'route' else 8,
                                        text_config={'num_labels': 4 if args.question == 'route' else 8,
                                                     'id2label': id2label})
    base_model = AutoModelForSequenceClassification.from_pretrained(model_name(args.name), low_cpu_mem_usage=True,
                                                                    torch_dtype='bfloat16', device_map='auto',
                                                                    config=config)
else:
    base_model = AutoModelForSequenceClassification.from_pretrained(model_name(args.name), low_cpu_mem_usage=True,
                                                                    torch_dtype='bfloat16', device_map='auto',
                                                                    num_labels=4 if args.question == 'route' else 8)
base_model.config.get_text_config().pad_token_id = tokenizer.pad_token_id

train_dataset = datasets.load_dataset('json', data_files=f'{args.data}/template{args.template}_{args.question}_train.jsonl', split=datasets.Split.TRAIN)
train_dataset = train_dataset.map(data_process, batched=False, remove_columns=train_dataset.column_names)
test_dataset = datasets.load_dataset('json', data_files=f'{args.data}/template{args.template}_{args.question}_test.jsonl', split=datasets.Split.TRAIN)
test_dataset = test_dataset.map(data_process, batched=False, remove_columns=test_dataset.column_names)
data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

train_config = TrainingArguments(
    output_dir=f'{args.ckpt}/t{args.template}_{args.ft_description}_{args.question}/{args.name}_{args.seed}',
    eval_strategy='epoch',
    per_device_train_batch_size=args.batch,
    per_device_eval_batch_size=args.batch,
    learning_rate=args.lr,
    num_train_epochs=args.epoch,
    log_level='info',
    save_strategy='best',
    save_total_limit=1,
    disable_tqdm=False,
    metric_for_best_model='accuracy',
    report_to='none',
    remove_unused_columns=False,
    label_names=['labels']
)

peft_config = LoraConfig(
    r=args.rank,
    lora_alpha=args.alpha,
    lora_dropout=args.dropout,
    target_modules=['q_proj', 'v_proj', 'k_proj', 'o_proj'],
    task_type=TaskType.SEQ_CLS,
    modules_to_save=['classifier'],
)

model = get_peft_model(base_model, peft_config)
model.print_trainable_parameters()

trainer = Trainer(
    model=model,
    args=train_config,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
    processing_class=tokenizer,
    compute_metrics=compute_metrics,
    data_collator=data_collator,
)

ckpt_dir = f'{args.ckpt}/t{args.template}_{args.ft_description}_{args.question}/{args.name}_{args.seed}'
peft_model = PeftModel.from_pretrained(base_model, f'{ckpt_dir}/{os.listdir(ckpt_dir)[0]}', torch_dtype='bfloat16')
merged_model = peft_model.merge_and_unload()
trainer.model = merged_model

pred = trainer.predict(test_dataset)
pred_labels = pred.predictions.argmax(-1).tolist()

f = open(f'{args.data}/template{args.template}_{args.question}_test.jsonl')
data = f.readlines()
f.close()

with open(f'{args.pred}/template{args.template}_{args.ft_description}_{args.test_description}_{args.question}_{args.name}_{args.seed}.jsonl', 'w') as f:
    for d, p in zip(data, pred_labels):
        d = json.loads(d.strip())
        d['pred'] = SURVEY_DIRECTIONS[p] if args.question == 'survey' else ROUTE_DIRECTIONS[p]
        print(json.dumps(d), file=f)
