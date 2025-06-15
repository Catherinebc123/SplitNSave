from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import json
import random

app = Flask(__name__)
app.secret_key = "your_secret_key"

# MySQL config - update accordingly
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Cheruv@ll1l",
    database="money"
)
cursor = db.cursor(dictionary=True)

# Helper function to generate boxes
def generate_boxes(goal_amount, num_boxes=10):
    if num_boxes >= goal_amount:
        boxes = [1] * goal_amount + [0] * (num_boxes - goal_amount)
        random.shuffle(boxes)
        return boxes

    cuts = sorted(random.sample(range(50, goal_amount), num_boxes - 1))
    boxes = [cuts[0]] + [cuts[i] - cuts[i - 1] for i in range(1, len(cuts))] + [goal_amount - cuts[-1]]
    random.shuffle(boxes)
    return boxes

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('money'))
    return render_template('simply.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cursor.fetchone()
        if existing_user:
            flash('Username already exists, please choose a different one.', 'error')
            return render_template('signin.html')

        hashed_password = generate_password_hash(password)
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
        db.commit()

        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('signin.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['username'] = username
            session['user_id'] = user['id']
            return redirect(url_for('money'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/money')
def money():
    if 'username' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor.execute("SELECT * FROM savings_history WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
    goals = cursor.fetchall()

    for goal in goals:
        try:
            goal['boxes'] = json.loads(goal['boxes']) if goal['boxes'] else []
        except Exception:
            goal['boxes'] = []
        try:
            goal['clicked_indexes'] = json.loads(goal['clicked_indexes']) if goal['clicked_indexes'] else []
        except Exception:
            goal['clicked_indexes'] = []

    return render_template("money.html", goals=goals)

@app.route('/create_goal', methods=['POST'])
def create_goal():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json(force=True)
    goal_amount = data.get('goal_amount')
    goal_description = data.get('goal_description', '').strip()

    if not isinstance(goal_amount, int) or goal_amount <= 0:
        return jsonify({'error': 'Invalid goal amount'}), 400
    if not goal_description:
        return jsonify({'error': 'Goal description required'}), 400

    boxes = generate_boxes(goal_amount)
    remaining = goal_amount
    clicked_indexes = []
    user_id = session['user_id']

    cursor.execute("""
        INSERT INTO savings_history (user_id, goal_amount, goal_description, boxes, clicked_indexes, remaining)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        user_id,
        goal_amount,
        goal_description,
        json.dumps(boxes),
        json.dumps(clicked_indexes),
        remaining
    ))
    db.commit()

    return jsonify({'status': 'goal_created'})

@app.route('/update_progress/<int:goal_id>', methods=['POST'])
def update_progress(goal_id):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json(force=True)
    clicked_indexes = data.get('clicked_indexes')
    remaining_amount = data.get('remaining_amount')

    if not isinstance(clicked_indexes, list):
        return jsonify({'error': 'Invalid clicked indexes'}), 400
    if not isinstance(remaining_amount, (int, float)):
        return jsonify({'error': 'Invalid remaining amount'}), 400

    user_id = session['user_id']

    cursor.execute("SELECT * FROM savings_history WHERE id = %s AND user_id = %s", (goal_id, user_id))
    goal = cursor.fetchone()
    if not goal:
        return jsonify({'error': 'Goal not found or unauthorized'}), 404

    try:
        cursor.execute("""
            UPDATE savings_history
            SET clicked_indexes = %s, remaining = %s
            WHERE id = %s
        """, (
            json.dumps(clicked_indexes),
            remaining_amount,
            goal_id
        ))
        db.commit()
    except Exception as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

    return jsonify({'status': 'progress_updated'})

# New routes for split.html and es.html
@app.route('/split')
def split():
    return render_template('split.html')

@app.route('/es')
def es():
    return render_template('es.html')

@app.route('/index')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
