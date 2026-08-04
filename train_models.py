import os
import pickle
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense

# Set random seeds for reproducibility
np.random.seed(42)
tf.random.set_seed(42)

# Load features
FEATURES_CSV = 'data/features.csv'
df = pd.read_csv(FEATURES_CSV)

# Define feature columns and target label
feature_cols = [
    'login_hour_deviation', 'data_transfer_zscore', 'is_weekend_access',
    'files_outside_role_pct', 'usb_freq_7day', 'distinct_locations_7day'
]
X = df[feature_cols]
y = df['is_anomaly']

# Train-Test Split (80/20) with stratification on the label
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Train set shape: {X_train.shape}, Test set shape: {X_test.shape}")
print(f"Anomaly rate in train: {y_train.mean()*100:.2f}%, in test: {y_test.mean()*100:.2f}%\n")

# Scale features for the Autoencoder
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# ==========================================
# 1. Isolation Forest (Baseline Model)
# ==========================================
print("Training Isolation Forest...")
contamination = y_train.mean() # Ground truth anomaly rate as contamination baseline
if_model = IsolationForest(contamination=contamination, random_state=42)
if_model.fit(X_train)

# Calculate Isolation Forest anomaly scores
# decision_function returns negative for anomalies, positive for normals.
# We take negative of decision_function so higher = more anomalous.
raw_scores_if_train = -if_model.decision_function(X_train)
raw_scores_if_test = -if_model.decision_function(X_test)

# Scale Isolation Forest scores to 0-100 risk score (clipped at 95th percentile)
clip_val_if = np.percentile(raw_scores_if_train, 95)
raw_scores_if_train_clipped = np.clip(raw_scores_if_train, None, clip_val_if)
min_max_if = MinMaxScaler(feature_range=(0, 100))
min_max_if.fit(raw_scores_if_train_clipped.reshape(-1, 1))

raw_scores_if_test_clipped = np.clip(raw_scores_if_test, None, clip_val_if)
risk_scores_if = min_max_if.transform(raw_scores_if_test_clipped.reshape(-1, 1)).flatten()

# Predict binary anomaly labels based on target contamination percentile
threshold_if = np.percentile(risk_scores_if, 100 * (1 - contamination))
y_pred_if = (risk_scores_if >= threshold_if).astype(int)

# ==========================================
# 2. Keras Autoencoder (Deep Learning Model)
# ==========================================
print("Training Keras Autoencoder...")
# Autoencoders are trained ONLY on normal instances for unsupervised reconstruction
X_train_normal = X_train_scaled[y_train == 0]

input_dim = len(feature_cols)
encoding_dim = 2 # bottleneck dimensionality representation

autoencoder = Sequential([
    Dense(4, activation='relu', input_shape=(input_dim,)),
    Dense(encoding_dim, activation='relu'),
    Dense(4, activation='relu'),
    Dense(input_dim, activation='linear')
])

autoencoder.compile(optimizer='adam', loss='mse')

# Train Autoencoder
autoencoder.fit(
    X_train_normal, X_train_normal,
    epochs=70,
    batch_size=32,
    validation_split=0.1,
    verbose=0
)

# Calculate test reconstruction MSE (raw anomaly score)
reconstruction_train = autoencoder.predict(X_train_scaled, verbose=0)
mse_train = np.mean(np.power(X_train_scaled - reconstruction_train, 2), axis=1)

reconstruction_test = autoencoder.predict(X_test_scaled, verbose=0)
mse_test = np.mean(np.power(X_test_scaled - reconstruction_test, 2), axis=1)

# Scale Autoencoder scores to 0-100 risk score (clipped at 95th percentile)
clip_val_ae = np.percentile(mse_train, 95)
mse_train_clipped = np.clip(mse_train, None, clip_val_ae)
min_max_ae = MinMaxScaler(feature_range=(0, 100))
min_max_ae.fit(mse_train_clipped.reshape(-1, 1))

mse_test_clipped = np.clip(mse_test, None, clip_val_ae)
risk_scores_ae = min_max_ae.transform(mse_test_clipped.reshape(-1, 1)).flatten()

# Predict binary anomaly labels based on target contamination percentile
threshold_ae = np.percentile(risk_scores_ae, 100 * (1 - contamination))
y_pred_ae = (risk_scores_ae >= threshold_ae).astype(int)

# ==========================================
# 3. Model Evaluation & Comparison
# ==========================================
# Evaluation Metrics for Isolation Forest
precision_if = precision_score(y_test, y_pred_if)
recall_if = recall_score(y_test, y_pred_if)
f1_if = f1_score(y_test, y_pred_if)
auc_if = roc_auc_score(y_test, risk_scores_if)

# Evaluation Metrics for Autoencoder
precision_ae = precision_score(y_test, y_pred_ae)
recall_ae = recall_score(y_test, y_pred_ae)
f1_ae = f1_score(y_test, y_pred_ae)
auc_ae = roc_auc_score(y_test, risk_scores_ae)

# Print Comparison Table
print("\n" + "=" * 70)
print("                    MODEL PERFORMANCE COMPARISON                    ")
print("=" * 70)
print(f"{'Model Name':<20} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10} | {'ROC-AUC':<10}")
print("-" * 70)
print(f"{'Isolation Forest':<20} | {precision_if:<10.4f} | {recall_if:<10.4f} | {f1_if:<10.4f} | {auc_if:<10.4f}")
print(f"{'Autoencoder':<20} | {precision_ae:<10.4f} | {recall_ae:<10.4f} | {f1_ae:<10.4f} | {auc_ae:<10.4f}")
print("=" * 70 + "\n")

# ==========================================
# 4. Save the Better Model
# ==========================================
models_dir = 'models'
os.makedirs(models_dir, exist_ok=True)
pkl_path = os.path.join(models_dir, 'anomaly_model.pkl')

best_model_data = {}
if f1_if >= f1_ae:
    print(f"Winner Model: Isolation Forest (F1: {f1_if:.4f} vs Autoencoder F1: {f1_ae:.4f})")
    best_model_data = {
        'model_type': 'isolation_forest',
        'model': if_model,
        'min_max': min_max_if,
        'feature_cols': feature_cols
    }
else:
    print(f"Winner Model: Autoencoder (F1: {f1_ae:.4f} vs Isolation Forest F1: {f1_if:.4f})")
    keras_path = os.path.join(models_dir, 'autoencoder_model.keras')
    autoencoder.save(keras_path)
    best_model_data = {
        'model_type': 'autoencoder',
        'keras_model_path': keras_path,
        'scaler': scaler,
        'min_max': min_max_ae,
        'feature_cols': feature_cols
    }

# Serialize metadata wrapper to anomaly_model.pkl
with open(pkl_path, 'wb') as f:
    pickle.dump(best_model_data, f)
print(f"Successfully saved model wrapper to {pkl_path}")
