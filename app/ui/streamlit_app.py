import streamlit as st
import requests
import time
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
        return {
            "Authorization": f"Bearer {st.session_state.token}"
        }
    return {}


def api_get(endpoint):
    try:
        return requests.get(
            API_URL + endpoint,
            headers=auth_headers(),
            timeout=20
        )
    except Exception as e:
        st.error(e)
        return None


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
        st.error(e)
        return None


def api_put(endpoint, data):

    try:
        return requests.put(
            API_URL + endpoint,
            json=data,
            headers=auth_headers(),
            timeout=30
        )
    except Exception as e:
        st.error(e)
        return None


def api_delete(endpoint):

    try:
        return requests.delete(
            API_URL + endpoint,
            headers=auth_headers(),
            timeout=30
        )
    except Exception as e:
        st.error(e)
        return None


# ==========================================================
# Authentication
# ==========================================================

def login(username, password):

    response = api_post(
        "/auth/login",
        {
            "username": username,
            "password": password
        }
    )

    if response is None:
        return False

    if response.status_code != 200:
        st.error("Invalid username or password.")
        return False

    data = response.json()

    st.session_state.token = data["access_token"]

    load_current_user()

    return True


def load_current_user():

    response = api_get("/auth/me")

    if response is None:
        return

    if response.status_code != 200:
        return

    st.session_state.user = response.json()


def logout():

    st.session_state.token = None
    st.session_state.user = None
    st.session_state.page = "Dashboard"

    st.rerun()


# ==========================================================
# Login Page
# ==========================================================

def login_page():

    st.title("🏥 AgentCare")

    st.subheader("Healthcare Administration System")

    with st.form("login"):

        username = st.text_input("Username")

        password = st.text_input(
            "Password",
            type="password"
        )

        submitted = st.form_submit_button(
            "Login"
        )

    if submitted:

        if login(username, password):

            st.success("Login successful.")

            st.rerun()

    st.info(
        "Don't have an account? Register below."
    )

    if st.button("Register"):

        st.session_state.page = "Register"

        st.rerun()


# ==========================================================
# Register Page
# ==========================================================

def register_page():

    st.title("Create Account")

    with st.form("register"):

        username = st.text_input("Username")

        email = st.text_input("Email")

        password = st.text_input(
            "Password",
            type="password"
        )

        confirm = st.text_input(
            "Confirm Password",
            type="password"
        )

        role = st.selectbox(
            "Role",
            [
                "patient",
                "staff"
            ]
        )

        submit = st.form_submit_button(
            "Create Account"
        )

    if submit:

        if password != confirm:

            st.error("Passwords do not match.")

            return

        response = api_post(
            "/auth/register",
            {
                "username": username,
                "email": email,
                "password": password,
                "role": role
            }
        )

        if response is None:
            return

        if response.status_code in (200, 201):

            st.success(
                "Registration successful."
            )

            st.session_state.page = "Login"

            st.rerun()

        else:

            st.error(response.text)

    if st.button("Back to Login"):

        st.session_state.page = "Login"

        st.rerun()


# ==========================================================
# Sidebar
# ==========================================================

def sidebar():

    with st.sidebar:

        st.title("🏥 AgentCare")

        user = st.session_state.user

        st.write(
            f"**User:** {user['username']}"
        )

        st.write(
            f"**Role:** {user['role']}"
        )

        page = st.radio(
            "Navigation",
            [
                "Dashboard",
                "Profile",
                "Appointments",
                "Documents",
                "AI Requests",
                "Workflow History",
                "Reminders"
            ]
        )

        if user["role"] == "admin":

            admin_page = st.radio(
                "Administration",
                [
                    "Users",
                    "Audit Logs"
                ]
            )

            if admin_page:
                page = admin_page

        if st.button("Logout"):

            logout()

    st.session_state.page = page


# ==========================================================
# Placeholder Pages
# (Implemented in Response 2 & 3)
# ==========================================================

def dashboard_page():
    st.header("Dashboard Coming Next")


def profile_page():
    st.header("Profile Coming Next")




def documents_page():
    st.header("Documents Coming Next")


def ai_requests_page():
    st.header("AI Requests Coming Next")


def workflow_page():
    st.header("Workflow History Coming Next")


def reminders_page():
    st.header("Reminders Coming Next")


def users_page():
    st.header("Users Coming Next")


def audit_logs_page():
    st.header("Audit Logs Coming Next")


# ==========================================================
# Router
# ==========================================================

def router():

    page = st.session_state.page

    if page == "Dashboard":
        dashboard_page()

    elif page == "Profile":
        profile_page()

    elif page == "Appointments":
        appointments_page()

    elif page == "Documents":
        documents_page()

    elif page == "AI Requests":
        ai_requests_page()

    elif page == "Workflow History":
        workflow_page()

    elif page == "Reminders":
        reminders_page()

    elif page == "Users":
        users_page()

    elif page == "Audit Logs":
        audit_logs_page()


# ==========================================================
# Main
# ==========================================================

def main():

    if st.session_state.token is None:

        if st.session_state.page == "Register":
            register_page()
        else:
            login_page()

        return

    sidebar()

    router()


# ==========================================================
# Dashboard
# ==========================================================

def dashboard_page():
    st.title("🏥 Dashboard")

    response = api_get("/patients/dashboard")

    if response is None:
        st.error("Unable to connect to the server.")
        return

    if response.status_code != 200:
        st.error("Unable to load dashboard.")
        return

    dashboard = response.json()

    stats = dashboard.get("stats", {})

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Appointments",
            stats.get("appointments", 0)
        )

    with col2:
        st.metric(
            "Documents",
            stats.get("documents", 0)
        )

    with col3:
        st.metric(
            "Reminders",
            stats.get("reminders", 0)
        )

    with col4:
        st.metric(
            "Workflows",
            stats.get("workflows", 0)
        )

    st.divider()

    left, right = st.columns([2, 1])

    with left:

        st.subheader("Upcoming Appointments")

        appointments = dashboard.get(
            "appointments",
            []
        )

        if appointments:

            for appt in appointments:

                with st.expander(
                    f"{appt['appointment_date']} - {appt['doctor_name']}"
                ):

                    st.write(
                        f"**Department:** {appt['department']}"
                    )

                    st.write(
                        f"**Doctor:** {appt['doctor_name']}"
                    )

                    st.write(
                        f"**Status:** {appt['status']}"
                    )

                    st.write(
                        f"**Reason:** {appt.get('reason','')}"
                    )

        else:

            st.info(
                "No upcoming appointments."
            )

        st.divider()

        st.subheader("Recent Workflow Activity")

        workflows = dashboard.get(
            "workflows_history",
            []
        )

        if workflows:

            for wf in workflows[:5]:

                st.write(
                    f"• {wf['workflow_type']} "
                    f"({wf['status']})"
                )

        else:

            st.info(
                "No workflow history."
            )

    with right:

        st.subheader("Pending Reminders")

        reminders = dashboard.get(
            "reminders",
            []
        )

        if reminders:

            for reminder in reminders:

                st.warning(
                    reminder["message"]
                )

        else:

            st.success(
                "No pending reminders."
            )

        st.divider()

        st.subheader("Quick Actions")

        if st.button(
            "📅 Book Appointment",
            use_container_width=True
        ):
            st.session_state.page = "Appointments"
            st.rerun()

        if st.button(
            "📄 Upload Document",
            use_container_width=True
        ):
            st.session_state.page = "Documents"
            st.rerun()

        if st.button(
            "🤖 New AI Request",
            use_container_width=True
        ):
            st.session_state.page = "AI Requests"
            st.rerun()

        if st.button(
            "👤 Edit Profile",
            use_container_width=True
        ):
            st.session_state.page = "Profile"
            st.rerun()
# ==========================================================
# Profile Helpers
# ==========================================================

def load_profile():

    response = api_get(
        "/patients/me/profile"
    )

    if response is None:
        return None

    if response.status_code != 200:
        return None

    return response.json()


def update_profile(profile):

    return api_put(
        "/patients/me/profile",
        profile
    )

def profile_summary(profile):

    st.subheader("Patient Information")

    col1, col2 = st.columns(2)

    with col1:

        st.text_input(
            "Name",
            value=profile.get("name", ""),
            disabled=True
        )

        st.text_input(
            "Email",
            value=profile.get("email", ""),
            disabled=True
        )

        st.text_input(
            "Phone",
            value=profile.get("phone", ""),
            disabled=True
        )

        st.text_input(
            "Gender",
            value=profile.get("gender", ""),
            disabled=True
        )

    with col2:

        st.text_input(
            "DOB",
            value=profile.get(
                "date_of_birth",
                ""
            ),
            disabled=True
        )

        st.text_input(
            "Language",
            value=profile.get(
                "preferred_language",
                ""
            ),
            disabled=True
        )

        st.text_input(
            "Emergency Contact",
            value=profile.get(
                "emergency_contact",
                ""
            ),
            disabled=True
        )

        st.text_input(
            "Address",
            value=profile.get(
                "address",
                ""
            ),
            disabled=True
        )
# ==========================================================
# Profile Page
# ==========================================================

def profile_page():

    st.title("👤 My Profile")

    profile = load_profile()

    if profile is None:
        st.error("Unable to load profile.")
        return

    tab1, tab2 = st.tabs([
        "View Profile",
        "Edit Profile"
    ])

    # ------------------------------------------------------
    # View Profile
    # ------------------------------------------------------

    with tab1:

        profile_summary(profile)

    # ------------------------------------------------------
    # Edit Profile
    # ------------------------------------------------------

    with tab2:

        with st.form("edit_profile_form"):

            name = st.text_input(
                "Full Name",
                value=profile.get("name", "")
            )

            email = st.text_input(
                "Email",
                value=profile.get("email", "")
            )

            phone = st.text_input(
                "Phone",
                value=profile.get("phone", "")
            )

            dob = st.text_input(
                "Date of Birth",
                value=profile.get(
                    "date_of_birth",
                    ""
                )
            )

            gender = st.selectbox(
                "Gender",
                [
                    "",
                    "Male",
                    "Female",
                    "Other"
                ],
                index=0 if not profile.get("gender") else
                ["", "Male", "Female", "Other"].index(
                    profile.get("gender")
                )
                if profile.get("gender") in
                ["", "Male", "Female", "Other"]
                else 0
            )

            language = st.text_input(
                "Preferred Language",
                value=profile.get(
                    "preferred_language",
                    ""
                )
            )

            address = st.text_area(
                "Address",
                value=profile.get(
                    "address",
                    ""
                ),
                height=100
            )

            emergency_contact = st.text_input(
                "Emergency Contact",
                value=profile.get(
                    "emergency_contact",
                    ""
                )
            )

            emergency_phone = st.text_input(
                "Emergency Phone",
                value=profile.get(
                    "emergency_phone",
                    ""
                )
            )

            submitted = st.form_submit_button(
                "💾 Save Changes"
            )

        if submitted:

            if not name.strip():

                st.error("Name is required.")

                return

            if not email.strip():

                st.error("Email is required.")

                return

            if not phone.strip():

                st.error("Phone number is required.")

                return

            payload = {

                "name": name,

                "email": email,

                "phone": phone,

                "date_of_birth": dob,

                "gender": gender,

                "preferred_language": language,

                "address": address,

                "emergency_contact": emergency_contact,

                "emergency_phone": emergency_phone

            }

            with st.spinner("Updating profile..."):

                response = update_profile(
                    payload
                )

            if response is None:

                st.error(
                    "Unable to connect to server."
                )

            elif response.status_code == 200:

                st.success(
                    "Profile updated successfully."
                )

                st.rerun()

            else:

                try:
                    detail = response.json()
                    st.error(detail)
                except Exception:
                    st.error(
                        response.text
                    )

    st.divider()

    st.subheader("Account Information")

    col1, col2 = st.columns(2)

    with col1:

        st.info(
            f"""
**Username**

{profile.get("username", "-")}
"""
        )

        st.info(
            f"""
**Role**

{profile.get("role", "-")}
"""
        )

    with col2:

        st.info(
            f"""
**Patient ID**

{profile.get("patient_id", "-")}
"""
        )

        st.info(
            f"""
**Account Status**

{profile.get("status", "Active")}
"""
        )

def appointments_page():
    st.header("Appointments Coming Next")


# ==========================================================
# Appointments Page
# ==========================================================

def load_departments():
    response = api_get("/departments")

    if response is None or response.status_code != 200:
        return []

    return response.json()


def load_doctors(department_id=None):

    endpoint = "/doctors"

    if department_id:
        endpoint += f"?department_id={department_id}"

    response = api_get(endpoint)

    if response is None or response.status_code != 200:
        return []

    return response.json()


def load_appointments():

    response = api_get("/patients/me/appointments")

    if response is None:
        return []

    if response.status_code != 200:
        return []

    return response.json()


def cancel_appointment(appointment_id):

    return api_delete(
        f"/appointments/{appointment_id}"
    )


def create_appointment(data):

    return api_post(
        "/appointments",
        data
    )


# ==========================================================


def appointments_page():

    st.title("📅 Appointments")

    tab1, tab2 = st.tabs(
        [
            "My Appointments",
            "Book Appointment"
        ]
    )

    # ------------------------------------------------------
    # My Appointments
    # ------------------------------------------------------

    with tab1:

        appointments = load_appointments()

        if not appointments:

            st.info("No appointments found.")

        else:

            for appointment in appointments:

                title = (
                    f"{appointment.get('appointment_date','')} - "
                    f"{appointment.get('doctor_name','Unknown Doctor')}"
                )

                with st.expander(title):

                    col1, col2 = st.columns(2)

                    with col1:

                        st.write(
                            f"**Department:** "
                            f"{appointment.get('department','-')}"
                        )

                        st.write(
                            f"**Doctor:** "
                            f"{appointment.get('doctor_name','-')}"
                        )

                        st.write(
                            f"**Status:** "
                            f"{appointment.get('status','-')}"
                        )

                    with col2:

                        st.write(
                            f"**Reason:** "
                            f"{appointment.get('reason','-')}"
                        )

                        st.write(
                            f"**Appointment ID:** "
                            f"{appointment.get('id')}"
                        )

                    if appointment.get("status", "").lower() not in [
                        "completed",
                        "cancelled",
                    ]:

                        if st.button(
                            "Cancel Appointment",
                            key=f"cancel_{appointment['id']}"
                        ):

                            response = cancel_appointment(
                                appointment["id"]
                            )

                            if (
                                response is not None
                                and response.status_code == 200
                            ):

                                st.success(
                                    "Appointment cancelled."
                                )

                                st.rerun()

                            else:

                                st.error(
                                    "Unable to cancel appointment."
                                )

    # ------------------------------------------------------
    # Book Appointment
    # ------------------------------------------------------

    with tab2:

        departments = load_departments()

        if not departments:

            st.warning(
                "No departments available."
            )

            return

        department_names = [
            d["name"]
            for d in departments
        ]

        selected_department = st.selectbox(
            "Department",
            department_names
        )

        department = next(
            d
            for d in departments
            if d["name"] == selected_department
        )

        doctors = load_doctors(
            department["id"]
        )

        if not doctors:

            st.warning(
                "No doctors available."
            )

            return

        doctor_names = [
            doctor["name"]
            for doctor in doctors
        ]

        selected_doctor = st.selectbox(
            "Doctor",
            doctor_names
        )

        doctor = next(
            d
            for d in doctors
            if d["name"] == selected_doctor
        )

        with st.form(
            "appointment_form"
        ):

            appointment_date = st.date_input(
                "Appointment Date"
            )

            appointment_time = st.time_input(
                "Appointment Time"
            )

            reason = st.text_area(
                "Reason for Visit"
            )

            submitted = st.form_submit_button(
                "Book Appointment"
            )

        if submitted:

            payload = {

                "doctor_id": doctor["id"],

                "department_id": department["id"],

                "appointment_date":
                    appointment_date.isoformat(),

                "appointment_time":
                    appointment_time.strftime("%H:%M:%S"),

                "reason": reason

            }

            with st.spinner(
                "Booking appointment..."
            ):

                response = create_appointment(
                    payload
                )

            if response is None:

                st.error(
                    "Unable to connect to server."
                )

            elif response.status_code in (
                200,
                201
            ):

                st.success(
                    "Appointment booked successfully."
                )

                st.rerun()

            else:

                try:

                    st.error(
                        response.json()
                    )

                except Exception:

                    st.error(
                        response.text
                    )

    st.divider()

    if st.button(
        "🔄 Refresh Appointments"
    ):
        st.rerun()

# ==========================================================
# Documents Page
# ==========================================================

def load_documents():

    response = api_get("/documents")

    if response is None:
        return []

    if response.status_code != 200:
        return []

    return response.json()


def upload_document(file, document_type):

    files = {
        "file": (
            file.name,
            file,
            file.type
        )
    }

    data = {
        "document_type": document_type
    }

    try:
        response = requests.post(
            f"{API_URL}/documents/upload",
            headers=auth_headers(),
            files=files,
            data=data,
            timeout=60
        )
        return response

    except Exception as e:

        st.error(e)

        return None


def delete_document(document_id):

    return api_delete(
        f"/documents/{document_id}"
    )


def documents_page():

    st.title("📄 Documents")

    tab1, tab2 = st.tabs(
        [
            "My Documents",
            "Upload"
        ]
    )

    # -------------------------------------------------

    with tab1:

        documents = load_documents()

        if not documents:

            st.info("No uploaded documents.")

        else:

            for document in documents:

                with st.expander(
                    document.get(
                        "filename",
                        "Document"
                    )
                ):

                    st.write(
                        f"Type: {document.get('document_type','-')}"
                    )

                    st.write(
                        f"Uploaded: {document.get('uploaded_at','-')}"
                    )

                    col1, col2 = st.columns(2)

                    with col1:

                        if document.get("download_url"):

                            st.link_button(
                                "Download",
                                document["download_url"]
                            )

                    with col2:

                        if st.button(
                            "Delete",
                            key=f"delete_doc_{document['id']}"
                        ):

                            response = delete_document(
                                document["id"]
                            )

                            if (
                                response is not None
                                and response.status_code == 200
                            ):

                                st.success(
                                    "Document deleted."
                                )

                                st.rerun()

                            else:

                                st.error(
                                    "Unable to delete document."
                                )

    # -------------------------------------------------

    with tab2:

        uploaded_file = st.file_uploader(
            "Choose Document"
        )

        document_type = st.selectbox(

            "Document Type",

            [
                "Prescription",
                "Medical Report",
                "Insurance",
                "Lab Result",
                "Other"
            ]

        )

        if st.button("Upload"):

            if uploaded_file is None:

                st.warning(
                    "Please select a file."
                )

            else:

                with st.spinner(
                    "Uploading..."
                ):

                    response = upload_document(
                        uploaded_file,
                        document_type
                    )

                if response is None:

                    st.error(
                        "Upload failed."
                    )

                elif response.status_code in (
                    200,
                    201
                ):

                    st.success(
                        "Document uploaded."
                    )

                    st.rerun()

                else:

                    st.error(
                        response.text
                    )


# ==========================================================
# AI Requests (CrewAI)
# ==========================================================

def load_workflows():

    response = api_get(
        "/patients/me/workflows"
    )

    if response is None:
        return []

    if response.status_code != 200:
        return []

    return response.json()


def submit_ai_request(data):

    return api_post(
        "/patients/request",
        data
    )


def get_workflow_status(workflow_id):

    response = api_get(
        f"/patients/workflow/{workflow_id}"
    )

    if response is None:
        return None

    if response.status_code != 200:
        return None

    return response.json()


def ai_requests_page():

    st.title("🤖 AI Healthcare Assistant")

    st.write(
        "Submit administrative healthcare requests."
    )

    with st.form(
        "workflow_request"
    ):

        request_type = st.selectbox(

            "Request Type",

            [
                "Appointment",
                "Medical Records",
                "Insurance",
                "Prescription",
                "Referral",
                "Billing",
                "General"
            ]

        )

        priority = st.selectbox(

            "Priority",

            [
                "Low",
                "Normal",
                "High",
                "Urgent"
            ]

        )

        request = st.text_area(

            "Describe your request",

            height=180

        )

        submitted = st.form_submit_button(
            "Submit Request"
        )

    if submitted:

        if request.strip() == "":

            st.warning(
                "Please describe your request."
            )

        else:

            patient_id = st.session_state.user.get("patient_id")
            if patient_id is None:
                st.error("AI requests are available only to patient accounts.")
                return

            payload = {
                "patient_id": patient_id,
                "request": f"[{request_type} | {priority}] {request}",
            }

            with st.spinner(
                "Running AI workflow..."
            ):

                response = submit_ai_request(
                    payload
                )

            if response is None:

                st.error(
                    "Unable to connect."
                )

            elif response.status_code in (
                200,
                201
            ):

                result = response.json()

                workflow_id = result.get("workflow_id")

                if workflow_id is None:

                    st.error(
                        "Workflow submitted, but no workflow_id was returned."
                    )

                else:

                    # Poll GET /patients/workflow/{workflow_id} until the
                    # background crew finishes (status becomes Completed
                    # or Failed), instead of just showing the initial
                    # "Running" response.
                    with st.spinner(
                        "Waiting for AI agents to finish..."
                    ):

                        final_data = None

                        for _ in range(90):  # ~90 * 2s = 3 min max wait

                            status_data = get_workflow_status(workflow_id)

                            if status_data is None:
                                st.error("Lost connection while checking workflow status.")
                                break

                            if status_data["status"] in ("Completed", "Failed"):
                                final_data = status_data
                                break

                            time.sleep(2)

                    if final_data is None:

                        st.warning(
                            f"Workflow ID {workflow_id} is still running. "
                            "Check 'Recent AI Requests' below shortly."
                        )

                    elif final_data["status"] == "Failed":

                        st.error("Workflow failed.")
                        st.write(final_data.get("result"))

                    else:  # Completed

                        result_text = final_data.get("result") or ""
                        lower_text = result_text.lower()

                        # Simple keyword check for appointment booking status
                        if "appointment" in lower_text and (
                            "booked" in lower_text
                            or "confirmed" in lower_text
                            or "scheduled" in lower_text
                        ):
                            st.success("✅ Appointment booked successfully!")
                        elif "appointment" in lower_text and (
                            "not" in lower_text
                            or "unable" in lower_text
                            or "failed" in lower_text
                            or "conflict" in lower_text
                        ):
                            st.error("❌ Appointment could not be booked.")
                        else:
                            st.info(
                                "Workflow completed. See full response below."
                            )

                        st.markdown("### AI Response")
                        st.write(result_text)

            else:

                st.error(
                    response.text
                )

    st.divider()

    st.subheader(
        "Recent AI Requests"
    )

    workflows = load_workflows()

    if not workflows:

        st.info(
            "No workflow history."
        )

    else:

        for workflow in workflows[:10]:

            with st.expander(

                f"{workflow.get('workflow_type','Request')} "

                f"({workflow.get('status','Pending')})"

            ):

                st.write(
                    f"Status: {workflow.get('status')}"
                )

                st.write(
                    f"Department: {workflow.get('department','-')}"
                )

                st.write(
                    f"Priority: {workflow.get('priority','-')}"
                )

                if workflow.get("summary"):

                    st.write(
                        workflow["summary"]
                    )

                if workflow.get("created_at"):

                    st.caption(
                        workflow["created_at"]
                    )


if __name__ == "__main__":
    main()

