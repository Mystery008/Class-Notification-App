import streamlit as st
from datetime import datetime, timedelta
from supabase_setup import init_supabase

st.set_page_config(page_title="Notification Student History", layout="wide")

supabase = init_supabase()

st.title("Notification: Faculty Not Present")

# ----------------- Auth Check -----------------
if "user" not in st.session_state or st.session_state.user is None:
    st.error("Please login to continue.")
    st.stop()

user = st.session_state.user

# ---------------- Student View ----------------
if user["role"] == "student":
    st.header("📩 Inform Faculty Absence")

    # Load Timetable entries for student's division
    timetable_data = supabase.table("timetable").select("*").eq("division", user["division"]).execute().data

    if not timetable_data:
        st.warning("No timetable found for your division.")
        st.stop()

    # Step 1: Subject Dropdown
    subjects = sorted(set(entry["subject"] for entry in timetable_data))
    subject = st.selectbox("🎯 Select Subject", ["Select subject"] + subjects)

    # Step 2: Faculty Dropdown (after subject selection)
    if subject != "Select subject":
        faculty_list = sorted(set(entry["faculty"] for entry in timetable_data if entry["subject"] == subject))
        faculty_short_map = {f: f[:3].upper() for f in faculty_list}
        faculty_display = [f"{faculty_short_map[f]} - {f}" for f in faculty_list]
        faculty_choice = st.selectbox("👤 Select Faculty", ["Select faculty"] + faculty_display)
        faculty_email = next((f for f in faculty_list if f"{faculty_short_map[f]} - {f}" == faculty_choice), None)
    else:
        faculty_email = None

    # Step 3: Date Picker
    selected_date = st.date_input("📅 Select Date", value=datetime.today())
    selected_day = selected_date.strftime("%A")

    # Step 4: Time Slot from Timetable
    if subject != "Select subject" and faculty_email:
        time_slots = sorted(set(
            entry["time"]
            for entry in timetable_data
            if entry["subject"] == subject and entry["faculty"] == faculty_email and entry["day"] == selected_day
        ))
        time_slot = st.selectbox("🕒 Select Time Slot", ["Select time"] + time_slots if time_slots else ["No slot available"])
    else:
        time_slot = None

    # Submit Button
    if subject != "Select subject" and faculty_email and time_slot and time_slot != "Select time":
        if st.button("🚨 Submit "):
            new_note = {
                "username": user["username"],
                "role": "student",
                "division": user["division"],
                "faculty": faculty_email,
                "subject": subject,
                "date": selected_date.strftime("%Y-%m-%d"),
                "day": selected_day,
                "time": time_slot,
                "status": "Faculty not present",
                "message": "Reported faculty absence",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            supabase.table("notifications").insert(new_note).execute()
            st.success("📬 Report submitted successfully!")

    # ---------------- View Sent Notifications ----------------
    st.markdown("---")
    st.subheader("📚 Your Sent Notifications")

    student_notes = supabase.table("notifications").select("*") \
        .eq("username", user["username"]).eq("role", "student") \
        .order("date").execute().data

    if not student_notes:
        st.info("You haven't submitted any reports yet.")
    else:
        for n in student_notes:
            n["date_obj"] = datetime.strptime(n["date"], "%Y-%m-%d")

        student_notes.sort(key=lambda x: x["date_obj"])
        first_date = student_notes[0]["date_obj"]
        base_week_start = first_date - timedelta(days=first_date.weekday())
        grouped_weeks = {}

        for note in student_notes:
            week_index = ((note["date_obj"] - base_week_start).days) // 7 + 1
            grouped_weeks.setdefault(week_index, []).append(note)

        today = datetime.today()
        current_week_index = ((today - base_week_start).days) // 7 + 1

        if current_week_index in grouped_weeks:
            st.markdown(f"### 📅 Current Week (Week {current_week_index})")
            for idx, n in enumerate(grouped_weeks[current_week_index], 1):
                st.markdown(f"**{idx}. {n['subject']} | {n['day']} | {n['time']} | {n['faculty'][:3]} | {n['date']}**")
                st.markdown(f"Message: {n['message']}")
                if isinstance(n.get("response"), dict) and "message" in n["response"]:
                    st.success(f"Faculty Response: {n['response']['message']}")
                else:
                    st.info("Awaiting faculty response...")

        for week_num in sorted(grouped_weeks):
            if week_num == current_week_index:
                continue
            with st.expander(f"📦 Week {week_num}"):
                for idx, n in enumerate(grouped_weeks[week_num], 1):
                    st.markdown(f"**{idx}. {n['subject']} | {n['day']} | {n['time']} | {n['faculty'][:3]} | {n['date']}**")
                    st.markdown(f"Message: {n['message']}")
                    if isinstance(n.get("response"), dict) and "message" in n["response"]:
                        st.success(f"Faculty Response: {n['response']['message']}")
                    else:
                        st.info("Awaiting faculty response...")

# ---------------- Faculty View ----------------
elif user["role"] == "faculty":
    st.header("Student Notifications")

    notes = supabase.table("notifications").select("*") \
        .eq("role", "student").eq("faculty", user["username"]).execute().data

    if not notes:
        st.info("No student notifications found.")
    else:
        for idx, n in enumerate(reversed(notes), 1):
            st.markdown(f"**{idx}. {n['subject']} | {n['date']} | {n['time']} | Student: {n['username']}**")
            st.markdown(f"Message: {n['message']}")

            response_data = n.get("response")
            if isinstance(response_data, dict) and "message" in response_data:
                st.info(f"You responded: {response_data['message']}")
            else:
                col1, col2, col3, col4 = st.columns(4)
                if col1.button("I'm coming", key=f"coming_{idx}"):
                    supabase.table("notifications").update({
                        "response": {"by": user["username"], "message": "I'm coming"}
                    }).eq("timestamp", n["timestamp"]).execute()
                    st.rerun()
                if col2.button("I'm unavailable", key=f"unavail_{idx}"):
                    supabase.table("notifications").update({
                        "response": {"by": user["username"], "message": "I'm unavailable"}
                    }).eq("timestamp", n["timestamp"]).execute()
                    st.rerun()
                if col3.button("Contact Coordinator", key=f"coord_{idx}"):
                    supabase.table("notifications").update({
                        "response": {"by": user["username"], "message": "Contact Class Coordinator"}
                    }).eq("timestamp", n["timestamp"]).execute()
                    st.rerun()
                if col4.button("🗑️ Delete", key=f"delete_{idx}"):
                    supabase.table("notifications").delete().eq("timestamp", n["timestamp"]).execute()
                    st.rerun()
else:
    st.warning("This page is restricted to students and faculty.")
