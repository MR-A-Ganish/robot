from database import connect_db

def process_order(items):

    conn = connect_db()
    cur = conn.cursor()

    steps = []
    steps.append("🤖 Robot Activated...\n")

    item_locations = []

    for item in items:
        cur.execute(
            "SELECT aisle, shelf, position FROM products WHERE id=%s",
            (item["id"],)
        )
        location = cur.fetchone()

        if location:
            aisle, shelf, pos = location

            # fallback safety
            aisle = aisle or "A"
            shelf = shelf or "1"
            pos = pos or 1

            item_locations.append((aisle, shelf, pos, item))
        else:
            steps.append(f"❌ Item {item['name']} not found")

    # sort path
    item_locations.sort(key=lambda x: (x[0], x[1], x[2]))

    current_aisle = None

    for aisle, shelf, pos, item in item_locations:

        if aisle != current_aisle:
            steps.append(f"\n➡️ Moving to Aisle {aisle}")
            current_aisle = aisle

        steps.append(f"📦 Shelf {shelf}")
        steps.append(f"📍 Position {pos}")
        steps.append(f"🛒 Picking {item['name']}")

        if item.get("fragile", False):
            steps.append("🤏 Soft grip")
        else:
            steps.append("✊ Normal grip")

        if item.get("weight", 0) > 800:
            steps.append("⚠️ Heavy item detected")

        steps.append("✅ Picked")

    steps.append("\n📦 Packing items")
    steps.append("🚚 Ready for delivery")

    cur.close()
    conn.close()

    return "\n".join(steps)