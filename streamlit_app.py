import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os

# Neon DB credentials
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Database connection
def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        sslmode="require",
        cursor_factory=RealDictCursor
    )

# Create table if not exists
def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id SERIAL PRIMARY KEY,
            project_name TEXT NOT NULL,
            description TEXT NOT NULL,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

# Insert new project
def add_project(name, desc):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO projects (project_name, description) 
        VALUES (%s, %s)
    """, (name, desc))
    conn.commit()
    cur.close()
    conn.close()

# Update project
def update_project(project_id, name, desc):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE projects 
        SET project_name = %s, description = %s 
        WHERE id = %s
    """, (name, desc, project_id))
    conn.commit()
    cur.close()
    conn.close()

# Delete project
def delete_project(project_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM projects WHERE id = %s", (project_id,))
    conn.commit()
    cur.close()
    conn.close()

# Fetch projects (with optional search keyword)
def get_projects(keyword=None):
    conn = get_connection()
    cur = conn.cursor()
    if keyword:
        search_term = f"%{keyword}%"
        cur.execute("""
            SELECT * FROM projects
            WHERE project_name ILIKE %s OR description ILIKE %s
            ORDER BY date_added DESC
        """, (search_term, search_term))
    else:
        cur.execute("SELECT * FROM projects ORDER BY date_added DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

# Copy to clipboard
def copy_to_clipboard(text):
    js_code = f"""
    <script>
        navigator.clipboard.writeText(`{text}`).then(() => {{
            alert("Copied to clipboard!");
        }});
    </script>
    """
    st.markdown(js_code, unsafe_allow_html=True)

# Main UI
st.set_page_config(page_title="Project Manager", page_icon="📂", layout="wide")
st.title("📂 My Project Manager")

# Initialize DB
init_db()

menu = st.sidebar.radio("Navigation", ["➕ Add New Project", "📋 Dashboard"])

if menu == "➕ Add New Project":
    st.subheader("Add a New Project")
    with st.form("add_project_form"):
        name = st.text_input("Project Name")
        desc = st.text_area("Project Description (can include live links, tech stack, etc.)", height=200)
        submitted = st.form_submit_button("Save Project")
        if submitted:
            if name.strip() and desc.strip():
                add_project(name, desc)
                st.success(f"✅ Project '{name}' added successfully!")
            else:
                st.warning("⚠️ Please fill in all fields.")

elif menu == "📋 Dashboard":
    st.subheader("Projects Dashboard")
    keyword = st.text_input("🔍 Search by keyword", placeholder="Enter keyword (e.g., Python, chatbot, API)")
    projects = get_projects(keyword) if keyword else get_projects()

    if projects:
        for p in projects:
            with st.expander(f"📌 {p['project_name']}"):
                st.markdown(p['description'], unsafe_allow_html=True)
                st.markdown(f"*Added on: {p['date_added'].strftime('%Y-%m-%d')}*")

                col1, col2, col3, col4 = st.columns([1, 1, 1, 4])
                with col1:
                    if st.button("📋 Copy", key=f"copy_{p['id']}"):
                        copy_to_clipboard(p['description'])
                with col2:
                    if st.button("✏️ Edit", key=f"edit_{p['id']}"):
                        with st.form(f"edit_form_{p['id']}"):
                            new_name = st.text_input("Project Name", value=p['project_name'])
                            new_desc = st.text_area("Description", value=p['description'], height=200)
                            if st.form_submit_button("Update"):
                                update_project(p['id'], new_name, new_desc)
                                st.success("✅ Project updated successfully!")
                                st.experimental_rerun()
                with col3:
                    if st.button("🗑 Delete", key=f"delete_{p['id']}"):
                        delete_project(p['id'])
                        st.warning("🗑 Project deleted!")
                        st.experimental_rerun()
                st.markdown("---")
    else:
        st.info("No projects found. Try a different keyword or add a new one.")
