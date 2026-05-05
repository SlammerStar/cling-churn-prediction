from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pathlib import Path

# Import all API handlers
from api.predict import predict as handle_predict
from api.predict_batch import batch_predict as handle_batch_predict
from api.stats import stats as handle_stats
from api.health import health as handle_health
from api.history import history as handle_history
from api.sample import sample as handle_sample

app = Flask(__name__, static_folder="public")
CORS(app)

# Register routes to call the respective handlers
# We just map them here. Since they were designed as isolated Flask apps, 
# their decorators were @app.route. In this monolithic app, we define them manually.

@app.route('/api/predict', methods=['POST', 'OPTIONS'])
def local_predict(): return handle_predict()

@app.route('/api/predict/batch', methods=['POST', 'OPTIONS'])
def local_batch(): return handle_batch_predict()

@app.route('/api/stats', methods=['GET', 'OPTIONS'])
def local_stats(): return handle_stats()

@app.route('/api/health', methods=['GET', 'OPTIONS'])
def local_health(): return handle_health()

@app.route('/api/history', methods=['GET', 'OPTIONS'])
def local_history(): return handle_history()

@app.route('/api/sample', methods=['GET', 'OPTIONS'])
def local_sample(): return handle_sample()

# Serve static files for frontend
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    public_dir = Path(__file__).parent / "public"
    if path and (public_dir / path).exists():
        return send_from_directory(public_dir, path)
    return send_from_directory(public_dir, "index.html")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
