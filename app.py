from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import random
import os

app = Flask(__name__)

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'postgresql+psycopg2://postgres.tvlobiffdkivwwpyolwi:Vishal1nand%40@aws-0-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Excel file path
EXCEL_PATH = 'questions.xlsx'

# Define Question model
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.Text, nullable=False)
    option_b = db.Column(db.Text, nullable=False)
    option_c = db.Column(db.Text, nullable=False)
    option_d = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.Text, nullable=False)

# Load questions from Excel into DB
def load_questions_to_db():
    if not os.path.exists(EXCEL_PATH):
        raise FileNotFoundError("questions.xlsx not found!")

    df = pd.read_excel(EXCEL_PATH)
    
    # Drop and recreate table
    db.drop_all()
    db.create_all()

    for _, row in df.iterrows():
        q = Question(
            question=row['question'],
            option_a=row['Option A'],
            option_b=row['Option B'],
            option_c=row['Option C'],
            option_d=row['Option D'],
            correct_answer=row['Correct Answer']
        )
        db.session.add(q)

    db.session.commit()

@app.route('/')
def index():
    return render_template('quiz.html')

@app.route('/get-questions')
def get_questions():
    questions = Question.query.all()
    random.shuffle(questions)
    quiz = []
    for idx, q in enumerate(questions):
        quiz.append({
            "id": idx + 1,
            "question": q.question,
            "options": [q.option_a, q.option_b, q.option_c, q.option_d],
            "correct": q.correct_answer  # internal use only, not sent to frontend
        })
    return jsonify(quiz)

@app.route('/submit', methods=['POST'])
def submit():
    user_answers = request.json.get('answers')
    questions = Question.query.all()
    correct_answers = [q.correct_answer for q in questions]

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
    with app.app_context():
        load_questions_to_db()
    app.run(debug=True)
