import sys
import traceback
from pathlib import Path
from flask import Flask, request, jsonify

# Add project root to path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from ml.predictor import predict_single
from core.database import log_prediction

app = Flask(__name__)

@app.route('/api/predict', methods=['POST', 'OPTIONS'])
@app.route('/', methods=['POST', 'OPTIONS'])
def predict():
    if request.method == 'OPTIONS':
        # CORS preflight
        response = app.make_default_options_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    try:
        data = request.get_json(force=True)
        if not data:
            response = jsonify({"error": "No JSON body provided"})
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response, 400

        result = predict_single(data)
        
        # Log to DB (runs even if fails, using graceful degradation)
        user_id = request.headers.get("X-User-Id", "anonymous")
        log_prediction(user_id, data, result["probability"], result["risk_level"])

        response = jsonify(result)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    except FileNotFoundError as e:
        response = jsonify({"error": "Model not trained yet", "detail": str(e)})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 503
    except Exception as e:
        traceback.print_exc()
        response = jsonify({"error": "Prediction failed", "detail": str(e)})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500

# Required for Vercel
def handler(request, response):
    return app(request, response)
