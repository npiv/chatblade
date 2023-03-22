import sys
import os
import argparse

from . import utils


def get_piped_input():
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return None


def get_openai_key(options):
    if options["openai_api_key"]:
        return options["openai_api_key"]
    elif "OPENAI_API_KEY" in os.environ:
        return os.environ["OPENAI_API_KEY"]
    else:
        return None


def extract_query(query):
    """The query comes from both the query and any piped input
    The user can provide either only a query, a piped input, or both
    in which case the piped input gets placed above the query
    """
    query = " ".join(query) if query else None
    piped_input = get_piped_input()
    if query and piped_input:
        return piped_input + "\n----------------\n" + query
    elif query:
        return query
    elif piped_input:
        return piped_input
    else:
        return None


def extract_options(options):
    options = vars(options)  # to map
    options["openai_api_key"] = get_openai_key(options)
    options["model"] = {"3.5": "gpt-3.5-turbo", "4": "gpt-4"}[options["chat_gpt"]]
    del options["query"]
    del options["chat_gpt"]
    return utils.DotDict(options)


def parse(args):
    parser = argparse.ArgumentParser(
        "Chatblade", description="a CLI Swiss Army Knife for ChatGPT"
    )
    parser.add_argument("query", type=str, nargs="*", help="Query to send to chat GPT")
    parser.add_argument(
        "-l",
        "--last",
        action="store_true",
        help="""display the last result. 
        If a query is given the conversation is continued""",
    )
    parser.add_argument(
        "-p",
        "--prompt-config",
        metavar="PROMPT",
        type=str,
        help="prompt config name, or file containing a prompt config",
    )
    parser.add_argument(
        "--openai-api-key",
        metavar="KEY",
        type=str,
        help="the OpenAI API key can also be set as env variable OPENAI_API_KEY",
    )
    parser.add_argument(
        "--temperature",
        metavar="T",
        type=float,
        help="temperature (openai setting)",
        default=0.0,
    )
    parser.add_argument(
        "-c", "--chat-gpt", choices=["3.5", "4"], help="chat GPT model", default="3.5"
    )

    parser.add_argument(
        "-i",
        "--interactive",
        help="start an interactive chat session. This will implicitly continue the conversation",
        action="store_true",
    )
    parser.add_argument(
        "-s",
        "--stream",
        help="Stream the incoming text to the terminal",
        action="store_true",
    )

    # ------ Display Options
    parser.add_argument(
        "-e",
        "--extract",
        help="extract content from response if possible (either json or code block)",
        action="store_true",
    )
    parser.add_argument(
        "-r",
        "--raw",
        help="print the last response as pure text, don't pretty print or format",
        action="store_true",
    )
    parser.add_argument(
        "-t",
        "--tokens",
        help="display what *would* be sent, how many tokens, and estimated costs",
        action="store_true",
    )

    # --- debug
    parser.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)

    options = parser.parse_args(args)
    return extract_query(options.query), extract_options(options)
