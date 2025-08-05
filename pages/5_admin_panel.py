import streamlit as st
from supabase_setup import init_supabase
import ast

st.set_page_config(page_title="Admin Panel", layout="wide")

supabase = init_supabase()

# -------------------- Auth Check --------------------
user = st.session_state.get("user")
if not user or user.get("role") != "admin":
    st.error("🚫 Access denied. Only admins can view this page.")
    st.stop()

st.title("🛠️ Admin Panel - Faculty Management")

# -------------------- Load Faculty Users --------------------
@st.cache_data(ttl=30)
def get_faculty_users():
    result = supabase.table("users").select("*").eq("role", "faculty").execute()
    return result.data if result.data else []

faculty_users = get_faculty_users()

# -------------------- Handle Success Messages --------------------
if "status_message" in st.session_state:
    st.success(st.session_state.status_message)
    del st.session_state["status_message"]

# -------------------- Show & Edit Faculty Users --------------------
st.subheader("👨‍🏫 Existing Faculty Users")

for idx, user in enumerate(faculty_users):
    with st.expander(user["username"]):
        st.write(f"**Subjects**: {', '.join(user.get('subjects', []))}")
        st.write(f"**Divisions**: {', '.join(user.get('divisions', []))}")

        new_subjects = st.text_input("Edit Subjects", ", ".join(user.get("subjects", [])), key=f"sub_{idx}")
        new_divisions = st.text_input("Edit Divisions", ", ".join(user.get("divisions", [])), key=f"div_{idx}")
        new_password = st.text_input("Edit Password", user["password"], type="password", key=f"pwd_{idx}")

        if st.button(f"💾 Update {user['username']}", key=f"update_{idx}"):
            supabase.table("users").update({
                "subjects": [s.strip() for s in new_subjects.split(",") if s.strip()],
                "divisions": [d.strip() for d in new_divisions.split(",") if d.strip()],
                "password": new_password
            }).eq("username", user["username"]).execute()
            st.session_state.status_message = f"✅ Updated {user['username']}"
            st.cache_data.clear()
            st.rerun()

        if st.button(f"🗑️ Delete {user['username']}", key=f"delete_{idx}"):
            supabase.table("users").delete().eq("username", user["username"]).execute()
            st.session_state.status_message = f"✅ Deleted {user['username']}"
            st.cache_data.clear()
            st.rerun()

# -------------------- Add New Faculty --------------------
st.markdown("---")
st.subheader("➕ Add New Faculty")

new_username = st.text_input("Username (email)", key="new_username")
new_password = st.text_input("Password", key="new_password")
new_subjects = st.text_input("Subjects (comma-separated)", key="new_subjects")
new_divisions = st.text_input("Divisions (comma-separated)", key="new_divisions")

if st.button("➕ Create Faculty"):
    exists = supabase.table("users").select("username").eq("username", new_username).execute()
    if exists.data:
        st.error("⚠️ A user with this username already exists.")
    else:
        new_user = {
            "username": new_username,
            "password": new_password,
            "role": "faculty",
            "subjects": [s.strip() for s in new_subjects.split(",") if s.strip()],
            "divisions": [d.strip() for d in new_divisions.split(",") if d.strip()]
        }
        supabase.table("users").insert(new_user).execute()
        st.session_state.status_message = "✅ New faculty added successfully."
        st.cache_data.clear()
        st.rerun()
