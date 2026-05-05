import sys
from pathlib import Path
from flask import Flask, jsonify, request

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from ml.predictor import get_model_stats

app = Flask(__name__)

@app.route('/api/stats', methods=['GET', 'OPTIONS'])
@app.route('/', methods=['GET', 'OPTIONS'])
def stats():
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        return response

    try:
        data = get_model_stats()
        if not data:
            response = jsonify({"error": "Model stats not available"})
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response, 503
        
        response = jsonify(data)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        response = jsonify({"error": str(e)})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500

def handler(request, response):
    return app(request, response)
