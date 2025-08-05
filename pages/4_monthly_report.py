import streamlit as st
import pandas as pd
from datetime import datetime
from calendar import monthrange
from supabase_setup import init_supabase
import plotly.express as px
import io

st.set_page_config(page_title="📊 Monthly Report", layout="wide")

# -------------------- Initialize Supabase --------------------
supabase = init_supabase()

# -------------------- Authentication --------------------
if "user" not in st.session_state or st.session_state.user is None:
    st.error("Please log in to access this page.")
    st.stop()

user = st.session_state.user
username = user.get("username")
role = user.get("role")

st.title("📊 Monthly Class Report")

# -------------------- Fetch Faculty's Timetable --------------------
timetable_resp = supabase.table("timetable").select("*").eq("faculty", username).execute()
timetable = timetable_resp.data if timetable_resp.data else []

division_subject_map = {}
for entry in timetable:
    div = entry.get("division")
    subj = entry.get("subject")
    if div and subj:
        division_subject_map.setdefault(div, set()).add(subj)

divisions = sorted(division_subject_map.keys())

if not divisions:
    st.warning("No division or subject assigned to you in the timetable.")
    st.stop()

selected_division = st.selectbox("Select Division", divisions)
assigned_subjects = list(division_subject_map.get(selected_division, []))

# -------------------- Month & Year Selector --------------------
month = st.selectbox("Select Month", list(range(1, 13)), index=datetime.now().month - 1)
current_year = datetime.now().year
year = st.selectbox("Select Year", list(range(2025, current_year + 1)), index=0)

# -------------------- Safe Date Range --------------------
month_str = str(month).zfill(2)
last_day = monthrange(year, month)[1]
start_date = f"{year}-{month_str}-01"
end_date = f"{year}-{month_str}-{str(last_day).zfill(2)}"

# -------------------- Fetch Notifications --------------------
faculty_noti = supabase.table("notifications").select("*")\
    .eq("role", "faculty")\
    .eq("username", username)\
    .eq("division", selected_division)\
    .in_("subject", assigned_subjects)\
    .gte("date", start_date).lte("date", end_date).execute().data

student_noti = supabase.table("notifications").select("*")\
    .eq("role", "student")\
    .eq("division", selected_division)\
    .in_("subject", assigned_subjects)\
    .gte("date", start_date).lte("date", end_date).execute().data

# -------------------- Convert to DataFrames --------------------
df_fac = pd.DataFrame(faculty_noti)
df_stu = pd.DataFrame(student_noti)

# -------------------- Clean and Validate --------------------
for df in [df_fac, df_stu]:
    for col in ["date", "time", "subject", "status", "username", "division", "response"]:
        if col not in df.columns:
            df[col] = None

    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df.dropna(subset=["date"], inplace=True)
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")

# -------------------- Prepare Faculty Not Present --------------------
faculty_not_present = []
if not df_stu.empty:
    grouped = df_stu.groupby(["date", "time", "subject"])
    for (date, time, subject), group in grouped:
        fac_match = df_fac[
            (df_fac["date"] == date) &
            (df_fac["time"] == time) &
            (df_fac["subject"] == subject)
        ]
        if fac_match.empty or fac_match.iloc[0].get("response", "").strip().lower() == "i'm unavailable":
            faculty_not_present.append({
                "subject": subject,
                "status": "Faculty Not Present",
                "username": username,
                "division": selected_division,
                "date": date
            })

# -------------------- Combine All --------------------
status_records = []

if not df_fac.empty:
    for _, row in df_fac.iterrows():
        status_records.append({
            "subject": row.get("subject", "Unknown"),
            "status": row.get("status", "Unknown"),
            "username": row.get("username", "N/A"),
            "division": row.get("division", selected_division),
            "date": row.get("date", "")
        })

status_records.extend(faculty_not_present)

if not status_records:
    st.info("No class notifications available for this month and division.")
    st.stop()

df_summary = pd.DataFrame(status_records)

# -------------------- Debug Summary --------------------
with st.expander("📂 Debug: Summary Data"):
    st.dataframe(df_summary)

# -------------------- Aggregate --------------------
df_agg = df_summary.groupby(["subject", "status"]).size().reset_index(name="Count")

# -------------------- Plot --------------------
fig = px.bar(
    df_agg,
    x="subject",
    y="Count",
    color="status",
    barmode="stack",
    text_auto=True,
    title=f"📊 Monthly Class Report - {selected_division} ({datetime(year, month, 1).strftime('%B %Y')})"
)
fig.update_layout(
    yaxis_title="Total Classes (per status)",
    xaxis_title="Subject",
    legend_title="Class Status",
    height=500
)

st.plotly_chart(fig, use_container_width=True)

# -------------------- Excel Export --------------------
def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Monthly Report")
    return output.getvalue()

excel_data = convert_df_to_excel(df_summary)
st.download_button(
    label="📥 Download Full Report as Excel (.xlsx)",
    data=excel_data,
    file_name=f"{selected_division}_{month}_{year}_report.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
