import json
import re
from rich.console import Console
from rich.panel import Panel
from rich.json import JSON
from rich.markdown import Markdown
from rich.table import Table


console = Console()

DEFAULT_ARGS = {
    "roles": ["user", "assistant"],
}


def print_tokens(messages, token_count, args):
    args = {**DEFAULT_ARGS, **args}
    args["roles"] = ["user", "assistant", "system"]
    print_messages(messages, args)
    table = Table()
    table.add_column("Measure", no_wrap=True)
    table.add_column("Value", style="bold", justify="right")
    table.add_row("Tokens", f"{token_count}")
    table.add_row("GPT 3.5", f"${0.002 * token_count / 1000}")
    table.add_row("GPT 4", f"~ ${0.045 * token_count / 1000}")
    console.print(table)


def print_messages(messages, args):
    args = {**DEFAULT_ARGS, **args}
    if args["raw"]:
        print(messages[-1].content)
    elif args["extract"]:
        extract_messages(messages, args)
    else:
        for message in messages:
            if message.role in args["roles"]:
                print_message(message, args)


COLORS = {"user": "blue", "assistant": "green", "system": "red"}


def print_message(message, args):
    printable = detect_and_format_message(
        message.content, cutoff=1000 if message.role == "user" else None
    )
    printable = Panel(printable, title=message.role, border_style=COLORS[message.role])
    console.print(printable)


def extract_messages(messages, args):
    message = messages[-1]
    if contains_json(message.content):
        print(extract_json(message.content))
    elif contains_block(message.content):
        print(extract_block(message.content))
    else:
        print(message.content)


def detect_and_format_message(msg, cutoff=None):
    if contains_json(msg):
        return JSON(extract_json(msg))
    else:
        if cutoff and len(msg) > cutoff:
            msg = "... **text shortened** ... " + msg[-cutoff:]
        return Markdown(msg)


def extract_json_lists(str_lists, flatten=False):
    lists = [json.loads(extract_json(x)) for x in str_lists if contains_json(x)]
    if flatten:
        return json.dumps([item for sublist in lists for item in sublist])
    else:
        return json.dumps(lists)


def contains_block(str):
    if extract_block(str):
        return True
    return False


def extract_block(str):
    matches = re.findall(r"```(.*?)```", str, re.DOTALL)
    try:
        return sorted(matches, key=lambda x: len(x))[-1].strip()
    except IndexError:
        return None
    except Exception as e:
        print(e)
        return None


def contains_json(str):
    try:
        extract_json(str)
    except ValueError:
        return False
    return True


def extract_json(str):
    """
    try to extract json from a string that may contain other lines before the json
    returns the json as a string or raises a ValueError if no json is found
    """
    lines_with_idxs = enumerate(str.splitlines())
    for idx, line in lines_with_idxs:
        if line.strip().startswith("{") or line.strip().startswith("["):
            return json.dumps(json.loads(" ".join(str.splitlines()[idx:])))

    raise ValueError("No json in string")
