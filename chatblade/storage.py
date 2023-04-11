"""
Handles storage of cache and prompt config directories, as well
as figuring out where to put them on various platforms 
"""

import os
import platformdirs
import pickle
import yaml
import random
import string

from . import errors, chat

APP_NAME = "chatblade"


def make_postfix():
    return "." + "".join(random.choices(string.ascii_letters + string.digits, k=10))


def get_cache_path(create=True):
    """
    if ~/.cache is availabe always use ~/.cache/chatblade as the cachefile
    otherwise fallback to the platform recommended location and create the directory
    e.g. ~/Library/Caches/chatblade on osx
    """
    os_cache_path = os.path.expanduser("~/.cache")
    if not os.path.exists(os_cache_path):
        os_cache_path = platformdirs.user_cache_dir(APP_NAME)
        if not os.path.exists(os_cache_path):
            os.makedirs(os_cache_path)

    cache_path = os.path.join(os_cache_path, APP_NAME)
    if create and not os.path.exists(cache_path):
        os.makedirs(cache_path)

    return cache_path


def get_session_path(session, exists=False):
    """get the path of a session file
    If exists=True, return None if the path does not exists"""
    session_path = os.path.join(get_cache_path(), f"{session}.yaml")
    if exists and not os.path.exists(session_path):
        return
    return session_path


def to_cache(messages, session):
    """cache the current messages state"""
    file_path = get_session_path(session)
    file_path_tmp = file_path + make_postfix()
    with open(file_path_tmp, "w") as f:
        yaml.dump(messages, f)
    os.replace(file_path_tmp, file_path)


def messages_from_cache(session):
    """load messages from session
    Return empty list if not exists"""
    file_path = get_session_path(session)
    if not os.path.exists(file_path):
        return []
    else:
        with open(file_path, "r") as f:
            return [chat.Message.import_yaml(m) for m in yaml.load(f, yaml.SafeLoader)]


def messages_from_cache_legacy():
    """load messages from last state or ChatbladeError if not exists"""
    file_path = get_cache_path(False)
    if not os.path.exists(file_path):
        raise errors.ChatbladeError("No last state cached from which to begin")
    else:
        with open(file_path, "rb") as f:
            return pickle.load(f)


def migrate_to_session(session):
    """save pre-session last messages to session"""
    file_path = get_cache_path(False)
    messages = messages_from_cache_legacy()
    file_path_tmp = file_path + make_postfix()
    # resolve name conflict, but keep old cache file
    # until all has gone through fine
    os.replace(file_path, file_path_tmp)
    to_cache(messages, session)
    os.unlink(file_path_tmp)


def load_prompt_file(prompt_name):
    """
    load a prompt configuration by its name
    Assumes the user created the ~/.config/chatblade/{prompt_name}
    or a file directly by path
    """
    paths_to_try = [
        prompt_name,
        os.path.expanduser(os.path.join("~/.config/chatblade", f"{prompt_name}")),
    ]
    try:
        for file_path in paths_to_try:
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    return f.read()
        # fallback legacy
        load_prompt_config_legacy_yaml(prompt_name)
    except Exception:
        locations = "".join(["\n - " + p for p in paths_to_try])
        raise errors.ChatbladeError(
            f"no prompt {prompt_name} found in any of following locations: {locations}"
        )


def load_prompt_config_legacy_yaml(prompt_name):
    """
    LEGACY: keep right now for people that still use yaml
    load a prompt configuration by its name
    Assumes the user created the {name}.yaml in ~/.config/chatblade
    """
    path = os.path.expanduser(
        os.path.join("~/.config/chatblade", f"{prompt_name}.yaml")
    )
    try:
        with open(path, "r") as f:
            return yaml.load(f, Loader=yaml.FullLoader)["system"]
    except FileNotFoundError:
        raise errors.ChatbladeError(f"Prompt {prompt_name} not found in {path}")
