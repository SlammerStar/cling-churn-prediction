import sys
from pathlib import Path
from flask import Flask, jsonify, request

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from ml.predictor import load_artifacts

app = Flask(__name__)

@app.route('/api/health', methods=['GET', 'OPTIONS'])
@app.route('/', methods=['GET', 'OPTIONS'])
def health():
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        return response

    try:
        load_artifacts()
        response = jsonify({"status": "ok", "model_loaded": True})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        response = jsonify({"status": "degraded", "error": str(e)})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 503

def handler(request, response):
    return app(request, response)
