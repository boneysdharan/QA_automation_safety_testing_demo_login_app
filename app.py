import streamlit as st
import requests

BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Login Demo", layout="centered")

# Session state
if "login_message" not in st.session_state:
    st.session_state.login_message = ""
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["Login", "Dashboard", "Content Moderation"], 
                        index=["Login", "Dashboard", "Content Moderation"].index(
                            st.session_state.get("page", "Login")
                        ))

# LOGIN PAGE
if page == "Login":
    if not st.session_state.logged_in:
        st.title("🔐 Login Page")

        with st.form("login_form"):
            username = st.text_input("Username", key="username", label_visibility="visible")
            password = st.text_input("Password", type="password", key="password", label_visibility="visible")
            submitted = st.form_submit_button("Login")

            if submitted:
                if not username:
                    st.session_state.login_message = "Username is required"
                elif not password:
                    st.session_state.login_message = "Password is required"
                elif username == "admin" and password == "password123":
                    st.session_state.logged_in = True
                    st.session_state.login_message = f"Welcome, {username}"
                    st.session_state["page"] = "Dashboard"
                    st.rerun()
                else:
                    st.session_state.login_message = "Invalid credentials"

        # Element for Playwright to read login result
        st.markdown(
            f"<div id='login-result'>{st.session_state.login_message}</div>",
            unsafe_allow_html=True
        )

    else:
        st.success(st.session_state.login_message)
        st.sidebar.success("✅ You are logged in!")

# DASHBOARD
elif page == "Dashboard":
    if st.session_state.logged_in:
        st.title("📊 Dashboard Overview")

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.login_message = ""
            st.rerun()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Active Users", "1,245", "+58 today")
        with col2:
            st.metric("Revenue", "$12.4K", "↑ 12%")
        with col3:
            st.metric("Server Status", "✅ Online")

        st.divider()
        st.write("### Recent Activity")
        st.table({
            "User": ["alice", "bob", "charlie"],
            "Action": ["Login", "Upload File", "Logout"],
            "Time": ["10:21 AM", "11:05 AM", "11:47 AM"]
        })

        st.divider()
        st.write("### Performance Chart")
        st.line_chart({
            "Month": ["Jan", "Feb", "Mar", "Apr", "May"],
            "Sales": [120, 150, 180, 90, 200],
        })
    else:
        st.warning("⚠️ Please log in first!")

# CONTENT MODERATION
elif page == "Content Moderation":
    st.title("🛡️ Content Moderation with Detoxify")

    user_input = st.text_area("Enter text to check for toxicity:")
    if st.button("Moderate Text"):
        if user_input.strip():
            try:
                response = requests.post(f"{BACKEND_URL}/api/moderate", json={"text": user_input})
                if response.status_code == 200:
                    result = response.json()
                    if result.get("toxicity") == "toxic":
                        st.error("🚨 This text is **Toxic**!")
                    else:
                        st.success("✅ This text is **Safe**.")
                    st.json(result)
                else:
                    st.error(f"Server error: {response.status_code}")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("Please enter some text before moderating.")