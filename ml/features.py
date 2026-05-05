import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer
import joblib

def load_data(filepath):
    """Load the Telco Customer Churn dataset."""
    df = pd.read_csv(filepath)
    return df

def apply_feature_engineering(df):
    """
    Apply advanced feature engineering to the dataset.
    This function modifies the dataframe in-place.
    """
    # Standardize column names if needed
    if 'customerID' in df.columns:
        df.drop(columns=['customerID'], inplace=True)
    
    # Handle TotalCharges numeric conversion
    if 'TotalCharges' in df.columns:
        df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')
        # Impute missing TotalCharges with 0 (since they are usually new customers with 0 tenure)
        df['TotalCharges'] = df['TotalCharges'].fillna(0)
    
    # 1. Charge-to-tenure ratio
    if 'MonthlyCharges' in df.columns and 'tenure' in df.columns:
        df['ChargeToTenureRatio'] = df['TotalCharges'] / (df['tenure'] + 1)
        
    # 2. Service bundle score (weighted sum of premium services)
    service_cols = ['PhoneService', 'MultipleLines', 'InternetService', 'OnlineSecurity', 
                    'OnlineBackup', 'DeviceProtection', 'TechSupport', 'StreamingTV', 'StreamingMovies']
    
    # We'll assign points for premium services
    # A simple approach: +1 for "Yes", +1 for "Fiber optic"
    df['ServiceBundleScore'] = 0
    for col in service_cols:
        if col in df.columns:
            if col == 'InternetService':
                df['ServiceBundleScore'] += df[col].apply(lambda x: 2 if x == 'Fiber optic' else (1 if x == 'DSL' else 0))
            else:
                df['ServiceBundleScore'] += df[col].apply(lambda x: 1 if x == 'Yes' else 0)
                
    # 3. Contract risk score
    if 'Contract' in df.columns:
        contract_risk = {'Month-to-month': 3, 'One year': 2, 'Two year': 1}
        df['ContractRiskScore'] = df['Contract'].map(contract_risk).fillna(2)
        
    # 4. Interaction terms
    if 'SeniorCitizen' in df.columns and 'MonthlyCharges' in df.columns:
        df['Senior_MonthlyCharges'] = df['SeniorCitizen'] * df['MonthlyCharges']
        
    if 'tenure' in df.columns and 'InternetService' in df.columns:
        df['NewCustomer_FiberOptic'] = ((df['tenure'] <= 12) & (df['InternetService'] == 'Fiber optic')).astype(int)

    # 5. Tenure Group
    if 'tenure' in df.columns:
        df["TenureGroup"] = pd.cut(df["tenure"], bins=[-1, 12, 24, 48, 72, 100], labels=[1, 2, 3, 4, 5]).astype(int)

    # 6. Log transforms on skewed numeric columns (TotalCharges, MonthlyCharges)
    if 'TotalCharges' in df.columns:
        df['TotalCharges_Log'] = np.log1p(df['TotalCharges'])
    if 'MonthlyCharges' in df.columns:
        df['MonthlyCharges_Log'] = np.log1p(df['MonthlyCharges'])

    return df

def preprocess_data(df, is_training=True, artifacts=None):
    """
    Preprocess data (encode, scale).
    If is_training=True, it fits the encoders and scalers and returns them.
    If is_training=False, it uses the provided artifacts.
    """
    df = df.copy()
    
    # Handle Target
    y = None
    if 'Churn' in df.columns:
        y = df['Churn'].map({'Yes': 1, 'No': 0, 1: 1, 0: 0}).fillna(0).astype(int).values
        df.drop(columns=['Churn'], inplace=True)
    
    # Categorical and Numerical Columns
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    num_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    if is_training:
        encoders = {}
        # Fill missing values
        for col in num_cols:
            df[col] = df[col].fillna(df[col].median())
            
        for col in cat_cols:
            df[col] = df[col].fillna('Unknown').astype(str)
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col])
            encoders[col] = le
            
        feature_names = df.columns.tolist()
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df[feature_names])
        
        return X_scaled, y, feature_names, encoders, scaler
        
    else:
        encoders = artifacts['encoders']
        scaler = artifacts['scaler']
        feature_names = artifacts['feature_names']
        
        for feat in feature_names:
            if feat not in df.columns:
                df[feat] = 0
                
        for col in num_cols:
            if col in df.columns:
                df[col] = df[col].fillna(df[col].median())
                
        for col, le in encoders.items():
            if col in df.columns:
                df[col] = df[col].astype(str)
                known_classes = set(le.classes_)
                df[col] = df[col].apply(lambda x: x if x in known_classes else le.classes_[0])
                df[col] = le.transform(df[col])
                
        # Fill remaining object types that were not in training set
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = 0
            
        X = df[feature_names].values.astype(float)
        X_scaled = scaler.transform(X)
        
        return X_scaled, y

