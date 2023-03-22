import collections
import types
import tiktoken
import openai
import openai.error

from . import utils, errors

Message = collections.namedtuple("Message", ["role", "content"])
CostConfig = collections.namedtuple("CostConfig", "name prompt_cost completion_cost")
CostCalculation = collections.namedtuple("CostCalculation", "name tokens cost")

costs = [CostConfig("gpt-3.5", 0.002, 0.002), CostConfig("gpt-4", 0.03, 0.06)]


def get_tokens_and_costs(messages):
    return [
        CostCalculation(
            cost_config.name, *num_tokens_in_messages(messages, cost_config)
        )
        for cost_config in costs
    ]


def num_tokens_in_messages(messages, cost_config):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(cost_config.name)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = 0
    cost = 0
    for i, message in enumerate(messages):
        msg_tokens = (
            4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
        )
        msg_tokens += len(encoding.encode(message.role))
        msg_tokens += len(encoding.encode(message.content))
        if i == len(messages) - 1 and message.role == "assistant":
            cost += cost_config.completion_cost * msg_tokens
        else:
            cost += cost_config.prompt_cost * msg_tokens
        num_tokens += msg_tokens
    if messages[-1].role == "user":
        num_tokens += 2  # every reply is primed with <im_start>assistant
        cost += cost_config.prompt_cost * 2
    return num_tokens, cost / 1000


def init_conversation(user_msg, system_msg=None):
    system = [Message("system", system_msg)] if system_msg else []
    return system + [Message("user", user_msg)]


DEFAULT_OPENAI_SETTINGS = {
    "model": "gpt-3.5-turbo",
    "temperature": 0.1,
    "n": 1,
    "stream": False,
}


def map_generator(openai_gen):
    """maps a openai streaming generator a stream of Message with the
    final one being the completed Message"""
    role, message = None, ""
    for update in openai_gen:
        delta = [choice["delta"] for choice in update["choices"]][0]
        if "role" in delta:
            role = delta["role"]
        elif "content" in delta:
            message += delta["content"]
        yield Message(role, message)


def map_single(result):
    """maps a result to a Message"""
    response_message = [choice["message"] for choice in result["choices"]][0]
    return Message(response_message["role"], response_message["content"])


def query_chat_gpt(messages, config):
    """Queries the chat GPT API with the given messages and config."""
    openai.api_key = config["openai_api_key"]
    config = utils.merge_dicts(DEFAULT_OPENAI_SETTINGS, config)
    dict_messages = [msg._asdict() for msg in messages]
    try:
        result = openai.ChatCompletion.create(messages=dict_messages, **config)
        if isinstance(result, types.GeneratorType):
            return map_generator(result)
        elif isinstance(result, dict):
            return map_single(result)
        else:
            raise ValueError(f"unexpected result openai: {result}")
    except (
        openai.error.InvalidRequestError,
        openai.error.AuthenticationError,
        openai.error.RateLimitError,
    ) as e:
        raise errors.ChatbladeError(f"openai error: {e}")
