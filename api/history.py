import sys
from pathlib import Path
from flask import Flask, jsonify, request

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from core.database import get_recent_predictions

app = Flask(__name__)

@app.route('/api/history', methods=['GET', 'OPTIONS'])
@app.route('/', methods=['GET', 'OPTIONS'])
def history():
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'X-User-Id'
        return response

    try:
        user_id = request.headers.get("X-User-Id", None)
        limit = int(request.args.get("limit", 10))
        
        predictions = get_recent_predictions(user_id=user_id, limit=limit)
        
        response = jsonify({"history": predictions})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        response = jsonify({"error": str(e)})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500

def handler(request, response):
    return app(request, response)
