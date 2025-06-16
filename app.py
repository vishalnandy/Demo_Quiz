from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pandas as pd
import pytz
import random
import os
import re

# NLTK imports for paraphrasing
import nltk
# nltk.download('wordnet')
# nltk.download('punkt')
# nltk.download('averaged_perceptron_tagger')
# nltk.download('omw-1.4')
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize
from nltk import pos_tag

app = Flask(__name__)
app.secret_key = 'your_secret_key'

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'postgresql+psycopg2://postgres.tvlobiffdkivwwpyolwi:Vishal1nand%40@aws-0-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# POS tag mapping from nltk -> wordnet
def get_wordnet_pos(treebank_tag):
    if treebank_tag.startswith('J'):
        return wordnet.ADJ
    elif treebank_tag.startswith('V'):
        return wordnet.VERB
    elif treebank_tag.startswith('N'):
        return wordnet.NOUN
    elif treebank_tag.startswith('R'):
        return wordnet.ADV
    else:
        return None

def paraphrase_sentence(sentence):
    tokens = word_tokenize(sentence)
    tagged = pos_tag(tokens)
    new_words = []
    for word, tag in tagged:
        wn_tag = get_wordnet_pos(tag)
        if wn_tag:
            synsets = wordnet.synsets(word, pos=wn_tag)
            if synsets:
                lemmas = synsets[0].lemma_names()
                synonym = lemmas[0].replace('_', ' ')
                if synonym.lower() != word.lower():
                    new_words.append(synonym)
                    continue
        new_words.append(word)
    return ' '.join(new_words)

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

    return render_template('register.html')

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
    
    user_name = session['user_name']
    return render_template('quiz.html', user_name=user_name)

@app.route('/get-questions')
def get_questions():
    questions = Question.query.all()
    random.shuffle(questions)
    quiz = []
    for q in questions:
        paraphrased = paraphrase_sentence(q.question)
        quiz.append({
            "id": q.id,
            "question": paraphrased,
            "options": [q.option_a, q.option_b, q.option_c, q.option_d],
            "correct": q.correct_answer  # not used on frontend
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
        submitted_answer = ans.get('answer', '').strip()

        if qid in correct_answer_map:
            correct_answer = correct_answer_map[qid].strip()

            submitted_set = set(filter(None, map(str.strip, submitted_answer.split(','))))
            correct_set = set(filter(None, map(str.strip, correct_answer.split(','))))

            print(f"Question ID {qid}")
            print(f"Submitted: {submitted_set}")
            print(f"Correct:   {correct_set}")

            if submitted_set == correct_set:
                score += 1

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

    print(f"Q{id} → submitted: {submitted_set} | correct: {correct_set}")

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
