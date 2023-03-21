"""
Handles storage of cache and prompt config directories, as well
as figuring out where to put them on various platforms 
"""

import os
import platformdirs
import pickle
import yaml

from . import errors

APP_NAME = "chatblade"


def get_cache_file_path():
    """
    if ~/.cache is availabe always use ~/.cache/chatblade as the cachefile
    otherwise fallback to the platform recommended location and create the directory
    e.g. ~/Library/Caches/chatblade on osx
    """
    cache_path = os.path.expanduser("~/.cache")
    if not os.path.exists(cache_path):
        cache_path = platformdirs.user_cache_dir(APP_NAME)
        if not os.path.exists(cache_path):
            os.makedirs(cache_path)

    return os.path.join(cache_path, APP_NAME)


def to_cache(messages):
    """cache the current messages state"""
    with open(get_cache_file_path(), "wb") as f:
        pickle.dump(messages, f)


def messages_from_cache():
    """load messages from last state or ChatbladeError if not exists"""
    file_path = get_cache_file_path()
    if not os.path.exists(file_path):
        raise errors.ChatbladeError("No last state cached from which to begin")
    else:
        with open(file_path, "rb") as f:
            return pickle.load(f)


def load_prompt_config(prompt_name):
    """
    load a prompt configuration by its name
    Assumes the user created the {name}.yaml in ~/.config/chatblade
    """
    path = os.path.expanduser(
        os.path.join("~/.config/chatblade", f"{prompt_name}.yaml")
    )
    try:
        with open(path, "r") as f:
            return yaml.load(f, Loader=yaml.FullLoader)
    except FileNotFoundError:
        raise errors.ChatbladeError(f"Prompt {prompt_name} not found in {path}")
