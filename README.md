# EMNLP-2026-perspective-transformation-in-LLMs

## Introduction

This repository is for our work published at EMNLP 2026 *From Route to Survey: Probing Spatial Perspective Transformation in Large Language Models*.

The `data` folder contains the training set and test set for each task. Files are in jsonl format. The `data/generator` folder contains all scripts to generate datasets.

The `train` folder contains finetuning and zero-shot evaluation scripts. Specifically, `main.py` is used for the main experiments (*i.e.*, finetune a language model, test the finetuned model). The `generalisation_inter_template.py` script is used for evaluating generalisation ability across different templates. The `generalisation_inter_perspective.py` script is used for evaluating generalisation ability across different combinations, within one template. The `scalability.py` is used for finetuning and evaluating different models in Qwen-3.5 family. The `zeroshot_open.py` is used to evaluate LLMs in the zero-shot setting. Use 

```
python3 scripte_name --help
```

to see all possible arguments.

## Citation
If you use this code or data, please consider citing our paper:

```
@inproceedings{zhang2026perspective,
    title = "From Route to Survey: Probing Spatial Perspective Transformation in Large Language Models",
    author = "Zhang, Haotong",
    booktitle = "Findings of the Association for Computational Linguistics: EMNLP 2026",
    year = "2026",
    address = "Budapest, Hungary",
}
```
