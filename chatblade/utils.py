from rich.pretty import pprint

CONSOLE_DEBUG_LOGGING = False

scratch_session = "last"


class DotDict(dict):
    """dot.notation access to dictionary attributes"""

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def merge_dicts(dict1, dict2):
    """merge 2 dicts with priority from dict2, but only for keys known by dict1"""
    merged = {**dict1, **dict2}
    merged = {k: v for k, v in merged.items() if v is not None and k in dict1}
    return DotDict(merged)


def debug(title=None, **kwargs):
    if CONSOLE_DEBUG_LOGGING:
        if title:
            pprint({f"{title}": kwargs})
        else:
            pprint(kwargs)
