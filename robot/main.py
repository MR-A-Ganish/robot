from database import connect_db

# -------------------------------
# ROBOT PROCESS ORDER
# -------------------------------
def process_order(items):
    """
    items = [
        {"name": "Milk", "weight": 500, "fragile": False},
        {"name": "Eggs", "weight": 200, "fragile": True}
    ]
    """

    conn = connect_db()
    cur = conn.cursor()

    steps = []
    steps.append("🤖 Robot Activated...\n")

    # 🔥 Sort items by aisle for efficient movement (basic optimization)
    item_locations = []

    for item in items:
        cur.execute(
            "SELECT aisle, shelf, position FROM products WHERE name=%s",
            (item["name"],)
        )
        location = cur.fetchone()

        if location:
            aisle, shelf, pos = location
            item_locations.append((aisle, shelf, pos, item))
        else:
            steps.append(f"❌ Item '{item['name']}' not found in warehouse")

    # 🔥 Sort by aisle → shelf → position (simple path optimization)
    item_locations.sort(key=lambda x: (x[0], x[1], x[2]))

    # -------------------------------
    # PROCESS EACH ITEM
    # -------------------------------
    current_aisle = None

    for aisle, shelf, pos, item in item_locations:

        # Move to aisle only if changed
        if aisle != current_aisle:
            steps.append(f"\n➡️ Moving to Aisle {aisle}")
            current_aisle = aisle

        steps.append(f"📦 Navigating to Shelf {shelf}")
        steps.append(f"📍 Locating Position {pos}")
        steps.append(f"🛒 Picking item: {item['name']}")

        # 🔥 Grip logic
        if item["fragile"]:
            steps.append("🤏 Using SOFT grip (fragile item)")
        else:
            steps.append("✊ Using NORMAL grip")

        # 🔥 Weight handling
        if item["weight"] > 800:
            steps.append("⚠️ Heavy item detected - adjusting grip strength")

        steps.append("✅ Item picked successfully")

    # -------------------------------
    # PACKING STAGE
    # -------------------------------
    steps.append("\n📦 Moving to packing station")

    fragile_items = [item for item in items if item["fragile"]]

    if fragile_items:
        steps.append("🧴 Using protective packaging for fragile items")

    steps.append("📦 Packing all items securely")

    # -------------------------------
    # DELIVERY ASSIGNMENT
    # -------------------------------
    steps.append("\n🚚 Moving to delivery zone")
    steps.append("📲 Assigning delivery partner...")
    steps.append("✅ Order ready for dispatch!")

    # -------------------------------
    # CLOSE DB
    # -------------------------------
    cur.close()
    conn.close()

    return "\n".join(steps)