from database.database_manager import get_pill_by_id

print("RxSort starting...")

pill_id = int(input("Simulated AI pill ID: "))

pill = get_pill_by_id(pill_id)

if pill:
    print("\nPill identified:")
    print("Medication:", pill[1])
    print("Strength:", pill[3])
    print("Color:", pill[5])
    print("Shape:", pill[6])
else:
    print("\nUnknown Pill - send to reject bin.")
