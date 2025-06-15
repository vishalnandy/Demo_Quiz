from flask import Flask, request, jsonify, render_template, redirect, url_for
import pandas as pd
import random
import psycopg2
import os

app = Flask(__name__)

DATABASE_URL = 'postgresql+psycopg2://postgres.tvlobiffdkivwwpyolwi:Vishal1nand%40@aws-0-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require'  # Set this in your environment variables (for Render)
EXCEL_PATH = 'questions.xlsx'

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

def load_questions_to_db():
    if not os.path.exists(EXCEL_PATH):
        raise FileNotFoundError("questions.xlsx not found!")

    df = pd.read_excel(EXCEL_PATH)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS questions")
    cursor.execute('''CREATE TABLE questions (
                        question TEXT,
                        "Option A" TEXT,
                        "Option B" TEXT,
                        "Option C" TEXT,
                        "Option D" TEXT,
                        "Correct Answer" TEXT)''')
    for _, row in df.iterrows():
        cursor.execute("INSERT INTO questions VALUES (%s, %s, %s, %s, %s, %s)", tuple(row))
    conn.commit()
    cursor.close()
    conn.close()

@app.route('/')
def index():
    return render_template('quiz.html')

@app.route('/get-questions')
def get_questions():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions")
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    random.shuffle(data)
    quiz = []
    for idx, q in enumerate(data):
        quiz.append({
            "id": idx + 1,
            "question": q[0],
            "options": [q[1], q[2], q[3], q[4]],
            "correct": q[5]  # internal use only, not sent to frontend
        })
    return jsonify(quiz)

@app.route('/submit', methods=['POST'])
def submit():
    user_answers = request.json.get('answers')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions")
    rows = cursor.fetchall()
    correct_answers = [r[5] for r in rows]
    cursor.close()
    conn.close()

    score = 0
    for idx, ans in enumerate(user_answers):
        if idx < len(correct_answers) and ans['answer'] == correct_answers[idx]:
            score += 1
    return jsonify({"score": score, "total": len(user_answers)})

@app.route('/result')
def result_page():
    score = request.args.get('score', 0)
    total = request.args.get('total', 0)
    return render_template('result.html', score=score, total=total)

if __name__ == '__main__':
    load_questions_to_db()
    app.run(debug=True)