from .packing import pack_items
from .grip_control import get_grip_pressure
from .delivery import assign_agent
from .navigation import astar, create_grid

def process_order(items):

    packed = pack_items(items)

    grip = []
    for item in packed:
        psi = get_grip_pressure(item["weight"], item["fragile"])
        grip.append({"item": item["name"], "psi": psi})

    grid = create_grid(10, 10)
    path = astar(grid, (0, 0), (9, 9))

    agents = [
        {"id": 1, "distance": 2, "available": True},
        {"id": 2, "distance": 1, "available": True}
    ]

    assigned = assign_agent(agents)

    return {
        "packing": packed,
        "grip": grip,
        "path": path,
        "delivery": assigned
    }