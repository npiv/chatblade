import sys
import types

import rich
from rich.prompt import Prompt
from rich.live import Live
from rich.text import Text

from . import printer, chat, utils, storage, errors, parser


def fetch_and_cache(messages, params):
    result = chat.query_chat_gpt(messages, params)
    if isinstance(result, types.GeneratorType):
        text = Text("")
        message = None
        with Live(text, refresh_per_second=4) as live:
            for message in result:
                live.update(message.content)
            live.update("")
        response_msg = message
    else:
        response_msg = chat.query_chat_gpt(messages, params)
    messages.append(response_msg)
    storage.to_cache(messages)
    return messages


def start_repl(messages, params):
    while True:
        try:
            query = Prompt.ask("[yellow]query (type 'quit' to exit): [/yellow]")
        except (EOFError, KeyboardInterrupt):
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
    utils.debug(title="cli input", query=query, params=params)

    if params.last:
        messages = storage.messages_from_cache()
        if query:  # continue conversation
            messages.append(chat.Message("user", query))
    elif params.prompt_config:
        prompt_config = storage.load_prompt_config(params.prompt_config)
        messages = chat.init_conversation(query, prompt_config["system"])
        params = utils.merge_dicts(params, prompt_config)
    elif query:
        messages = chat.init_conversation(query)
    elif params.interactive:
        start_repl(None, params)
    else:
        printer.warn("no query or option given. nothing to do...")
        exit()

    if params.tokens:
        token_prices = chat.get_tokens_and_costs(messages)
        printer.print_tokens(messages, token_prices, params)
    else:
        if messages[-1].role == "user":
            messages = fetch_and_cache(messages, params)
        printer.print_messages(messages, params)

    if params.interactive:
        start_repl(messages, params)


def cli():
    query, params = parser.parse(sys.argv[1:])
    if params.debug:
        utils.CONSOLE_DEBUG_LOGGING = True
    try:
        handle_input(query, params)
    except errors.ChatbladeError as e:
        printer.warn(e)
