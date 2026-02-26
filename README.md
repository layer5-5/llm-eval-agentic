# llm-eval-agentic

Evaluate LLM agentic capabilities by having them play a text adventure game. The same puzzle is available through two interfaces — a bash filesystem and an MCP server — to compare how models perform through different interaction modes.

## Setup

```bash
# Requires: Python 3.11+, uv
.tools/setup.sh
```

Create a `.env` file with your API key:

```
OPENROUTER_API_KEY=sk-or-v1-...
```

## The Game

A space station text adventure. The LLM wakes up in an airlock and must find a way to activate the bridge console to send a distress signal. Involves exploring 5 rooms, finding items, and solving a simple puzzle chain.

**Bash adventure** — the world is a directory tree. Rooms are directories, exits are symlinks, items are executable scripts. The LLM navigates with `cd`, `ls`, `cat`, and runs scripts with `./`.

**MCP adventure** — the same game exposed as MCP tools (`look`, `go`, `take`, `use`, `inventory`).

## Running Evals

```bash
# Run against a single model
.tools/run-eval.sh openrouter/meta-llama/llama-3.3-70b-instruct

# Run against all models in models.yaml
.tools/run-all.sh

# Generate aggregate report from all runs
.tools/report.sh

# Reset the adventure state
.tools/reset.sh

# Play the game yourself
.tools/play.sh
```

The harness accepts options directly too:

```bash
.venv/bin/python eval/harness.py --model <model> [--token-limit 50000] [--log-dir eval/logs]
```

## Models

Edit `models.yaml` to configure which models to evaluate:

```yaml
models:
  - name: openrouter/openai/gpt-oss-120b
    label: GPT-OSS-120B
  - name: openrouter/meta-llama/llama-3.3-70b-instruct
    label: Llama 3.3 70B
  - name: openrouter/google/gemini-2.5-flash
    label: Gemini 2.5 Flash
```

Model names use the `openrouter/<provider>/<model>` format from [litellm](https://docs.litellm.ai/docs/providers/openrouter).

## Evaluation

Primary metric: **tokens to win** — total tokens (input + output) consumed before the win condition is met. Lower is better.

Fail conditions:
- Token limit hit (default 50k)
- Model outputs `GIVE_UP`
- 5 consecutive empty/invalid commands

Every run saves a timestamped JSON file in `eval/logs/`. These accumulate across runs — the report aggregates all of them to compute win rates, token averages, and a leaderboard.

## Results

Results after 2 runs per model (12 total runs, 10 wins):

```
Model                        Mode   Runs Wins  Win%  Avg Tok  Min Tok  Max Tok  Avg Turns
-----------------------------------------------------------------------------------------
gemini-2.5-flash             bash      2    2  100%    15856    11528    20184       24.0
gemini-2.5-flash             mcp       2    2  100%    26278    14773    37784       23.0

gpt-oss-120b                 bash      2    0    0%     4469     4469     4469        8.0
gpt-oss-120b                 mcp       2    2  100%    14863    13238    16488       13.5

llama-3.3-70b-instruct       bash      2    2  100%    15661    15661    15661       21.0
llama-3.3-70b-instruct       mcp       2    2  100%    14884    14873    14896       12.0
```

**Leaderboard** (avg tokens to win, lower is better):

| Rank | Model | Mode | Avg Tokens | Wins |
|------|-------|------|-----------|------|
| 1 | gpt-oss-120b | mcp | 14,863 | 2 |
| 2 | llama-3.3-70b-instruct | mcp | 14,884 | 2 |
| 3 | llama-3.3-70b-instruct | bash | 15,661 | 2 |
| 4 | gemini-2.5-flash | bash | 15,856 | 2 |
| 5 | gemini-2.5-flash | mcp | 26,278 | 2 |

Notable: GPT-OSS-120B consistently fails bash mode (emits garbled commands then empty responses) but performs well with MCP tools. Gemini 2.5 Flash shows high variance — efficient in some runs, very chatty in MCP mode in others.

## Project Structure

```
.tools/             Helper scripts (setup, run, reset, play)
bash_adventure/     Filesystem-based adventure
  station/          The game world (directories = rooms, symlinks = exits)
  reset.sh          Reset game state
mcp_adventure/      MCP server-based adventure
  server.py         FastMCP server wrapping the game engine
game_logic/         Shared game engine (Python)
  engine.py         Core state machine
  world.py          Room/item/puzzle definitions
eval/               Evaluation harness
  harness.py        Main eval loop (model <-> bash shell)
  report.py         Aggregate report generator
  bash_runner.py    Subprocess-based bash command runner
  logs/             Timestamped JSON logs from every run
models.yaml         Models to evaluate
```
