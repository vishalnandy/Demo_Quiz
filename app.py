from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pandas as pd
import pytz
import random
import os
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# SQLAlchemy configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'postgresql+psycopg2://postgres.tvlobiffdkivwwpyolwi:Vishal1nand%40@aws-0-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Excel file path
EXCEL_PATH = 'questions.xlsx'

### MODELS ###

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.Text, nullable=False)
    option_b = db.Column(db.Text, nullable=False)
    option_c = db.Column(db.Text, nullable=False)
    option_d = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.Text, nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    #age = db.Column(db.Integer, nullable=False)

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

### HELPERS ###

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def load_questions_to_db():
    if not os.path.exists(EXCEL_PATH):
        raise FileNotFoundError("questions.xlsx not found!")

    df = pd.read_excel(EXCEL_PATH)

    # Drop and recreate only the Question table
    Question.__table__.drop(db.engine)
    Question.__table__.create(db.engine)

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

### ROUTES ###

@app.route('/')
def home():
    return redirect(url_for('register'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip()
        #age = request.form['age']

        if not is_valid_email(email):
            flash("Invalid email format", "error")
            return redirect(url_for('register'))

        user = User.query.filter_by(name=name, email=email).first()
        if user:
            flash("User already registered", "error")
            return redirect(url_for('register'))

        new_user = User(name=name, email=email)
        db.session.add(new_user)
        db.session.commit()

        session['user_name'] = name
        session['user_email'] = email

        return redirect(url_for('index'))

    return render_template('register.html')  # Removed `students=students`

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip()

        user = User.query.filter_by(name=name, email=email).first()
        if user:
            session['user_name'] = name
            session['user_email'] = email
            return redirect(url_for('index'))
        else:
            flash("User not found. Please register.", "error")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/quiz')
def index():
    if 'user_name' not in session:
        return redirect(url_for('login'))
    
    user_name = session['user_name']  # Fetch from session
    return render_template('quiz.html', user_name=user_name)

@app.route('/get-questions')
def get_questions():
    questions = Question.query.all()
    random.shuffle(questions)
    quiz = []
    for q in questions:
        quiz.append({
            "id": q.id,
            "question": q.question,
            "options": [q.option_a, q.option_b, q.option_c, q.option_d],
            "correct": q.correct_answer  # still optional for backend, not sent to frontend
        })
    return jsonify(quiz)

@app.route('/submit', methods=['POST'])
def submit():
    user_answers = request.json.get('answers')
    questions = Question.query.all()
    correct_answer_map = {q.id: q.correct_answer for q in questions}

    score = 0
    for ans in user_answers:
        qid = ans.get('id')
        selected = ans.get('answer')
        if qid in correct_answer_map and selected == correct_answer_map[qid]:
            score += 1

    # Store result
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)

    result = Result(
        user_name=session['user_name'],
        email=session['user_email'],
        score=score,
        timestamp=now_ist
    )
    db.session.add(result)
    db.session.commit()

    return jsonify({"score": score, "total": len(user_answers)})

@app.route('/result')
def result_page():
    score = int(request.args.get('score', 0))
    total = int(request.args.get('total', 0))
    return render_template('result.html', score=score, total=total)

if __name__ == '__main__':
    with app.app_context():
        load_questions_to_db()
    app.run(debug=True)
