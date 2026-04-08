def assign_agent(agents):
    available = [a for a in agents if a["available"]]
    if not available:
        return None
    return min(available, key=lambda x: x["distance"])