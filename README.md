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