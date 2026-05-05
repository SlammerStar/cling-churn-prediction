import io
import sys
import traceback
from pathlib import Path
import pandas as pd
from flask import Flask, request, jsonify

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from ml.predictor import predict_batch
from core.database import log_batch_job
import os
import resend

app = Flask(__name__)

@app.route('/api/predict/batch', methods=['POST', 'OPTIONS'])
@app.route('/api/predict_batch', methods=['POST', 'OPTIONS'])
@app.route('/', methods=['POST', 'OPTIONS'])
def batch_predict():
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    try:
        if "file" not in request.files:
            response = jsonify({"error": "No file provided. Send a CSV as 'file' field."})
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response, 400

        f = request.files["file"]
        if f.filename == "":
            response = jsonify({"error": "Empty filename"})
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response, 400

        content = f.read().decode("utf-8")
        df = pd.read_csv(io.StringIO(content))

        if df.empty:
            response = jsonify({"error": "CSV file is empty"})
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response, 400

        result_df = predict_batch(df)

        churn_count = int(result_df["ChurnPrediction"].sum())
        total = len(result_df)
        avg_prob = float(result_df["ChurnProbability"].mean())

        risk_dist = result_df["RiskLevel"].value_counts().to_dict()
        risk_dist = {str(k): int(v) for k, v in risk_dist.items()}

        records = result_df.to_dict(orient="records")

        # Basic integration point for Notifications later:
        high_risk_count = risk_dist.get('High', 0)
        
        # Send Email Alert if high risk users found
        if high_risk_count > 0:
            resend_key = os.environ.get("RESEND_API_KEY")
            alert_email = os.environ.get("ALERT_EMAIL")
            if resend_key and alert_email:
                try:
                    resend.api_key = resend_key
                    resend.Emails.send({
                        "from": "Cling Platform <onboarding@resend.dev>",
                        "to": alert_email,
                        "subject": f"Cling Alert: {high_risk_count} High-Risk Customers Detected",
                        "html": f"<p>A recent batch upload identified <strong>{high_risk_count}</strong> customers with a high churn risk.</p><p>Total processed: {total}</p><p>Please check the Cling dashboard for detailed reports.</p>"
                    })
                except Exception as e:
                    print(f"Failed to send email alert: {e}")

        user_id = request.headers.get("X-User-Id", "anonymous")
        log_batch_job(user_id, total, high_risk_count, avg_prob)

        response = jsonify({
            "total": total,
            "churn_count": churn_count,
            "churn_rate": round(churn_count / total * 100, 1),
            "avg_churn_probability": round(avg_prob, 1),
            "risk_distribution": risk_dist,
            "predictions": records
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    except Exception as e:
        traceback.print_exc()
        response = jsonify({"error": "Batch prediction failed", "detail": str(e)})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500

def handler(request, response):
    return app(request, response)
