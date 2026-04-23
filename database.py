import sqlite3

DB_NAME = "study_assistant.db"


def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            branch TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            branch TEXT NOT NULL,
            topic TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def save_student(name, branch):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO students (name, branch) VALUES (?, ?)",
        (name, branch)
    )

    conn.commit()
    conn.close()


def save_score(student_name, branch, topic, score, total):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO quiz_scores (student_name, branch, topic, score, total)
        VALUES (?, ?, ?, ?, ?)
        """,
        (student_name, branch, topic, score, total)
    )

    conn.commit()
    conn.close()


def get_leaderboard():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT student_name, branch, topic, score, total
        FROM quiz_scores
        ORDER BY score DESC, total DESC
    """)

    data = cursor.fetchall()
    conn.close()
    return data