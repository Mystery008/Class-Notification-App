import json
import os
from supabase_setup import init_supabase

supabase = init_supabase()

# ---------------------- Load JSON ----------------------
TIMETABLE_FILE = "timetable.json"

if not os.path.exists(TIMETABLE_FILE):
    print("timetable.json not found.")
    exit()

with open(TIMETABLE_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------------------- Upload Data ----------------------
success_count = 0
fail_count = 0

for row in data:
    try:
        payload = {
            "day": row.get("day", ""),
            "time": row.get("time", ""),
            "subject": row.get("subject", ""),
            "faculty": row.get("faculty", ""),
            "division": row.get("division", ""),
            "batch": row.get("batch"),  # Can be None
            "room": row.get("room", ""),
            "type": row.get("type", "")
        }

        response = supabase.table("timetable").insert(payload, upsert=True).execute()

        if response.data:
            success_count += 1
        else:
            print("⚠️ Failed insert:", payload)
            fail_count += 1
    except Exception as e:
        print("Error inserting row:", row)
        print("Exception:", e)
        fail_count += 1

# ---------------------- Summary ----------------------
print("\nUpload completed:")
print(f"  Inserted/Updated: {success_count}")
print(f"  Failed          : {fail_count}")
