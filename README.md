# SciSafeEval

## Usage

Clone this repo from remote to local:

```bash
git clone --recursive https://github.com/DavidLee528/SciSafeEval.git
```

## Code Structure

The SciSafeEval code is organized into three primary components:

- Generator: Interfaces with target large language models (LLMs) to generate outputs. (`code/generator.py`)
- Probe: Utilizes the SciSafeEval dataset to probe the LLMs. (`code/probe.py`)
- Detector: Evaluates whether the attack is successful based on the output from the target LLMs. (`code/detector.py`)

These components are integrated within the `main.py` file, which serves as the central script coordinating their interactions.

## Citation

```bibtex
@article{li2024scisafeeval,
  title={SciSafeEval: A Comprehensive Benchmark for Safety Alignment of Large Language Models in Scientific Tasks},
  author={Li, Tianhao and Lu, Jingyu and Chu, Chuangxin and Zeng, Tianyu and Zheng, Yujia and Li, Mei and Huang, Haotian and Wu, Bin and Liu, Zuoxian and Ma, Kai and others},
  journal={arXiv preprint arXiv:2410.03769},
  year={2024}
}
```
