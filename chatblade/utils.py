import time
from itertools import cycle
from rich.progress import Progress
from rich.pretty import pprint

CONSOLE_DEBUG_LOGGING = False


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


def breathing(stopper):
    breathing_phases = [
	["[blue]Inhale...", 400],
	["[green]Hold.....", 700],
	["[blue]Exhale...", 800],
    ]

    for i in cycle(breathing_phases):
        p = Progress(transient=True)
        p.columns[2].text_format = ""

        with p as progress:
            task = progress.add_task(i[0], total=i[1])
            while not progress.finished:
                if stopper.is_set():
                    break
                progress.update(task, advance=10)
                time.sleep(0.1)
            if stopper.is_set():
                break

