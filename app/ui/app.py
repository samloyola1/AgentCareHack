import streamlit as st
import requests
from datetime import datetime
from typing import Optional

# ==========================================================
# Configuration
# ==========================================================

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="AgentCare",
    page_icon="🏥",
    layout="wide"
)

# ==========================================================
# Session State
# ==========================================================

if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

# ==========================================================
# API Helpers
# ==========================================================

def auth_headers():
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}

def api_get(endpoint):
    try:
        return requests.get(API_URL + endpoint, headers=auth_headers(), timeout=20)
    except Exception as e:
        st.error(e); return None

def api_post(endpoint, data=None, files=None):
    try:
        return requests.post(
            API_URL + endpoint,
            json=data if files is None else None,
            files=files,
            headers=auth_headers(),
            timeout=60
        )
    except Exception as e:
        st.error(e); return None

def api_put(endpoint, data):
    try:
        return requests.put(API_URL + endpoint, json=data, headers=auth_headers(), timeout=30)
    except Exception as e:
        st.error(e); return None

def api_delete(endpoint):
    try:
        return requests.delete(API_URL + endpoint, headers=auth_headers(), timeout=30)
    except Exception as e:
        st.error(e); return None

# ==========================================================
# Authentication
# ==========================================================

def login(username, password):
    response = api_post("/auth/login", {"username": username, "password": password})
    if not response or response.status_code != 200:
        st.error("Invalid username or password."); return False
    st.session_state.token = response.json()["access_token"]
    load_current_user(); return True

def load_current_user():
    response = api_get("/auth/me")
    if response and response.status_code == 200:
        st.session_state.user = response.json()

def logout():
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.page = "Dashboard"
    st.rerun()

# ==========================================================
# Login & Register Pages
# ==========================================================

def login_page():
    st.title("🏥 AgentCare")
    st.subheader("Healthcare Administration System")
    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
    if submitted and login(username, password):
        st.success("Login successful."); st.rerun()
    st.info("Don't have an account? Register below.")
    if st.button("Register"):
        st.session_state.page = "Register"; st.rerun()

def register_page():
    st.title("Create Account")
    with st.form("register"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm Password", type="password")
        role = st.selectbox("Role", ["patient", "staff"])
        submit = st.form_submit_button("Create Account")
    if submit:
        if password != confirm:
            st.error("Passwords do not match."); return
        response = api_post("/auth/register", {
            "username": username, "email": email, "password": password, "role": role
        })
        if response and response.status_code in (200, 201):
            st.success("Registration successful.")
            st.session_state.page = "Login"; st.rerun()
        else:
            st.error(response.text if response else "Error")
    if st.button("Back to Login"):
        st.session_state.page = "Login"; st.rerun()

# ==========================================================
# Sidebar
# ==========================================================

def sidebar():
    with st.sidebar:
        st.title("🏥 AgentCare")
        user = st.session_state.user
        st.write(f"**User:** {user['username']}")
        st.write(f"**Role:** {user['role']}")
        page = st.radio("Navigation", [
            "Dashboard", "Profile", "Appointments", "Documents",
            "AI Requests", "Workflow History", "Reminders"
        ])
        if user["role"] == "admin":
            admin_page = st.radio("Administration", ["Users", "Audit Logs"])
            if admin_page: page = admin_page
        if st.button("Logout"): logout()
    st.session_state.page = page

# ==========================================================
# Dashboard
# ==========================================================

def dashboard_page():
    st.title("🏥 Dashboard")
    response = api_get("/patients/dashboard")
    if not response or response.status_code != 200:
        st.error("Unable to load dashboard."); return
    dashboard = response.json()
    stats = dashboard.get("stats", {})
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Appointments", stats.get("appointments", 0))
    col2.metric("Documents", stats.get("documents", 0))
    col3.metric("Reminders", stats.get("reminders", 0))
    col4.metric("Workflows", stats.get("workflows", 0))
    st.divider()
    left, right = st.columns([2, 1])
    with left:
        st.subheader("Upcoming Appointments")
        appointments = dashboard.get("appointments", [])
        if appointments:
            for appt in appointments:
                with st.expander(f"{appt['appointment_date']} - {appt['doctor_name']}"):
                    st.write(f"**Department:** {appt['department']}")
                    st.write(f"**Doctor:** {appt['doctor_name']}")
                    st.write(f"**Status:** {appt['status']}")
                    st.write(f"**Reason:** {appt.get('reason','')}")
        else: st.info("No upcoming appointments.")
        st.divider()
        st.subheader("Recent Workflow Activity")
        workflows = dashboard.get("workflows_history", [])
        if workflows:
            for wf in workflows[:5]:
                st.write(f"• {wf['workflow_type']} ({wf['status']})")
        else: st.info("No workflow history.")
    with right:
        st.subheader("Pending Reminders")
        reminders = dashboard.get("reminders", [])
        if reminders:
            for reminder in reminders: st.warning(reminder["message"])
        else: st.success("No pending reminders.")
        st.divider()
        st.subheader("Quick Actions")
        if st.button("📅 Book Appointment", use_container_width=True):
            st.session_state.page = "Appointments"; st.rerun()
        if st.button("📄 Upload Document", use_container_width=True):
            st.session_state.page = "Documents"; st.rerun()
        if st.button("🤖 New AI Request", use_container_width=True):
            st.session_state.page = "AI Requests"; st.rerun()
        if st.button("👤 Edit Profile", use_container_width=True):
            st.session_state.page = "Profile"; st.rerun()

# ==========================================================
# Profile, Appointments, Documents
# ==========================================================
# (Keep your existing implementations from the attachment here)

# ==========================================================
# Workflow History
# ==========================================================

def workflow_page():
    st.title("📊 Workflow History")
    response = api_get("/patients/me/workflows")
    if not response or response.status_code != 200:
        st.error("Unable to load workflow history."); return
    workflows = response.json()
    if not workflows:
        st.info("No workflow history found."); return
    for workflow in workflows:
        title = f"{workflow.get('workflow_type','Workflow')} - {workflow.get('status','Pending')}"
        with st.expander(title):
            st.write(f"Department: {workflow.get('department','-')}")
            st.write(f"Priority: {workflow.get('priority','-')}")
            st.write(f"Created: {workflow.get('created_at','-')}")
            if workflow.get("summary"):
                st.markdown("### Summary"); st.write(workflow["summary"])
            if workflow.get("recommendation"):
                st.markdown("### Recommendation"); st.success(workflow["recommendation"])

# ==========================================================
# Reminders
# ==========================================================

def reminders_page():
    st.title("🔔 Reminders")
    response = api_get("/reminders/me")
    if not response or response.status_code != 200:
        st.error("Unable to load reminders."); return
    reminders = response.json()
    if not reminders:
        st.success("No pending reminders."); return
    for reminder in reminders:
        with st.container():
            st.subheader(reminder.get("title","Reminder"))
            st.write(reminder.get("message",""))
            st.write(f"Status: {reminder.get('status','Pending')}")
            st.write(f"Due: {reminder.get('due_date','-')}")
            st.divider()

# ==========================================================
# Admin Users
# ==========================================================

def users_page():
    st.title("👥 Users")
    response = api_get("/admin/users")
    if not response or response.status_code != 200:
        st.error("Unable to connect."); return
    users = response.json()
    if not users:
        st.info("No users found."); return
    
    for user in users:
        with st.expander(f"User: {user.get('username', 'N/A')} (ID: {user.get('id', 'N/A')})"):
            st.write(f"**Username:** {user.get('username', 'N/A')}")
            st.write(f"**Email:** {user.get('email', 'N/A')}")
            st.write(f"**Role:** {user.get('role', 'N/A')}")
            st.write(f"**Created At:** {user.get('created_at', 'N/A')}")
            st.button(f"Edit {user.get('username', 'User')}", key=f"edit_{user.get('id')}")
            st.button(f"Delete {user.get('username', 'User')}", key=f"delete_{user.get('id')}")
