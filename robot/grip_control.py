def get_grip_pressure(weight, fragile):
    if fragile:
        return 20
    elif weight < 300:
        return 30
    elif weight < 1000:
        return 50
    else:
        return 70