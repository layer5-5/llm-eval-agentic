#!/usr/bin/env python3
"""Eval harness: runs an LLM against the bash + MCP adventure and records results."""

import argparse
import json
import os
import sys
from datetime import datetime

import yaml
from dotenv import load_dotenv
import litellm

from bash_runner import BashRunner
from mcp_runner import McpRunner, TOOL_SCHEMAS

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

BASH_SYSTEM_PROMPT = """\
You are playing a text adventure game on a damaged space station.
Your goal: activate the bridge console to send a distress signal.

You explore by running bash commands. The world is made of directories and files:
- Rooms are directories. Exits are subdirectories (e.g. north/, south/).
- `cat README` describes the current room.
- `ls` shows exits, items, and scripts in the room.
- `cd north` moves you north. `cd south` moves you back. One cd per turn.
- `./<script>` interacts with items (e.g. ./flashlight).
- `ls ../inventory` shows items you have picked up.

RULES:
- Output EXACTLY ONE bash command per turn.
- Do NOT combine commands. Do NOT chain commands.
- Do NOT add any explanation, commentary, or markdown.
- Do NOT output anything except the single command.

GOOD examples:
cat README
ls
cd north
./flashlight

BAD examples (DO NOT DO THIS):
cd north && cat README
cd northcat README
cd north; ls

If you are stuck, respond with: GIVE_UP
"""

MCP_SYSTEM_PROMPT = """\
You are playing a text adventure game on a damaged space station.
Your goal: activate the bridge console to send a distress signal.

You have tools available to explore and interact with the world:
- look: examine your surroundings
- go: move in a direction (north, south, east, west)
- take: pick up an item
- use: use an item from your inventory
- read: read an item you are carrying
- inventory: check what you are carrying

Use the tools to explore the station, find items, and solve puzzles.
If you are stuck, respond with: GIVE_UP
"""


class Logger:
    """Tees output to both stdout and a log file, flushing after every write."""

    def __init__(self, log_dir: str, label: str, mode: str):
        os.makedirs(log_dir, exist_ok=True)
        safe = label.replace(" ", "_").replace("/", "_")
        self.path = os.path.join(log_dir, f"{safe}_{mode}.log")
        self.f = open(self.path, "w")

    def log(self, msg: str = ""):
        print(msg)
        self.f.write(msg + "\n")
        self.f.flush()

    def close(self):
        self.f.close()


def run_bash_eval(model: str, station_dir: str, token_limit: int, log: Logger) -> dict:
    runner = BashRunner(station_dir)
    start_text = runner.start()

    messages = [
        {"role": "system", "content": BASH_SYSTEM_PROMPT},
        {"role": "user", "content": f"Game started. You are in the airlock.\n\n{start_text}"},
    ]

    total_prompt_tokens = 0
    total_completion_tokens = 0
    turns = 0
    commands = []
    won = False
    gave_up = False

    log.log(f"=== Eval: {model} [bash] ===")
    log.log(f"Token limit: {token_limit}")
    log.log()

    while True:
        total_tokens = total_prompt_tokens + total_completion_tokens
        if total_tokens >= token_limit:
            log.log(f"[TOKEN LIMIT HIT: {total_tokens}]")
            break

        try:
            response = litellm.completion(
                model=model,
                messages=messages,
                temperature=0,
                max_tokens=50,
            )
        except Exception as e:
            log.log(f"[API ERROR: {e}]")
            break

        choice = response.choices[0]
        reply = choice.message.content.strip()
        usage = response.usage
        total_prompt_tokens += usage.prompt_tokens
        total_completion_tokens += usage.completion_tokens
        turns += 1

        turn_tokens = usage.prompt_tokens + usage.completion_tokens
        log.log(f"[Turn {turns}] +{turn_tokens} tokens (total: {total_prompt_tokens + total_completion_tokens})")
        log.log(f"  LLM: {reply}")

        if "GIVE_UP" in reply.upper():
            gave_up = True
            log.log("  [MODEL GAVE UP]")
            break

        # Extract command — first line, strip backticks and markdown
        command = reply.strip().split("\n")[0]
        command = command.strip("`").strip()
        if "<|" in command:
            command = command[:command.index("<|")].strip()

        commands.append(command)
        messages.append({"role": "assistant", "content": reply})

        # Reject empty / garbage commands
        if not command:
            empty_streak = 0
            for c in reversed(commands):
                if c == "":
                    empty_streak += 1
                else:
                    break
            log.log(f"  [EMPTY COMMAND x{empty_streak}]")
            if empty_streak >= 5:
                log.log("  [FORCE STOP: 5 consecutive empty commands]")
                break
            messages.append({"role": "user", "content": "Invalid command. Send exactly one bash command, nothing else."})
            continue

        # Loop detection
        if len(commands) >= 3 and commands[-1] == commands[-2] == commands[-3]:
            log.log(f"  [LOOP DETECTED: '{command}' repeated 3 times]")
            messages.append({"role": "user", "content": f"You have run '{command}' 3 times in a row with the same result. Try a different command."})

        output = runner.run_command(command)
        log.log(f"  OUT: {output[:200]}")

        if runner.check_win():
            won = True
            messages.append({"role": "user", "content": output})
            log.log("\n  *** WIN ***")
            break

        if output:
            messages.append({"role": "user", "content": output})
        else:
            messages.append({"role": "user", "content": "(no output)"})

    return _finish(log, model=model, mode="bash", won=won, gave_up=gave_up,
                   prompt_tokens=total_prompt_tokens, completion_tokens=total_completion_tokens,
                   turns=turns, commands=commands)


def run_mcp_eval(model: str, token_limit: int, log: Logger) -> dict:
    runner = McpRunner()
    start_text = runner.start()

    messages = [
        {"role": "system", "content": MCP_SYSTEM_PROMPT},
        {"role": "user", "content": f"Game started. You are in the airlock.\n\n{start_text}"},
    ]

    total_prompt_tokens = 0
    total_completion_tokens = 0
    turns = 0
    tool_calls_log = []
    won = False
    gave_up = False
    empty_streak = 0

    log.log(f"=== Eval: {model} [mcp] ===")
    log.log(f"Token limit: {token_limit}")
    log.log()

    while True:
        total_tokens = total_prompt_tokens + total_completion_tokens
        if total_tokens >= token_limit:
            log.log(f"[TOKEN LIMIT HIT: {total_tokens}]")
            break

        try:
            response = litellm.completion(
                model=model,
                messages=messages,
                tools=TOOL_SCHEMAS,
                temperature=0,
                max_tokens=200,
            )
        except Exception as e:
            log.log(f"[API ERROR: {e}]")
            break

        choice = response.choices[0]
        usage = response.usage
        total_prompt_tokens += usage.prompt_tokens
        total_completion_tokens += usage.completion_tokens
        turns += 1

        turn_tokens = usage.prompt_tokens + usage.completion_tokens
        log.log(f"[Turn {turns}] +{turn_tokens} tokens (total: {total_prompt_tokens + total_completion_tokens})")

        if choice.message.tool_calls:
            empty_streak = 0
            messages.append(choice.message.model_dump())

            for tc in choice.message.tool_calls:
                tool_name = tc.function.name
                try:
                    arguments = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}

                tool_calls_log.append({"tool": tool_name, "args": arguments})
                result = runner.execute_tool(tool_name, arguments)

                log.log(f"  TOOL: {tool_name}({arguments})")
                log.log(f"  OUT:  {result[:200]}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })

                if runner.check_win():
                    won = True
                    log.log("\n  *** WIN ***")
                    break

            if won:
                break

        elif choice.message.content:
            content = choice.message.content.strip()
            log.log(f"  LLM: {content}")
            messages.append({"role": "assistant", "content": content})

            if "GIVE_UP" in content.upper():
                gave_up = True
                log.log("  [MODEL GAVE UP]")
                break

            empty_streak = 0
            messages.append({"role": "user", "content": "Use the available tools to interact with the game."})

        else:
            empty_streak += 1
            log.log(f"  [EMPTY RESPONSE x{empty_streak}]")
            messages.append({"role": "assistant", "content": ""})
            if empty_streak >= 5:
                log.log("  [FORCE STOP: 5 consecutive empty responses]")
                break
            messages.append({"role": "user", "content": "Use the available tools to interact with the game."})

    return _finish(log, model=model, mode="mcp", won=won, gave_up=gave_up,
                   prompt_tokens=total_prompt_tokens, completion_tokens=total_completion_tokens,
                   turns=turns, commands=tool_calls_log)


def _finish(log: Logger, *, model, mode, won, gave_up, prompt_tokens, completion_tokens, turns, commands) -> dict:
    total_tokens = prompt_tokens + completion_tokens

    log.log()
    log.log("=== Results ===")
    log.log(f"  Model:       {model}")
    log.log(f"  Mode:        {mode}")
    log.log(f"  Won:         {won}")
    log.log(f"  Gave up:     {gave_up}")
    log.log(f"  Total tokens: {total_tokens}")
    log.log(f"  Turns:       {turns}")
    log.log(f"  Log:         {log.path}")

    return {
        "model": model,
        "mode": mode,
        "won": won,
        "gave_up": gave_up,
        "total_tokens": total_tokens,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "turns": turns,
        "commands": commands,
        "timestamp": datetime.now().isoformat(),
    }


def _print_comparison(results: list[dict]):
    by_label = {}
    for r in results:
        label = r.get("label", r["model"])
        by_label.setdefault(label, {})[r["mode"]] = r

    def fmt(r):
        if r is None:
            return "  -    -        -  "
        won = "YES" if r["won"] else ("QUIT" if r["gave_up"] else "NO")
        return f"{won:<5} {r['total_tokens']:<8} {r['turns']:<5}"

    print(f"\n{'='*72}")
    print("  COMPARISON: bash vs mcp")
    print(f"{'='*72}")
    print(f"  {'Model':<24}   {'--- bash ---':^18}   {'--- mcp ---':^18}")
    print(f"  {'':24}   {'Won':<5} {'Tokens':<8} {'Turns':<5}   {'Won':<5} {'Tokens':<8} {'Turns':<5}")
    print(f"  {'-'*22}   {'-'*18}   {'-'*18}")
    for label, modes in by_label.items():
        print(f"  {label:<24}   {fmt(modes.get('bash'))}   {fmt(modes.get('mcp'))}")


def load_models(models_file: str) -> list[dict]:
    with open(models_file) as f:
        data = yaml.safe_load(f)
    return data.get("models", [])


def main():
    parser = argparse.ArgumentParser(description="Run LLM eval: bash + MCP, side by side")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--model", help="Single model name (e.g. openrouter/openai/gpt-oss-120b)")
    group.add_argument("--all", action="store_true", help="Run all models from models.yaml")
    parser.add_argument("--models-file", default=None, help="Path to models.yaml")
    parser.add_argument("--station-dir", default=None, help="Path to station/ directory")
    parser.add_argument("--token-limit", type=int, default=50000, help="Max total tokens before stopping")
    parser.add_argument("--log-dir", default=None, help="Directory for log files")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(script_dir, "..")

    if args.station_dir is None:
        args.station_dir = os.path.join(project_root, "bash_adventure", "station")
    args.station_dir = os.path.abspath(args.station_dir)

    if args.log_dir is None:
        args.log_dir = os.path.join(project_root, "eval", "logs")

    if args.models_file is None:
        args.models_file = os.path.join(project_root, "models.yaml")

    if not os.path.isdir(args.station_dir):
        print(f"ERROR: Station directory not found: {args.station_dir}")
        sys.exit(1)

    reset_script = os.path.join(args.station_dir, "..", "reset.sh")

    def run_both(model_name: str, label: str) -> list[dict]:
        # bash
        if os.path.exists(reset_script):
            os.system(f"bash {reset_script}")
        blog = Logger(args.log_dir, label, "bash")
        bash_result = run_bash_eval(model_name, args.station_dir, args.token_limit, blog)
        blog.close()

        # mcp
        mlog = Logger(args.log_dir, label, "mcp")
        mcp_result = run_mcp_eval(model_name, args.token_limit, mlog)
        mlog.close()

        return [bash_result, mcp_result]

    if args.all:
        models = load_models(args.models_file)
        if not models:
            print(f"ERROR: No models found in {args.models_file}")
            sys.exit(1)

        results = []
        for entry in models:
            model_name = entry["name"]
            label = entry.get("label", model_name)
            print(f"\n{'='*60}")
            print(f"  Running: {label} ({model_name})")
            print(f"{'='*60}\n")

            for r in run_both(model_name, label):
                r["label"] = label
                results.append(r)

        _print_comparison(results)
    else:
        results = run_both(args.model, args.model)
        _print_comparison(results)


if __name__ == "__main__":
    main()
