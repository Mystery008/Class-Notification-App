import streamlit as st
import datetime
import pandas as pd
from supabase_setup import init_supabase

st.set_page_config(page_title="timetable", layout="wide")  # optional but helpful

# Initialize Supabase
supabase = init_supabase()

# -----------------------------
# Helpers
# -----------------------------
def get_today():
    return datetime.datetime.now().strftime("%A")

def get_today_date():
    return datetime.datetime.now().strftime("%Y-%m-%d")

def get_user_timetable(user):
    all_timetable = supabase.table("timetable").select("*").execute().data
    if user["role"] == "faculty":
        return [entry for entry in all_timetable if entry.get("faculty") == user["username"]]
    elif user["role"] == "student":
        return [entry for entry in all_timetable if entry.get("division") == user.get("division")]
    return []

def get_notifications():
    return supabase.table("notifications").select("*").execute().data

def render_timetable(entries, day, notifications, user):
    today_entries = [e for e in entries if e.get("day") == day]
    today_entries = sorted(today_entries, key=lambda x: x.get("time", ""))

    if not today_entries:
        st.info("No classes scheduled.")
    else:
        for idx, entry in enumerate(today_entries, start=1):
            faculty_username = entry.get("faculty", "")
            faculty_short = faculty_username[:3].upper() if faculty_username else "FAC"
            class_type = "🧪 Lab" if entry.get("type") == "Lab" else "📖 Lecture"

            st.markdown(
                f"**{idx}. {entry['time']}** | {class_type} - {entry['subject']} | 👤 {faculty_short} | Room: {entry.get('room', '')} | Division: {entry.get('division', '')} | Batch: {entry.get('batch', '')}"
            )

            if user["role"] == "faculty":
                existing = [n for n in notifications if n.get("role") == "faculty" and
                            n.get("username") == user["username"] and
                            n.get("subject") == entry["subject"] and
                            n.get("day") == entry["day"] and
                            n.get("time") == entry["time"]]

                if not existing:
                    col1, col2, col3 = st.columns(3)

                    if col1.button("✅ Class Happened", key=f"happened_{idx}_{day}"):
                        new_note = {
                            "username": user["username"],
                            "role": "faculty",
                            "subject": entry["subject"],
                            "division": entry.get("division", ""),
                            "day": day,
                            "date": get_today_date(),
                            "time": entry["time"],
                            "faculty": entry.get("faculty"),
                            "type": entry.get("type", ""),
                            "status": "Class Happened",  # ✅ Fixed label
                            "message": "Class was held successfully.",
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        supabase.table("notifications").insert(new_note).execute()
                        st.success("📩 Notification: Class Happened added.")
                        st.rerun()

                    if col2.button("❌ Class Cancelled", key=f"cancelled_{idx}_{day}"):
                        new_note = {
                            "username": user["username"],
                            "role": "faculty",
                            "subject": entry["subject"],
                            "division": entry.get("division", ""),
                            "day": day,
                            "date": get_today_date(),
                            "time": entry["time"],
                            "faculty": entry.get("faculty"),
                            "type": entry.get("type", ""),
                            "status": "Cancelled",  # ✅ Consistent
                            "message": "Class was cancelled.",
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        supabase.table("notifications").insert(new_note).execute()
                        st.warning("📩 Notification: Class Cancelled added.")
                        st.rerun()

                    if col3.button("🚫 No Students Present", key=f"absent_{idx}_{day}"):
                        new_note = {
                            "username": user["username"],
                            "role": "faculty",
                            "subject": entry["subject"],
                            "division": entry.get("division", ""),
                            "day": day,
                            "date": get_today_date(),
                            "time": entry["time"],
                            "faculty": entry.get("faculty"),
                            "type": entry.get("type", ""),
                            "status": "No Students Present",  # ✅ Consistent
                            "message": "No students attended the lecture.",
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        supabase.table("notifications").insert(new_note).execute()
                        st.warning("📩 Notification: No Students Present added.")
                        st.rerun()
                else:
                    col1, col2 = st.columns([6, 1])
                    col1.info(f"📌 Notification already sent: {existing[0]['status']}")
                    if col2.button("↩️ Undo", key=f"undo_{idx}_{day}"):
                        supabase.table("notifications").delete().eq("timestamp", existing[0]["timestamp"]).execute()
                        st.warning("⏪ Notification removed.")
                        st.rerun()

# -----------------------------
# Page Logic
# -----------------------------
if "user" not in st.session_state or st.session_state.user is None:
    st.error("🚫 You must be logged in to view the timetable.")
    st.stop()

st.title("📚 Class Timetable Viewer")

user = st.session_state.user
entries = get_user_timetable(user)
notifications = get_notifications()

# Filter by Subject
subjects = sorted(set(e["subject"] for e in entries))
selected_subjects = st.multiselect("🎯 Filter by Subjects:", subjects, default=subjects)
filtered = [e for e in entries if e["subject"] in selected_subjects]

# View Mode
st.markdown("---")
view_mode = st.radio("View Mode:", ["📅 Today's View", "📆 Full Week View"], horizontal=True)

if view_mode == "📅 Today's View":
    st.subheader(f"📌 Timetable for {get_today()} ({get_today_date()})")
    render_timetable(filtered, get_today(), notifications, user)

elif view_mode == "📆 Full Week View":
    week_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    for day in week_days:
        daily_entries = [e for e in filtered if e["day"] == day]
        if daily_entries:
            st.markdown(f"### 📌 {day}")
            df = pd.DataFrame(daily_entries)
            df['faculty_short'] = df['faculty'].apply(lambda x: x[:3].upper() if pd.notna(x) else 'FAC')
            for col in ["time", "subject", "type", "room", "division", "batch", "faculty_short"]:
                if col not in df.columns:
                    df[col] = ""
            df = df[["time", "subject", "type", "faculty_short", "room", "division", "batch"]]
            df.index = df.index + 1
            st.dataframe(df.rename(columns={
                "time": "Time",
                "subject": "Subject",
                "type": "Type",
                "faculty_short": "Faculty",
                "room": "Room",
                "division": "Division",
                "batch": "Batch"
            }), use_container_width=True)

    df_all = pd.DataFrame(filtered)
    if not df_all.empty:
        df_all['faculty_short'] = df_all['faculty'].apply(lambda x: x[:3].upper() if pd.notna(x) else 'FAC')
        df_all.index = df_all.index + 1
        csv = df_all.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download Full Timetable as CSV", 
            csv, 
            "timetable.csv", 
            "text/csv",
            key="download_full_timetable"
        )
