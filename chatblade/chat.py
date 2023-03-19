import collections
import tiktoken
import openai

from . import utils

Message = collections.namedtuple("Message", ["role", "content"])


def num_tokens_in_messages(messages, model="gpt-3.5-turbo-0301"):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = 0
    for message in messages:
        num_tokens += (
            4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
        )
        num_tokens += len(encoding.encode(message.role))
        num_tokens += len(encoding.encode(message.content))
    num_tokens += 2  # every reply is primed with <im_start>assistant
    return num_tokens


def init_conversation(user_msg, system_msg=None):
    system = [Message("system", system_msg)] if system_msg else []
    return system + [Message("user", user_msg)]


DEFAULT_OPENAI_SETTINGS = {
    "model": "gpt-3.5-turbo",
    "temperature": 0.1,
    "n": 1,
}


def query_chat_gpt(messages, config):
    """Queries the chat GPT API with the given messages and config."""
    openai.api_key = config["openai_api_key"]
    config = utils.merge_dicts(DEFAULT_OPENAI_SETTINGS, config)
    dict_messages = [msg._asdict() for msg in messages]
    result = openai.ChatCompletion.create(messages=dict_messages, **config)
    if not isinstance(result, dict):
        raise ValueError(
            "OpenAI Result is not a dict got %s: %s" % (type(result), result)
        )
    response_message = [choice["message"] for choice in result["choices"]][0]
    message = Message(response_message["role"], response_message["content"])
    return message, result
