import os
import datetime
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Failed to initialize Supabase client: {e}")

def log_prediction(user_id: str, input_features: dict, probability: float, risk_level: str):
    """
    Log a single prediction to the 'predictions' table.
    """
    if not supabase:
        return False

    try:
        data = {
            "user_id": user_id or "anonymous",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "tenure": input_features.get("tenure"),
            "monthly_charges": input_features.get("MonthlyCharges"),
            "probability": probability,
            "risk_level": risk_level,
            "features_json": input_features
        }
        supabase.table("predictions").insert(data).execute()
        return True
    except Exception as e:
        print(f"Error logging prediction: {e}")
        return False

def get_recent_predictions(user_id: str = None, limit: int = 10):
    """
    Get recent predictions for the dashboard.
    """
    if not supabase:
        return []

    try:
        query = supabase.table("predictions").select("*").order("timestamp", desc=True).limit(limit)
        if user_id:
            query = query.eq("user_id", user_id)
        
        result = query.execute()
        return result.data
    except Exception as e:
        print(f"Error fetching predictions: {e}")
        return []

def log_batch_job(user_id: str, total_records: int, high_risk_count: int, avg_probability: float):
    """
    Log a batch processing job.
    """
    if not supabase:
        return False

    try:
        data = {
            "user_id": user_id or "anonymous",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "total_records": total_records,
            "high_risk_count": high_risk_count,
            "avg_probability": avg_probability
        }
        supabase.table("batch_jobs").insert(data).execute()
        return True
    except Exception as e:
        print(f"Error logging batch job: {e}")
        return False
