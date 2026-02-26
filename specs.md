# llm-eval-agentic – one-off version

One-file script that runs a single YAML task twice (once against a local CLI tool, once against an MCP HTTP endpoint) and prints a tiny comparison table.  
No installs beyond Python 3.11+ and `httpx` (`pip install httpx`).

## Files
- `eval.py` – the whole thing
- `task.yaml` – your task definition

## task.yaml example
name: count_words
steps:
  - tool: wc
    input: hello world
expected: "1 2 11"

## Run
python eval.py task.yaml

## Output
=LOCAL=  ✔ 0.12 s  123 tokens
=MCP=   ✘ 0.45 s  456 tokens
