"""
Json Helpers
"""
def prune(data, keys):
    """
    Entfernt sämtliche Vorkommen der Keys aus einem verschachtelten dict/list.
    """
    if isinstance(data, dict):
        return {k: prune(v, keys) for k, v in data.items() if k not in keys}
    if isinstance(data, list):
        return [prune(item, keys) for item in data]
    return data
