import sys
import types
import os

import rich
from rich.prompt import Prompt
from rich.live import Live
from rich.text import Text

from . import printer, chat, utils, storage, errors, parser, session


def fetch_and_cache(messages, params):
    result = chat.query_chat_gpt(messages, params)
    if isinstance(result, types.GeneratorType):
        text = Text("")
        message = None
        with Live(text, refresh_per_second=4, vertical_overflow="visible") as live:
            for message in result:
                live.update(message.content)
            live.update("")
        response_msg = message
    else:
        response_msg = chat.query_chat_gpt(messages, params)
    messages.append(response_msg)
    storage.to_cache(messages, params.session or utils.scratch_session)
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
            init_msgs = (
                [storage.load_prompt_file(params.prompt_file)]
                if params.prompt_file
                else []
            )
            messages = chat.init_conversation(query, *init_msgs)
        else:
            messages.append(chat.Message("user", query))

        messages = fetch_and_cache(messages, params)
        printer.print_messages(messages[-1:], params)


def handle_input(query, params):
    utils.debug(title="cli input", query=query, params=params)

    messages = None
    if params.session:
        messages = storage.messages_from_cache(params.session)
    if messages:  # a session specified and it alredy exists
        if params.prompt_file:
            printer.warn("refusing to prepend prompt to existing session")
            exit(1)
        if query:  # continue conversation
            messages.append(chat.Message("user", query))
    else:
        if query:
            init_msgs = (
                [storage.load_prompt_file(params.prompt_file)]
                if params.prompt_file
                else []
            )
            messages = chat.init_conversation(query, *init_msgs)

    if messages:
        if params.tokens:
            token_prices = chat.get_tokens_and_costs(messages)
            printer.print_tokens(messages, token_prices, params)
        else:
            if messages[-1].role == "user":
                messages = fetch_and_cache(messages, params)
            printer.print_messages(messages, params)
    elif params.interactive:
        pass
    else:
        if params.session:
            printer.warn(
                f"session {params.session} does not exist, query is needed to initialize it"
            )
            exit(1)
        else:
            printer.warn("no query or option given. nothing to do...")
            exit(0)

    if params.interactive:
        start_repl(messages, params)


def do_session_op(sess, op, rename_to):
    if op == "list":
        print(*session.list_sessions(), sep="\n")
        return 0

    err = None
    if not sess:
        err = "session name required"
    elif op == "path" or op == "dump":
        sess_path = storage.get_session_path(sess, True)
        if sess_path:
            if op == "path":
                data = sess_path
            else:
                with open(sess_path, "r") as f:
                    data = f.read()
            print(data)
        else:
            err = "session does not exist"
    elif op == "delete":
        err = session.delete_session(sess)
    elif op == "rename":
        err = session.rename_session(sess, rename_to)
    else:
        raise ValueError(f"unknown session operation: {op}")

    if err:
        printer.warn(err)
        return 1

    return 0


def migrate_old_cache_file_if_exists():
    cache_path = storage.get_cache_path()
    if os.path.isfile(cache_path):
        try:
            storage.migrate_to_session(utils.scratch_session)
        except Exception as e:
            printer.warn(f"failed to migrate old cache file: {e}")
            return 1


def cli():
    migrate_old_cache_file_if_exists()

    query, params = parser.parse(sys.argv[1:])
    if params.session_op:
        ret = do_session_op(params.session, params.session_op, params.rename_to)
        exit(ret)
    if params.debug:
        utils.CONSOLE_DEBUG_LOGGING = True
    try:
        handle_input(query, params)
    except errors.ChatbladeError as e:
        printer.warn(e)
        exit(1)
