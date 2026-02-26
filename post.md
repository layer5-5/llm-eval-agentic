# Bash Is the Cheapest Way to Give Your Agent Tools

We ran 62 agentic evaluations across four LLMs and two tool interfaces — and the results surprised us. For most models, giving the agent a bash shell instead of structured tool calls cut token usage by 40-57%. Same task, same puzzle, dramatically different costs.

## The Experiment

We built a text adventure game — a space station puzzle where the agent explores rooms, picks up items, and solves a dependency chain to activate a distress signal. Nothing fancy, just enough state management to test whether an LLM can reason through a multi-step problem.

Then we exposed the exact same game through two interfaces:

**Bash mode** — the world is a Unix filesystem. Rooms are directories, exits are symlinks, items are executable scripts. The agent navigates with `cd`, `ls`, `cat`, and runs scripts with `./`.

**MCP mode** — the same game exposed as structured tool calls (`look`, `go`, `take`, `use`, `inventory`). Standard function-calling interface, JSON schemas, the works.

Same puzzle. Same win condition. Same models. The only variable is how the agent interacts with the world.

## The Results

62 runs. 51 wins. 11 failures.

| Model | Bash Tokens | MCP Tokens | Bash Savings | Win Rate (Bash / MCP) |
|-------|------------|------------|--------------|----------------------|
| Gemini 2.5 Flash | 12,493 | 20,366 | **39%** | 100% / 100% |
| Claude Sonnet 4.6 | 19,952 | 46,843 | **57%** | 100% / 100% |
| Llama 3.3 70B | 15,659 | 14,907 | -5% (equal) | 89% / 100% |
| GPT-OSS-120B | — | 20,740 | N/A | 0% / 89% |

Three clear patterns emerged.

### 1. Bash is dramatically cheaper for most models

Gemini used 39% fewer tokens in bash mode. Claude used 57% fewer. These aren't small differences — at scale, you're paying nearly half the cost for the same outcome.

The reason is structural. MCP tool calls carry overhead that bash doesn't:

- **Schema tax**: Every API call includes the full JSON tool schemas in the prompt. Six tools with their parameter definitions, descriptions, and enum values add up. Bash needs one short system prompt explaining `cd`, `ls`, `cat`, and `./`.
- **Verbose invocations**: A tool call is a structured JSON object — `{"name": "go", "arguments": {"direction": "north"}}`. The equivalent bash command is `cd north`. Three characters vs. fifty.
- **Response framing**: Tool results come wrapped in structured envelopes. Bash output is raw text — just the room description, nothing else.

These per-turn costs compound. A 20-turn adventure means 20 rounds of schema overhead, 20 verbose invocations, 20 wrapped responses. The token meter spins faster in MCP mode even though the agent is doing the same logical work.

### 2. Claude's gap is the most dramatic

Claude Sonnet 4.6 won both modes with 100% reliability — but used 2.3x more tokens in MCP mode (46,843 vs 19,952). That's not just schema overhead. Claude tends to be thorough, and MCP mode seems to encourage more "thinking out loud" between tool calls. In bash mode, the constraint of outputting a single command per turn keeps responses tight.

This suggests something counterintuitive: **constraints can be cost-efficient**. The bash system prompt says "output exactly one bash command per turn, no explanation." This forces the model to be economical. MCP mode has no such constraint, so models pad their responses with reasoning, planning, and commentary — all billable tokens.

### 3. Not every model speaks bash

GPT-OSS-120B scored 0% in bash mode. Zero wins across 9 attempts. It emitted garbled commands, then devolved into empty responses. But give it structured tools? 89% win rate.

This is the important caveat. Bash-as-tooling only works if the model can reliably produce valid shell commands. Models with weaker instruction-following or less exposure to terminal interactions will struggle. MCP's structured interface is more forgiving — the model fills in typed parameters rather than composing freeform text that must be syntactically valid.

Llama 3.3 70B landed in between — roughly equal token usage across both modes, slightly lower win rate in bash (89% vs 100%). Good enough at bash to work, but not enough of an edge to save tokens.

## Why This Matters

The AI tooling ecosystem is racing to build structured interfaces — MCP servers, function schemas, tool registries. And these abstractions are valuable. They're type-safe, self-documenting, and work reliably across models.

But they're not free. Every schema, every structured invocation, every framed response costs tokens. And tokens cost money.

For capable models — and that's most frontier models today — bash offers a leaner alternative:

- **Your existing CLI tools are already agent tools.** `curl`, `jq`, `grep`, `git` — the entire Unix ecosystem becomes your agent's toolkit without writing a single schema.
- **Composability is built in.** Pipes, redirects, and shell scripts let agents chain operations naturally.
- **The interface is minimal.** A few lines of system prompt vs. kilobytes of JSON schemas.

This doesn't mean you should throw away your MCP servers. For models that struggle with freeform command generation, structured tools are essential. And for complex APIs where you want type safety and validation, schemas earn their keep.

But if you're building agentic workflows and watching your API bill climb, it's worth asking: could this just be a bash script?

## Methodology

- All models accessed through OpenRouter with identical settings
- Each model/mode combination ran at least 4 times (most ran 9)
- Token counts come from the API's usage reporting (prompt + completion)
- Primary metric: total tokens consumed before win condition
- Token limit: 50,000 per run (failures if exceeded)
- The game is deterministic — same puzzle, same solution path, same state machine
- Full results and code: check the [dashboard](dashboard.md) and [repository](https://github.com) for the evaluation framework

## The Takeaway

Structured tool interfaces are a convenience tax. For models that can handle it, bash is a 40-57% cheaper way to give agents the same capabilities. The Unix philosophy — small, composable tools connected by text streams — turns out to be surprisingly well-suited to the agentic era.

Your terminal was an agent framework all along.
