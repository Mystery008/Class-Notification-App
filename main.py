import streamlit as st
from supabase_setup import init_supabase

# --------------------------
# App Configuration
# --------------------------
st.set_page_config(page_title="Class Tracker App", layout="centered")

# --------------------------
# Global Font Styling
# --------------------------
st.markdown("""
    <style>
    html, body, [class*="css"]  {
        font-size: 18px !important;
        font-family: "Segoe UI", sans-serif !important;
    }
    .sidebar-label {
        font-size: 18px;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 4px;
    }
    .sidebar-value {
        font-size: 17px;
        font-weight: 400;
        color: #dcdcdc;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Class Schedule & Notification Tracker")

# --------------------------
# Supabase Configuration
# --------------------------
supabase = init_supabase()

# --------------------------
# Session Initialization
# --------------------------
if "user" not in st.session_state:
    st.session_state.user = None

# --------------------------
# Login Section
# --------------------------
if st.session_state.user is None:
    st.subheader("🔐 Login to your account")
    st.markdown("Please enter your login credentials below.")

    email = st.text_input("📧 Username")
    password = st.text_input("🔒 Password", type="password")

    if st.button("➡️ Login"):
        try:
            response = supabase.table('users').select("*").eq('username', email).eq('password', password).execute()
            if response.data:
                user_found = response.data[0]
                st.session_state.user = user_found
                st.success(f"✅ Welcome, **{user_found['username']}** ({user_found['role'].capitalize()})")
                st.rerun()
            else:
                st.error("❌ Invalid credentials. Please try again.")
        except Exception as e:
            st.error(f"⚠️ Error connecting to database: {str(e)}")

# --------------------------
# Logged-In Home Page
# --------------------------
else:
    user = st.session_state.user
    username = user["username"]
    role = user["role"].capitalize()

    with st.sidebar:
        st.markdown(f"""
            <div class="sidebar-label">👤 <strong>Account</strong></div>
            <div class="sidebar-label">User:</div>
            <div class="sidebar-value">{username}</div>
            <div class="sidebar-label">Role:</div>
            <div class="sidebar-value">{role}</div>
            <hr style="margin: 10px 0 10px 0;">
        """, unsafe_allow_html=True)

        if st.button("Logout"):
            st.session_state.user = None
            st.rerun()

    st.markdown("---")
    st.markdown("### Welcome to the **Class Tracker System**")
    st.markdown("Use the **sidebar** to access available tools based on your role.")

    if user["role"] == "admin":
        st.info("⚙️ As an Admin, you can manage faculty from the **Admin Panel**.")

    st.markdown("""
    #### Features Available:
    - 📅 **Timetable View**: View or filter your weekly class schedule  
    - 📣 **Notifications**: Submit/view class status and responses  
    - 📊 **Monthly Report**: Visualize per-subject statistics (faculty only)  
    - 🛠️ **Admin Panel**: Manage faculty records (admin only)
    """)

    st.markdown("---")
