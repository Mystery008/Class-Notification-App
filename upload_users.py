import json
from supabase_setup import init_supabase

supabase = init_supabase()

# Load users.json
with open("users.json", "r") as f:
    users = json.load(f)

# Upsert each user (insert or update)
for user in users:
    supabase.table("users").upsert(user).execute()

print("All users upserted successfully.")
