import sqlite3

# Create or connect to a database
conn = sqlite3.connect('quiz.db')

# Create a table
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        option_a TEXT,
        option_b TEXT,
        option_c TEXT,
        option_d TEXT,
        correct_answer TEXT
    )
''')

conn.commit()
conn.close()
print("Database and table created successfully.")