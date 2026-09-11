"""
AI & Data Science — Team Portal
A small Streamlit app for a 3-person team to track and compare
each other's projects and coursework/grades.

Data is stored in a local SQLite file (portal.db). Each of the 3 fixed
"slots" can be claimed once by a team member (username + password),
after which they log in normally to edit their own data.
"""

import sqlite3
import hashlib
import hmac
import os
import datetime as dt

import streamlit as st

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------

DB_PATH = os.path.join(os.path.dirname(__file__), "portal.db")
NUM_SLOTS = 3
STATUS_OPTIONS = ["Planned", "In Progress", "Completed", "On Hold"]
STATUS_COLORS = {
    "Planned": "#9aa0a6",
    "In Progress": "#f2a600",
    "Completed": "#2ecc71",
    "On Hold": "#e74c3c",
}

st.set_page_config(page_title="AI & DS Team Portal", page_icon="📊", layout="wide")

# --------------------------------------------------------------------------
# DB helpers
# --------------------------------------------------------------------------

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS members (
            slot_id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password_hash TEXT,
            salt TEXT,
            display_name TEXT,
            bio TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            description TEXT,
            link TEXT,
            updated_at TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_id INTEGER NOT NULL,
            course_name TEXT NOT NULL,
            progress TEXT NOT NULL,
            notes TEXT,
            updated_at TEXT
        )
        """
    )
    conn.commit()

    # Make sure the 3 fixed slots exist (unclaimed to start with)
    for slot in range(1, NUM_SLOTS + 1):
        cur.execute("SELECT 1 FROM members WHERE slot_id = ?", (slot,))
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO members (slot_id, username, password_hash, salt, display_name, bio) "
                "VALUES (?, NULL, NULL, NULL, ?, ?)",
                (slot, f"Member {slot} (unclaimed)", ""),
            )
    conn.commit()
    conn.close()


def hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def now() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M")


# --------------------------------------------------------------------------
# Data access
# --------------------------------------------------------------------------

def get_all_members():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM members ORDER BY slot_id").fetchall()
    conn.close()
    return rows


def get_member(slot_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM members WHERE slot_id = ?", (slot_id,)).fetchone()
    conn.close()
    return row


def claim_slot(slot_id, username, password, display_name):
    salt = os.urandom(8).hex()
    pw_hash = hash_password(password, salt)
    conn = get_conn()
    conn.execute(
        "UPDATE members SET username=?, password_hash=?, salt=?, display_name=?, bio=? WHERE slot_id=?",
        (username, pw_hash, salt, display_name, "", slot_id),
    )
    conn.commit()
    conn.close()


def authenticate(username, password):
    conn = get_conn()
    row = conn.execute("SELECT * FROM members WHERE username = ?", (username,)).fetchone()
    conn.close()
    if row is None or row["password_hash"] is None:
        return None
    candidate = hash_password(password, row["salt"])
    if hmac.compare_digest(candidate, row["password_hash"]):
        return row
    return None


def update_profile(slot_id, display_name, bio):
    conn = get_conn()
    conn.execute(
        "UPDATE members SET display_name=?, bio=? WHERE slot_id=?",
        (display_name, bio, slot_id),
    )
    conn.commit()
    conn.close()


def add_project(slot_id, name, status, description, link):
    conn = get_conn()
    conn.execute(
        "INSERT INTO projects (slot_id, name, status, description, link, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (slot_id, name, status, description, link, now()),
    )
    conn.commit()
    conn.close()


def update_project(project_id, name, status, description, link):
    conn = get_conn()
    conn.execute(
        "UPDATE projects SET name=?, status=?, description=?, link=?, updated_at=? WHERE id=?",
        (name, status, description, link, now(), project_id),
    )
    conn.commit()
    conn.close()


def delete_project(project_id):
    conn = get_conn()
    conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
    conn.commit()
    conn.close()


def get_projects(slot_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM projects WHERE slot_id=? ORDER BY updated_at DESC", (slot_id,)
    ).fetchall()
    conn.close()
    return rows


def add_course(slot_id, course_name, progress, notes):
    conn = get_conn()
    conn.execute(
        "INSERT INTO courses (slot_id, course_name, progress, notes, updated_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (slot_id, course_name, progress, notes, now()),
    )
    conn.commit()
    conn.close()


def update_course(course_id, course_name, progress, notes):
    conn = get_conn()
    conn.execute(
        "UPDATE courses SET course_name=?, progress=?, notes=?, updated_at=? WHERE id=?",
        (course_name, progress, notes, now(), course_id),
    )
    conn.commit()
    conn.close()


def delete_course(course_id):
    conn = get_conn()
    conn.execute("DELETE FROM courses WHERE id=?", (course_id,))
    conn.commit()
    conn.close()


def get_courses(slot_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM courses WHERE slot_id=? ORDER BY updated_at DESC", (slot_id,)
    ).fetchall()
    conn.close()
    return rows


# --------------------------------------------------------------------------
# UI: sidebar (login / logout / claim slot)
# --------------------------------------------------------------------------

def sidebar_auth():
    st.sidebar.title("AI & DS Team Portal")

    if "logged_in_slot" not in st.session_state:
        st.session_state.logged_in_slot = None

    if st.session_state.logged_in_slot:
        member = get_member(st.session_state.logged_in_slot)
        st.sidebar.success(f"Logged in as **{member['display_name']}**")
        if st.sidebar.button("Log out"):
            st.session_state.logged_in_slot = None
            st.rerun()
        return

    tab_login, tab_claim = st.sidebar.tabs(["Log in", "Claim a slot"])

    with tab_login:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Log in"):
            member = authenticate(username, password)
            if member:
                st.session_state.logged_in_slot = member["slot_id"]
                st.rerun()
            else:
                st.error("Incorrect username or password.")

    with tab_claim:
        st.caption("Each of the 3 team slots can be claimed once.")
        unclaimed = [m for m in get_all_members() if m["username"] is None]
        if not unclaimed:
            st.info("All 3 slots have already been claimed.")
        else:
            slot_choice = st.selectbox(
                "Which slot is you?",
                options=[m["slot_id"] for m in unclaimed],
                format_func=lambda s: f"Member {s}",
            )
            new_name = st.text_input("Your display name", key="claim_name")
            new_user = st.text_input("Choose a username", key="claim_user")
            new_pass = st.text_input("Choose a password", type="password", key="claim_pass")
            if st.button("Claim this slot"):
                if not (new_name and new_user and new_pass):
                    st.error("Please fill in all fields.")
                elif any(m["username"] == new_user for m in get_all_members()):
                    st.error("That username is already taken.")
                else:
                    claim_slot(slot_choice, new_user, new_pass, new_name)
                    st.success("Slot claimed! Switch to the Log in tab.")


# --------------------------------------------------------------------------
# UI: dashboard (everyone can view, no login needed)
# --------------------------------------------------------------------------

def status_badge(status):
    color = STATUS_COLORS.get(status, "#9aa0a6")
    return f'<span style="background:{color};color:white;padding:2px 8px;border-radius:10px;font-size:0.8em;">{status}</span>'


def render_member_card(member):
    st.subheader(member["display_name"])
    if member["bio"]:
        st.caption(member["bio"])

    projects = get_projects(member["slot_id"])
    st.markdown("**Projects**")
    if not projects:
        st.write("_No projects added yet._")
    else:
        for p in projects:
            st.markdown(
                f"- **{p['name']}** {status_badge(p['status'])}",
                unsafe_allow_html=True,
            )
            if p["description"]:
                st.caption(p["description"])
            if p["link"]:
                st.markdown(f"  [link]({p['link']})")

    courses = get_courses(member["slot_id"])
    st.markdown("**Coursework / Grades**")
    if not courses:
        st.write("_No coursework added yet._")
    else:
        for c in courses:
            st.markdown(f"- **{c['course_name']}** — {c['progress']}")
            if c["notes"]:
                st.caption(c["notes"])


def render_dashboard():
    st.header("Team Dashboard")
    st.caption("Live comparison of projects and coursework across the team.")
    members = get_all_members()
    cols = st.columns(len(members))
    for col, member in zip(cols, members):
        with col:
            with st.container(border=True):
                render_member_card(member)


# --------------------------------------------------------------------------
# UI: my profile (login required)
# --------------------------------------------------------------------------

def render_my_profile():
    slot_id = st.session_state.logged_in_slot
    member = get_member(slot_id)

    st.header(f"My Profile — {member['display_name']}")

    with st.expander("Edit display name / bio"):
        new_name = st.text_input("Display name", value=member["display_name"])
        new_bio = st.text_area("Short bio", value=member["bio"] or "")
        if st.button("Save profile info"):
            update_profile(slot_id, new_name, new_bio)
            st.success("Profile updated.")
            st.rerun()

    st.divider()
    st.subheader("My Projects")
    with st.form("add_project_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("Project name")
        status = c2.selectbox("Status", STATUS_OPTIONS)
        description = st.text_area("Description")
        link = st.text_input("Link (GitHub, demo, etc.) — optional")
        submitted = st.form_submit_button("Add project")
        if submitted:
            if name:
                add_project(slot_id, name, status, description, link)
                st.success("Project added.")
                st.rerun()
            else:
                st.error("Project name is required.")

    for p in get_projects(slot_id):
        with st.expander(f"{p['name']} ({p['status']})"):
            ec1, ec2 = st.columns(2)
            e_name = ec1.text_input("Name", value=p["name"], key=f"pname_{p['id']}")
            e_status = ec2.selectbox(
                "Status", STATUS_OPTIONS, index=STATUS_OPTIONS.index(p["status"]), key=f"pstatus_{p['id']}"
            )
            e_desc = st.text_area("Description", value=p["description"] or "", key=f"pdesc_{p['id']}")
            e_link = st.text_input("Link", value=p["link"] or "", key=f"plink_{p['id']}")
            bcol1, bcol2 = st.columns(2)
            if bcol1.button("Save", key=f"psave_{p['id']}"):
                update_project(p["id"], e_name, e_status, e_desc, e_link)
                st.success("Saved.")
                st.rerun()
            if bcol2.button("Delete", key=f"pdel_{p['id']}"):
                delete_project(p["id"])
                st.rerun()

    st.divider()
    st.subheader("My Coursework / Grades")
    with st.form("add_course_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        course_name = c1.text_input("Course / module name")
        progress = c2.text_input("Grade or progress (e.g. 'A', '85%', '70% complete')")
        notes = st.text_area("Notes — optional")
        submitted = st.form_submit_button("Add coursework")
        if submitted:
            if course_name and progress:
                add_course(slot_id, course_name, progress, notes)
                st.success("Coursework added.")
                st.rerun()
            else:
                st.error("Course name and grade/progress are required.")

    for c in get_courses(slot_id):
        with st.expander(f"{c['course_name']} — {c['progress']}"):
            ec1, ec2 = st.columns(2)
            e_course = ec1.text_input("Course name", value=c["course_name"], key=f"cname_{c['id']}")
            e_progress = ec2.text_input("Grade / progress", value=c["progress"], key=f"cprog_{c['id']}")
            e_notes = st.text_area("Notes", value=c["notes"] or "", key=f"cnotes_{c['id']}")
            bcol1, bcol2 = st.columns(2)
            if bcol1.button("Save", key=f"csave_{c['id']}"):
                update_course(c["id"], e_course, e_progress, e_notes)
                st.success("Saved.")
                st.rerun()
            if bcol2.button("Delete", key=f"cdel_{c['id']}"):
                delete_course(c["id"])
                st.rerun()


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    init_db()
    sidebar_auth()

    if st.session_state.get("logged_in_slot"):
        tab1, tab2 = st.tabs(["Team Dashboard", "My Profile"])
        with tab1:
            render_dashboard()
        with tab2:
            render_my_profile()
    else:
        render_dashboard()
        st.info("Log in from the sidebar to edit your own projects and coursework.")


if __name__ == "__main__":
    main()
