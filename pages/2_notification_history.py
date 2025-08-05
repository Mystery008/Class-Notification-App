import streamlit as st
import pandas as pd
from datetime import datetime
from supabase_setup import init_supabase


st.set_page_config(page_title="notification_history", layout="wide")  # optional but helpful


supabase = init_supabase()

# --------------------------- Auth Check ---------------------------
if "user" not in st.session_state or st.session_state.user is None:
    st.error("Please log in to view this page.")
    st.stop()

user = st.session_state.user
username = user["username"]
role = user["role"]
division = user.get("division", "")

st.title("📜 Notification History")

# --------------------------- Fetch Notifications ---------------------------
if role == "faculty":
    response = supabase.table("notifications").select("*").eq("role", "faculty").eq("username", username).execute()
else:
    # For students, fetch notifications from their division posted by faculty
    response = supabase.table("notifications").select("*").eq("role", "faculty").eq("division", division).execute()

notifications_all = response.data if response.data else []

if not notifications_all:
    st.info("No faculty-submitted notifications found.")
    st.stop()

# --------------------------- Convert to DataFrame ---------------------------
df = pd.DataFrame(notifications_all)

# --------------------------- Sidebar Filters ---------------------------
st.sidebar.header("🔎 Filters")

subject_filter = st.sidebar.selectbox("Filter by Subject", ["All"] + sorted(df["subject"].unique()))
if subject_filter != "All":
    df = df[df["subject"] == subject_filter]

start_date = st.sidebar.date_input("From Date", value=None)
end_date = st.sidebar.date_input("To Date", value=None)

if start_date:
    df = df[pd.to_datetime(df["date"]) >= pd.to_datetime(start_date)]
if end_date:
    df = df[pd.to_datetime(df["date"]) <= pd.to_datetime(end_date)]

# --------------------------- Pagination ---------------------------
df = df.sort_values(by="timestamp", ascending=False).reset_index(drop=True)
page_size = 10
page_num = st.sidebar.number_input("Page", min_value=1, max_value=max(1, (len(df) - 1) // page_size + 1), step=1)
start_idx = (page_num - 1) * page_size
end_idx = start_idx + page_size
df_page = df.iloc[start_idx:end_idx]

# --------------------------- Display Notifications ---------------------------
for idx, row in df_page.iterrows():
    st.markdown(f"### {idx+1}. {row['subject']} on {row['day']} at {row['time']}")
    st.markdown(f"""
    - 📘 **Division**: {row.get('division')}
    - 🧪 **Type**: {row.get('type', 'N/A')}
    - 📌 **Status**: _{row.get('status')}_  
    - 🕒 **Timestamp**: {row.get('timestamp')}
    """)

    # Undo only for faculty
    if role == "faculty":
        if st.button("↩️ Undo Notification", key=f"undo_{idx}"):
            supabase.table("notifications").delete().eq("timestamp", row["timestamp"]).eq("username", username).execute()
            st.success("Notification undone.")
            st.rerun()
    
    st.markdown("---")
