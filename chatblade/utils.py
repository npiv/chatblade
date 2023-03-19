def merge_dicts(dict1, dict2):
    """merge 2 dicts with priority from dict2, but only for keys known by dict1"""
    merged = {**dict1, **dict2}
    merged = {k: v for k, v in merged.items() if v is not None and k in dict1}
    return merged
