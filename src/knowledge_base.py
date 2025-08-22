import sqlite3

def create_knowledge_tables(conn):
    """
    Create the new tables for the autonomous learning system.
    """
    try:
        c = conn.cursor()

        # Table for different areas of knowledge
        c.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_areas (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE
            )
        """)

        # Table for different learning techniques
        c.execute("""
            CREATE TABLE IF NOT EXISTS learning_techniques (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE
            )
        """)

        # Table to track the application of techniques to concepts
        c.execute("""
            CREATE TABLE IF NOT EXISTS concept_learning_progress (
                id INTEGER PRIMARY KEY,
                concept_id INTEGER NOT NULL,
                technique_id INTEGER NOT NULL,
                applications_count INTEGER NOT NULL DEFAULT 0,
                last_applied_timestamp TEXT,
                FOREIGN KEY (concept_id) REFERENCES concepts (id),
                FOREIGN KEY (technique_id) REFERENCES learning_techniques (id)
            )
        """)

        # Pre-populate with some default techniques
        default_techniques = [('Recall',), ('Elaboration',), ('Visualization',)]
        c.executemany("INSERT OR IGNORE INTO learning_techniques (name) VALUES (?)", default_techniques)

        conn.commit()
    except sqlite3.Error as e:
        print(f"Error creating knowledge tables: {e}")


def allocate_technique(conn, concept_id):
    """
    Analyzes the learning history of a concept and selects an appropriate technique.

    :param conn: Connection object
    :param concept_id: The ID of the concept to analyze
    :return: The name of the allocated technique
    """
    cur = conn.cursor()

    # Get the recall history for this concept
    cur.execute("""
        SELECT ai_grade
        FROM recall_sessions
        WHERE concept_id = ?
        ORDER BY timestamp DESC
    """, (concept_id,))

    grades = cur.fetchall()

    # Simple rule: if failed more than twice (grade <= 2), use "Elaboration"
    # FSRS grades: 1:Again, 2:Hard, 3:Good, 4:Easy. We'll consider < 3 a failure for this logic.
    failure_count = sum(1 for grade in grades if grade[0] < 3)

    if failure_count > 2:
        return "Elaboration"
    else:
        return "Recall"


def get_technique_id_by_name(conn, name):
    """
    Get the ID of a learning technique by its name.
    """
    cur = conn.cursor()
    cur.execute("SELECT id FROM learning_techniques WHERE name = ?", (name,))
    result = cur.fetchone()
    return result[0] if result else None

def update_concept_learning_progress(conn, concept_id, technique_id):
    """
    Update the progress for a given concept and technique.
    """
    import datetime
    cur = conn.cursor()

    timestamp = datetime.datetime.now().isoformat()

    cur.execute("""
        SELECT id, applications_count FROM concept_learning_progress
        WHERE concept_id = ? AND technique_id = ?
    """, (concept_id, technique_id))

    result = cur.fetchone()

    if result:
        # Update existing record
        progress_id, count = result
        cur.execute("""
            UPDATE concept_learning_progress
            SET applications_count = ?, last_applied_timestamp = ?
            WHERE id = ?
        """, (count + 1, timestamp, progress_id))
    else:
        # Insert new record
        cur.execute("""
            INSERT INTO concept_learning_progress (concept_id, technique_id, applications_count, last_applied_timestamp)
            VALUES (?, ?, 1, ?)
        """, (concept_id, technique_id, timestamp))

    conn.commit()
