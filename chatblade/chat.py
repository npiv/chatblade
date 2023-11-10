import collections
import os
import yaml

import tiktoken
import openai
from openai._exceptions import OpenAIError

from . import utils, errors


class Message(collections.namedtuple("Message", ["role", "content"])):
    @staticmethod
    def represent_for_yaml(dumper, msg):
        val = []
        md = msg._asdict()

        for fie in msg._fields:
            val.append([dumper.represent_data(e) for e in (fie, md[fie])])

        return yaml.nodes.MappingNode("tag:yaml.org,2002:map", val)

    @classmethod
    def import_yaml(cls, seq):
        """instantiate from YAML provided representation"""
        return cls(**seq)


yaml.add_representer(Message, Message.represent_for_yaml)


CostConfig = collections.namedtuple("CostConfig", "name prompt_cost completion_cost")
CostCalculation = collections.namedtuple("CostCalculation", "name tokens cost")

costs = [
    CostConfig("gpt-3.5-turbo", 0.001, 0.002),
    CostConfig("gpt-4", 0.03, 0.06),
    CostConfig("gpt-4-1106-preview", 0.01, 0.03),
]


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
        encoding = tiktoken.encoding_for_model(f"{cost_config.name}-0301")
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


def map_from_stream(openai_gen):
    """maps a openai streaming generator a stream of Message with the
    final one being the completed Message"""
    role, message = None, ""
    for update in openai_gen:
        delta = [choice.delta for choice in update.choices][0]
        if delta.role:
            role = delta.role
        elif delta.content:
            message += delta.content
        yield Message(role, message)


def map_single(result):
    """maps a result to a Message"""
    response_message = [choice.message for choice in result.choices][0]
    return Message(response_message.role, response_message.content)


def build_client(config):
    if "OPENAI_API_AZURE_ENGINE" in os.environ:
        return openai.AzureOpenAI(api_key=config["openai_api_key"])
    else:
        return openai.OpenAI(api_key=config["openai_api_key"])


def query_chat_gpt(messages, config):
    """Queries the chat GPT API with the given messages and config."""
    client = build_client(config)
    config = utils.merge_dicts(DEFAULT_OPENAI_SETTINGS, config)
    dict_messages = [msg._asdict() for msg in messages]
    try:
        result = client.chat.completions.create(messages=dict_messages, **config)
        if isinstance(result, openai._streaming.Stream):
            return map_from_stream(result)
        elif isinstance(result, openai.types.chat.ChatCompletion):
            return map_single(result)
        else:
            raise ValueError(f"unexpected result openai: {result}")
    except OpenAIError as e:
        raise errors.ChatbladeError(f"openai error: {e}")
