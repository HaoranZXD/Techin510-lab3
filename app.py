import sqlite3
from datetime import datetime
from enum import Enum

import streamlit as st
from pydantic import BaseModel
import streamlit_pydantic as sp

# Enum for task state and category
class State(str, Enum):
    PLANNED = "Planned"
    IN_PROGRESS = "In-progress"
    DONE = "Done"

class Category(str, Enum):
    SCHOOL = "School"
    WORK = "Work"
    PERSONAL = "Personal"

# Task model
class Task(BaseModel):
    name: str
    description: str
    state: State = State.PLANNED    
    category: Category

# Connect to SQLite database
con = sqlite3.connect("todoapp.sqlite", isolation_level=None, check_same_thread=False)
cur = con.cursor()

# Create the table
cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY,
        name TEXT,
        description TEXT,
        state TEXT,
        created_at TEXT,
        created_by TEXT,
        category TEXT
    )
""")

# Function to insert a new task
def insert_task(task_data):
    cur.execute("""
        INSERT INTO tasks (name, description, state, created_at, created_by, category) VALUES (?, ?, ?, ?, ?, ?)
    """, (task_data.name, task_data.description, task_data.state, datetime.now(), "default_user", task_data.category))

# Function to update the state of a task
def update_task_state(task_id, new_state):
    cur.execute("UPDATE tasks SET state = ? WHERE id = ?", (new_state, task_id))

# Function to delete a task
def delete_task(task_id):
    cur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    
# Streamlit app
def main():
    st.title("Todo App")

    # Task submission form
    task_data = sp.pydantic_form(key="task_form", model=Task)
    if task_data:
        insert_task(task_data)

    # Search and filter functionality
    search_query = st.text_input("Search")
    filter_category = st.selectbox("Filter by Category", options=["", "School", "Work", "Personal"])

    # Display tasks
    query = "SELECT * FROM tasks"
    conditions = []
    if search_query:
        conditions.append(f"(name LIKE '%{search_query}%' OR description LIKE '%{search_query}%')")
    if filter_category:
        conditions.append(f"category = '{filter_category}'")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    tasks = cur.execute(query).fetchall()
    for task in tasks:
        with st.expander(f"{task[1]} (ID: {task[0]})"):
            st.write(f"Description: {task[2]}")
            st.write(f"State: {task[3]}")
            st.write(f"Created At: {task[4]}")
            st.write(f"Created By: {task[5]}")
            st.write(f"Category: {task[6]}")

            # Update state
            # Update state with immediate effect
            current_state = task[3]
            new_state = st.selectbox(
                "Change State", 
                options=list(State), 
                index=list(State).index(current_state), 
                key=f"state_{task[0]}"
            )

            # Detect state change and update database
            if new_state != current_state:
                update_task_state(task[0], new_state)
                current_state = new_state  # Update current state to reflect the change

            # Delete task
            if st.button("Delete", key=f"delete_{task[0]}"):
                delete_task(task[0])
                st.experimental_rerun()

if __name__ == "__main__":
    main()
