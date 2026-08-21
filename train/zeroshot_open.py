import json
import logging
import argparse
from tqdm import tqdm
import torch
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument('--data', type=str, default='../data', help='data set directory')
parser.add_argument('--pred', type=str, default='../data/pred', help='directory path to store predictions')
parser.add_argument('-n', '--name', type=str, required=True, help='model name')
parser.add_argument('-t', '--template', type=str, required=True, help='which template')
parser.add_argument('-d', '--description', type=str, required=True, help='description type')
parser.add_argument('-q', '--question', type=str, required=True, help='question type')
parser.add_argument('-b', '--batch', type=int, default=8, help='batch size')
args = parser.parse_args()

SURVEY_DIRECTIONS = ['north', 'northeast', 'east', 'southeast', 'south', 'southwest', 'west', 'northwest']
ROUTE_DIRECTIONS = ['left', 'right', 'front', 'back']


def model_name(name):
    if name == 'llama':
        model_name = 'meta-llama/Llama-3.1-8B-Instruct'
    elif name == 'qwen':
        model_name = 'Qwen/Qwen3.5-9B'
    else:
        raise ValueError('Please choose a name from llama or qwen!')
    return model_name


class SpatialData(Dataset):
    def __init__(self, datapath, args):
        f = open(datapath)
        datalist = f.readlines()
        f.close()
        self.data = [json.loads(d) for d in datalist]
        self.args = args

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        description = self.data[idx][self.args.description]
        question = self.data[idx]['question']

        if self.args.description == 'route' and self.args.question == 'survey':
            additional_info = f'Assume that at the start of the description you are facing {self.data[idx]["route_initial"]}. Use this information to answer the following question. '
        else:
            additional_info = ''

        if self.args.question == 'route':
            choices = 'Choose answer from left, right, front and back. Only give your answer.'
        else:
            choices = 'Choose answer from north, south, east, west, northeast, northwest, southeast, southwest. Only give your answer.'

        prompt = f"""You will read a description of an area and answer a question.\n\nDescription:\n{description}\n\nQuestion:\n{additional_info}{question}\n{choices}\n\nAnswer:\n"""

        return prompt


tokenizer = AutoTokenizer.from_pretrained(model_name(args.name), use_fast=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = 'left'

if args.name == 'qwen':
    id2label = {i: ROUTE_DIRECTIONS[i] for i in range(len(ROUTE_DIRECTIONS))} if args.question == 'route' else \
        {i: SURVEY_DIRECTIONS[i] for i in range(len(SURVEY_DIRECTIONS))}
    config = AutoConfig.from_pretrained(model_name(args.name), num_labels=4 if args.question == 'route' else 8,
                                        text_config={'num_labels': 4 if args.question == 'route' else 8,
                                                     'id2label': id2label})
    model = AutoModelForCausalLM.from_pretrained(model_name(args.name), low_cpu_mem_usage=True, torch_dtype='bfloat16',
                                                 device_map='auto', config=config)
else:
    model = AutoModelForCausalLM.from_pretrained(model_name(args.name), low_cpu_mem_usage=True, torch_dtype='bfloat16',
                                                 device_map='auto', num_labels=4 if args.question == 'route' else 8)
model.config.get_text_config().pad_token_id = tokenizer.pad_token_id
model.generation_config.pad_token_id = tokenizer.pad_token_id

model.eval()
test_dataset = SpatialData(f'{args.data}/template{args.template}_{args.question}_test.jsonl', args)
test_dataloader = DataLoader(test_dataset, args.batch, shuffle=False)

with torch.no_grad():
    pred = []
    for prompt in tqdm(test_dataloader):
        inputs = tokenizer(prompt, padding=True, truncation=True, return_tensors='pt')
        inputs = {k: inputs[k].to(model.device) for k in inputs.keys()}
        generated_ids = model.generate(**inputs, max_new_tokens=5, do_sample=False)[:, inputs['input_ids'].shape[1]:]
        pred.extend(tokenizer.batch_decode(generated_ids, skip_special_tokens=True))

    data_file = open(f'{args.data}/template{args.template}_{args.question}_test.jsonl')
    data = data_file.readlines()
    data_file.close()
    assert len(data) == len(pred)

    f = open(f'{args.pred}/template{args.template}_{args.description}_{args.question}_{args.name}_zs.jsonl', 'w')
    for d, p in zip(data, pred):
        d = json.loads(d.strip())
        newd = {'id': d['id'], 'up': d['up'], 'route_initial': d['route_initial'], 'description': d[args.description],
                'question': d['question'], 'answer': d['answer'], 'pred': p}
        print(json.dumps(newd), file=f)
    f.close()
