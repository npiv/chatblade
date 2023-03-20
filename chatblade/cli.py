import pickle
import sys
import os
import argparse
import rich
import yaml

from . import printer, chat, utils
from rich.prompt import Prompt


def get_piped_input():
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return None


def get_openai_key(params):
    if params.openai_api_key:
        return params.openai_api_key
    elif "OPENAI_API_KEY" in os.environ:
        return os.environ["OPENAI_API_KEY"]
    else:
        return None


def parse_input():
    parser = argparse.ArgumentParser(description="Chatblade")
    parser.add_argument("query", type=str, nargs="*", help="Query to send to chat GPT")
    parser.add_argument(
        "--last",
        "-l",
        action="store_true",
        help="Display the last result. If a query is given the conversation is continued",
    )
    parser.add_argument(
        "--prompt-config",
        "-p",
        type=str,
        help="Prompt config name, or file containing a prompt config",
    )
    parser.add_argument(
        "--openai-api-key",
        type=str,
        help="OpenAI API key can also be set as env variable OPENAI_API_KEY",
    )
    parser.add_argument(
        "--temperature", type=float, help="Temperature (openai setting)"
    )
    parser.add_argument(
        "--chat-gpt", "-c", choices=["3.5", "4"], help="Chat GPT model (default 3.5)"
    )
    parser.add_argument(
        "--extract",
        "-e",
        help="Extract content from response if possible (either json or code block)",
        action="store_true",
    )
    parser.add_argument(
        "--raw",
        "-r",
        help="print the last response as pure text, don't pretty print or format",
        action="store_true",
    )
    parser.add_argument(
        "--tokens",
        "-t",
        help="Display what *would* be sent, how many tokens, and estimated costs",
        action="store_true",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        help="Start an interactive chat session. This will implicitly continue the conversation",
        action="store_true",
    )

    args = parser.parse_args()

    params = vars(args)
    params = {k: v for k, v in params.items() if v is not None}

    openai_api_key = get_openai_key(args)
    if not openai_api_key:
        print("expecting openai API Key")
        exit(parser.print_help())
    else:
        params["openai_api_key"] = openai_api_key

    if "chat_gpt" in params:
        if params["chat_gpt"] == "3.5":
            params["model"] = "gpt-3.5-turbo"
        elif params["chat_gpt"] == "4":
            params["model"] = "gpt-4"
        else:
            raise ValueError(f"Unknown chat GPT version {params['chat_gpt']}")

    query = " ".join(args.query)
    piped_input = get_piped_input()
    if piped_input:
        query = piped_input + "\n----------------\n" + query

    return query, params


MAX_TOKEN_COUNT = 4096
CACHE_PATH = "~/.cache/chatblade"
PROMPT_PATH = "~/.config/chatblade/"


def to_cache(messages):
    path = os.path.expanduser(CACHE_PATH)
    with open(path, "wb") as f:
        pickle.dump(messages, f)


def messages_from_cache():
    path = os.path.expanduser(CACHE_PATH)
    with open(path, "rb") as f:
        return pickle.load(f)


def load_prompt_config(prompt_name):
    path = os.path.expanduser(PROMPT_PATH + prompt_name + ".yaml")
    try:
        with open(path, "r") as f:
            return yaml.load(f, Loader=yaml.FullLoader)
    except FileNotFoundError:
        raise ValueError(f"Prompt {prompt_name} not found in {path}")


def fetch_and_cache(messages, params):
    response_msg, _ = chat.query_chat_gpt(messages, params)
    messages.append(response_msg)
    to_cache(messages)
    return messages


def cli():
    query, params = parse_input()
    while True:
        if params["last"] or params["extract"] or params["raw"]:
            messages = messages_from_cache()
            if query:
                messages.append(chat.Message("user", query))
        elif "prompt_config" in params:
            prompt_config = load_prompt_config(params["prompt_config"])
            messages = chat.init_conversation(query, prompt_config["system"])
            params = utils.merge_dicts(params, prompt_config)
        elif query:
            messages = chat.init_conversation(query)
        else:
            rich.print("[red]no query or option given. nothing to do...[/red]")
            exit()

        if "tokens" in params and params["tokens"]:
            num_tokens = chat.num_tokens_in_messages(messages)
            printer.print_tokens(messages, num_tokens, params)
        else:
            if messages[-1].role == "user":
                messages = fetch_and_cache(messages, params)
            printer.print_messages(messages, params)
        if params["interactive"]:
            params["last"] = True
            query = Prompt.ask("[yellow] Enter your next query")
        else:
            break
