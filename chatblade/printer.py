import json
import re
import sys
import rich
from rich.console import Console
from rich.json import JSON
from rich.markdown import Markdown
from rich.table import Table
from rich.rule import Rule

from chatblade import utils


console = Console()


def warn(msg):
    rich.print(f"[red]{msg}[/red]", file=sys.stderr)


def print_tokens(messages, token_stats, args):
    if args.only:
      args.roles = ["assistant"]
    else:
      args.roles = ["user", "assistant", "system"]
    print_messages(messages, args)
    console.print()
    table = Table(title="tokens/costs")
    table.add_column("Model", no_wrap=True)
    table.add_column("Tokens", no_wrap=True)
    table.add_column("Price", style="bold", justify="right")
    for token_stat in token_stats:
        table.add_row(
            token_stat.name,
            "{:d}".format(token_stat.tokens),
            "${:.6f}".format(token_stat.cost),
        )
    console.print(table)
    console.print(
        "[red] * estimated costs do not include the tokens that may be returned[/red]"
    )


def print_messages(messages, args):
    if "roles" not in args:
      if args.only:
        args.roles = ["assistant"]
      else:
        args.roles = ["user", "assistant"]
    if args.extract:
        extract_messages(messages, args)
    else:
        for message in messages:
            if message.role in args.roles:
                print_message(message, args)


COLORS = {"user": "blue", "assistant": "green", "system": "red"}


def print_message(message, args):
    printable = message.content
    if not args.raw:
        printable = detect_and_format_message(
            message.content, cutoff=1000 if message.role == "user" else None, theme=args.theme
        )
    if not args.no_format:
      console.print(Rule(message.role, style=COLORS[message.role]))

    if args.raw:
        print(message.content)
    else:
        console.print(printable)

    if not args.no_format:
      console.print(Rule(style=COLORS[message.role]))


def extract_messages(messages, args):
    message = messages[-1]
    if contains_json(message.content):
        print(extract_json(message.content))
    elif contains_block(message.content):
        print(extract_block(message.content))
    else:
        print(message.content.strip())


def detect_and_format_message(msg, cutoff=None, theme=None):
    if cutoff and len(msg) > cutoff:
        msg = "... **text shortened** ... " + msg[-cutoff:]
        return msg
    elif contains_json(msg):
        utils.debug(detected="json")
        return JSON(extract_json(msg))
    elif looks_like_markdown(msg):
        utils.debug(detected="markdown")
        theme = "monokai" if theme is None else theme
        return Markdown(msg,code_theme=theme)
    else:
        utils.debug(detected="regular")
        return msg


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
    matches = re.findall(r"```[\w]*(.*?)```", str, re.DOTALL)
    try:
        return sorted(matches, key=lambda x: len(x))[-1].strip()
    except IndexError:
        return None


def looks_like_markdown(str):
    """very rudimentary, but avoids making things markdown that shouldn't be"""
    md_links = len(re.findall(r"\[[^]]+\]\(https?:\/\/\S+\)", str))
    md_text = len(re.findall(r"\s(__|\*\*)(?!\s)(.(?!\1))+(?!\s(?=\1))", str))
    md_blocks = len(re.findall(r"```(.*?)```", str, re.DOTALL))
    md_inline_blocks = len(re.findall(r"`[^`]+`", str)) - md_blocks

    md_blocks *= 2
    utils.debug(
        title="counted",
        md_links=md_links,
        md_text=md_text,
        md_inline_blocks=md_inline_blocks,
        md_blocks=md_blocks,
    )
    score = md_links + md_text + md_inline_blocks + md_blocks
    return score >= 2


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
