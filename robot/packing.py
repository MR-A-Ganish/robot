def pack_items(items):
    # Sort: non-fragile first, heavy first
    return sorted(items, key=lambda x: (x["fragile"], -x["weight"]))