import sys
import os
import argparse
import rich

from chatblade import errors

from . import printer, chat, utils, storage
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


def fetch_and_cache(messages, params):
    response_msg, _ = chat.query_chat_gpt(messages, params)
    messages.append(response_msg)
    storage.to_cache(messages)
    return messages


def start_repl(messages, params):
    while True:
        try:
            query = Prompt.ask("[yellow]query (type 'quit' to exit): [/yellow]")
        except KeyboardInterrupt:
            rich.print("\n")
            exit()
        if query.lower() == "quit":
            exit()

        if not messages:
            messages = chat.init_conversation(query)
        else:
            messages.append(chat.Message("user", query))

        messages = fetch_and_cache(messages, params)
        printer.print_messages(messages[-1:], params)


def handle_input(query, params):
    if params["last"] or params["extract"] or params["raw"]:
        messages = storage.messages_from_cache()
        if query:
            messages.append(chat.Message("user", query))
    elif "prompt_config" in params:
        prompt_config = storage.load_prompt_config(params["prompt_config"])
        messages = chat.init_conversation(query, prompt_config["system"])
        params = utils.merge_dicts(params, prompt_config)
    elif query:
        messages = chat.init_conversation(query)
    elif params["interactive"]:
        start_repl(None, params)
    else:
        rich.print("[red]no query or option given. nothing to do...[/red]")
        exit()

    if "tokens" in params and params["tokens"]:
        token_prices = chat.get_tokens_and_costs(messages)
        printer.print_tokens(messages, token_prices, params)
    else:
        if messages[-1].role == "user":
            messages = fetch_and_cache(messages, params)
        printer.print_messages(messages, params)

    if params["interactive"]:
        start_repl(messages, params)


def cli():
    query, params = parse_input()
    try:
        handle_input(query, params)
    except errors.ChatbladeError as e:
        rich.print(f"[red]{e}[/red]")
