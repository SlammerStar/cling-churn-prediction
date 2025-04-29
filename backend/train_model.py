# backend/train_model.py

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import pickle

# Step 1: Generate dummy customer data
np.random.seed(42)  # For reproducibility
n_samples = 500

data = {
    'id': np.arange(1, n_samples + 1),
    'name': [f'Customer_{i}' for i in range(1, n_samples + 1)],
    'tenure': np.random.randint(1, 60, size=n_samples),          # Months
    'charges': np.random.uniform(20.0, 120.0, size=n_samples),    # Monthly charges
    'churn': np.random.choice([0, 1], size=n_samples, p=[0.7, 0.3]) # 0 = No churn, 1 = Churn
}

df = pd.DataFrame(data)

# Step 2: Features and Target
X = df[['tenure', 'charges']]  # You can expand later with more features
y = df['churn']

# Step 3: Split into Train and Test (optional for real case)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Step 4: Train the Model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Step 5: Save the trained model
with open('model.pkl', 'wb') as f:
    pickle.dump(model, f)

print("✅ Model trained and saved as 'model.pkl'")
