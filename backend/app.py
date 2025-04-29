from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import pandas as pd
import os
import pickle
import sqlite3
import hashlib

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
app.secret_key = 'cling-secret-key'

# === Paths
UPLOAD_FILE = os.path.join(os.path.dirname(__file__), 'uploaded.csv')
DB_FILE = os.path.join(os.path.dirname(__file__), 'users.db')
MODEL_FILE = os.path.join(os.path.dirname(__file__), 'model.pkl')

# === Load model
model = pickle.load(open(MODEL_FILE, 'rb'))


# === DB Helpers ===
def get_db():
    return sqlite3.connect(DB_FILE)

def verify_user(username, password):
    conn = get_db()
    cursor = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_pw))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def register_user(username, password):
    conn = get_db()
    cursor = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


# === HTML ROUTES ===
@app.route('/')
def index():
    return render_template('base.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if verify_user(username, password):
            session['user'] = username
            return redirect(url_for('upload'))
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if register_user(username, password):
            return render_template('signup.html', success='Account created! You can now log in.')
        else:
            return render_template('signup.html', error='Username already exists')
    return render_template('signup.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files.get('file')
        if not file or not file.filename.endswith('.csv'):
            return jsonify({'error': 'Please upload a valid CSV file'}), 400
        df = pd.read_csv(file)
        df.to_csv(UPLOAD_FILE, index=False)
        session['uploaded'] = True  # ✅ Set session flag
        return jsonify({'message': 'File uploaded successfully'}), 200

    return render_template('upload.html')


@app.route('/prediction')
def prediction_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    if not session.get('uploaded'):
        return redirect(url_for('upload'))  # ✅ block access
    return render_template('prediction.html')



@app.route('/feedback')
def feedback():
    return render_template('feedback.html')

@app.route('/action_tracker')
def action_tracker():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('action_tracker.html')


# === API ROUTES ===

@app.route('/predict', methods=['GET'])
def predict():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    if not session.get('uploaded'):
        return jsonify({'error': 'No uploaded file found. Please upload one before predicting.'}), 400

    if not os.path.exists(UPLOAD_FILE):
        return jsonify({'error': 'Uploaded file not found on server.'}), 400

    df = pd.read_csv(UPLOAD_FILE)

    if not all(col in df.columns for col in ['id', 'name', 'tenure', 'charges']):
        return jsonify({'error': 'Missing required columns in CSV (id, name, tenure, charges)'}), 400

    X = df[['tenure', 'charges']]
    predictions = model.predict(X)
    probs = model.predict_proba(X)[:, 1]

    # Optional: clear session flag so next prediction requires upload
    session.pop('uploaded', None)

    response = []
    for idx, (pred, prob) in enumerate(zip(predictions, probs)):
        response.append({
            'id': int(df.iloc[idx]['id']),
            'name': df.iloc[idx]['name'],
            'probability': float(prob),
            'label': 'Churn' if pred == 1 else 'No Churn'
        })

    return jsonify(response)



@app.route('/track_action', methods=['POST'])
def track_action():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    customer = data.get('customer')
    action = data.get('action')
    user = session['user']

    if not customer or not action:
        return jsonify({'error': 'Missing fields'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO actions (user, customer, action) VALUES (?, ?, ?)", (user, customer, action))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Action recorded'})


@app.route('/get_actions', methods=['GET'])
def get_actions():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user, customer, action, timestamp FROM actions ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()

    return jsonify([
        {'user': u, 'customer': c, 'action': a, 'timestamp': t}
        for (u, c, a, t) in rows
    ])

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    message = request.form.get('message')
    user = session['user']

    if not message:
        return jsonify({'error': 'Feedback cannot be empty'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO feedback (user, message) VALUES (?, ?)", (user, message))
    conn.commit()
    conn.close()

    return redirect(url_for('feedback'))


@app.route('/get_feedback', methods=['GET'])
def get_feedback():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user, message, timestamp FROM feedback ORDER BY timestamp DESC")
    feedback = cursor.fetchall()
    conn.close()

    return jsonify([
        {'user': u, 'message': m, 'timestamp': t}
        for (u, m, t) in feedback
    ])

@app.route('/api/dashboard_data')
def dashboard_data():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    if not os.path.exists(UPLOAD_FILE):
        return jsonify({'error': 'No uploaded file found.'}), 400

    df = pd.read_csv(UPLOAD_FILE)

    # Filters
    tenure_min = request.args.get('tenure_min', type=int)
    tenure_max = request.args.get('tenure_max', type=int)
    charges_min = request.args.get('charges_min', type=float)
    charges_max = request.args.get('charges_max', type=float)

    if tenure_min is not None:
        df = df[df['tenure'] >= tenure_min]
    if tenure_max is not None:
        df = df[df['tenure'] <= tenure_max]
    if charges_min is not None:
        df = df[df['charges'] >= charges_min]
    if charges_max is not None:
        df = df[df['charges'] <= charges_max]

    if df.empty:
        return jsonify({'error': 'No data matches filter criteria'}), 200

    X = df[['tenure', 'charges']]
    preds = model.predict(X)

    df['prediction'] = preds

    churned = int((preds == 1).sum())
    retained = int((preds == 0).sum())
    total = len(preds)

    # Bar chart: Churn by tenure group
    bins = [0, 12, 24, 36, 48, 60, 100]
    labels = ['0–12', '13–24', '25–36', '37–48', '49–60', '60+']
    df['tenure_group'] = pd.cut(df['tenure'], bins=bins, labels=labels, right=False)
    churn_by_group = df.groupby('tenure_group')['prediction'].sum().reindex(labels, fill_value=0).tolist()

    # Histogram data for charges
    hist_data = pd.cut(df['charges'], bins=10).value_counts().sort_index()
    charges_bins = [str(i) for i in hist_data.index.astype(str)]
    charges_counts = hist_data.tolist()

    # Scatter data
    tenure_charges = df[['tenure', 'charges']].values.tolist()

    return jsonify({
        'total': total,
        'churned': churned,
        'retained': retained,
        'tenure_labels': labels,
        'tenure_churn': churn_by_group,
        'charges_bins': charges_bins,
        'charges_counts': charges_counts,
        'tenure_charges': tenure_charges
    })



@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    if not os.path.exists(UPLOAD_FILE):
        return render_template('dashboard.html', error='No uploaded data found.')

    df = pd.read_csv(UPLOAD_FILE)

    if not all(col in df.columns for col in ['id', 'name', 'tenure', 'charges']):
        return render_template('dashboard.html', error='Invalid CSV format.')

    X = df[['tenure', 'charges']]
    preds = model.predict(X)

    churned = int((preds == 1).sum())
    retained = int((preds == 0).sum())
    total = len(preds)
    churn_rate = round((churned / total) * 100, 2) if total > 0 else 0

    return render_template('dashboard.html',
                           total=total,
                           churned=churned,
                           retained=retained,
                           churn_rate=churn_rate)


if __name__ == '__main__':
    app.run(debug=True)
