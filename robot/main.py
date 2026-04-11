from database import connect_db


# -------------------------------
# 🤖 ROBOT PROCESS ORDER (UPGRADED)
# -------------------------------
def process_order(items):
    """
    items = [
        {"name": "Milk", "weight": 500, "fragile": False, "qty": 2},
        {"name": "Eggs", "weight": 200, "fragile": True, "qty": 1}
    ]
    """

    conn = connect_db()
    cur = conn.cursor()

    steps = []
    steps.append("🤖 Robot Activated...\n")

    # -----------------------------------
    # 🚀 FETCH ALL PRODUCT LOCATIONS AT ONCE (FAST)
    # -----------------------------------
    names = tuple(item["name"] for item in items)

    cur.execute(
        f"SELECT name, aisle, shelf, position FROM products WHERE name IN %s",
        (names,)
    )

    db_data = cur.fetchall()

    location_map = {
        row[0]: (row[1], row[2], row[3])
        for row in db_data
    }

    # -----------------------------------
    # 🔥 BUILD ITEM LIST WITH LOCATION
    # -----------------------------------
    item_locations = []

    for item in items:
        loc = location_map.get(item["name"])

        if not loc:
            steps.append(f"❌ Item '{item['name']}' not found in warehouse")
            continue

        aisle, shelf, pos = loc

        # 👇 Repeat based on quantity
        for _ in range(item.get("qty", 1)):
            item_locations.append((aisle, shelf, pos, item))

    # -----------------------------------
    # 🧠 SMART SORT (PATH OPTIMIZATION)
    # -----------------------------------
    item_locations.sort(key=lambda x: (x[0], x[1], x[2]))

    # -----------------------------------
    # 🤖 PROCESS MOVEMENT
    # -----------------------------------
    current_aisle = None
    current_shelf = None

    for aisle, shelf, pos, item in item_locations:

        # Move aisle only if needed
        if aisle != current_aisle:
            steps.append(f"\n➡️ Moving to Aisle {aisle}")
            current_aisle = aisle
            current_shelf = None

        # Move shelf only if needed
        if shelf != current_shelf:
            steps.append(f"📦 Navigating to Shelf {shelf}")
            current_shelf = shelf

        steps.append(f"📍 Position {pos}")
        steps.append(f"🛒 Picking: {item['name']}")

        # -----------------------------------
        # 🤏 GRIP LOGIC
        # -----------------------------------
        if item.get("fragile"):
            steps.append("🤏 Using SOFT grip")
        else:
            steps.append("✊ Using NORMAL grip")

        # -----------------------------------
        # ⚖️ WEIGHT LOGIC
        # -----------------------------------
        if item.get("weight", 0) > 800:
            steps.append("⚠️ Heavy item - adjusting grip strength")

        steps.append("✅ Picked")

    # -----------------------------------
    # 📦 PACKING
    # -----------------------------------
    steps.append("\n📦 Moving to packing station")

    fragile_items = [i for i in items if i.get("fragile")]

    if fragile_items:
        steps.append("🧴 Bubble wrapping fragile items")

    steps.append("📦 Packing completed")

    # -----------------------------------
    # 🚚 DELIVERY
    # -----------------------------------
    steps.append("\n🚚 Moving to dispatch zone")
    steps.append("📲 Assigning delivery partner")
    steps.append("✅ Order dispatched successfully!")

    cur.close()
    conn.close()

    return "\n".join(steps)