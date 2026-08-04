import os
import pickle
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tensorflow as tf

# Resolve absolute default paths relative to script directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MODEL_PATH = os.path.join(PROJECT_ROOT, 'models', 'anomaly_model.pkl')
DEFAULT_HISTORY_PATH = os.path.join(PROJECT_ROOT, 'data', 'synthetic_insider_logs.csv')
DEFAULT_ALERTS_PATH = os.path.join(PROJECT_ROOT, 'alerts_log.csv')

# Define constants for file mappings (to identify files outside department role)
NORMAL_FILES = {
    'Finance': [
        'q3_balance_sheet.xlsx', 'invoice_summary.csv', 'tax_declaration_2026.pdf', 
        'vendor_payments.xlsx', 'monthly_reconciliation.csv', 'expense_reimbursements.xlsx',
        'payroll_details_draft.xlsx', 'depreciation_schedule.csv', 'general_ledger.xlsx'
    ],
    'HR': [
        'onboarding_checklist.pdf', 'candidate_interview_feedback.xlsx', 'employee_handbook.pdf',
        'benefits_summary_2026.pdf', 'hr_policy_draft.docx', 'recruiting_pipeline.xlsx',
        'performance_review_template.docx', 'offer_letter_template.docx', 'leave_requests.xlsx'
    ],
    'IT': [
        'server_health_check.sh', 'network_topology_v3.png', 'firewall_rules_active.conf',
        'active_directory_cleanup.ps1', 'vpn_access_logs.log', 'patch_schedule_q3.xlsx',
        'subnets_mapping.json', 'dns_records_backup.txt', 'router_config_backup.bin'
    ],
    'Sales': [
        'sales_leads_q3.csv', 'client_presentation_v2.pptx', 'customer_contracts_pending.docx',
        'sales_pipeline_dashboard.xlsx', 'pricing_model_2026.xlsx', 'marketing_brochure.pdf',
        'partner_agreement_final.pdf', 'sales_quota_tracking.xlsx', 'meeting_notes_sales.docx'
    ],
    'R&D': [
        'main_controller.py', 'algorithm_simulation.ipynb', 'api_gateway_v2.go',
        'docker-compose.yml', 'unit_test_suite.py', 'system_architecture.pdf',
        'model_training_loss.log', 'quantum_state_estimator.cpp', 'requirements_spec_v1.docx'
    ]
}

CONFIDENTIAL_FILES = {
    'Finance': ['payroll_salaries_2026.xlsx', 'm_and_a_target_valuation.pdf', 'bank_credentials.txt'],
    'HR': ['employee_disciplinary_records.csv', 'salary_band_revisions.xlsx', 'executive_background_checks.pdf'],
    'IT': ['active_directory_master_passwords.kdbx', 'root_ssl_private_key.key', 'aws_iam_policies_admin.json'],
    'Sales': ['enterprise_customer_contact_list.xlsx', 'competitor_intelligence_report.pdf', 'unreleased_pricing_discounts.xlsx'],
    'R&D': ['source_code_intellectual_property.zip', 'next_gen_product_patent.docx', 'secret_key_rotation.py']
}

# Rebuild lookup dictionary
file_to_dept = {}
for dept, files in NORMAL_FILES.items():
    for f in files:
        file_to_dept[f] = dept
for dept, files in CONFIDENTIAL_FILES.items():
    for f in files:
        file_to_dept[f] = dept

def check_outside_dept(file_name, user_dept):
    if not file_name or file_name == 'None' or file_name not in file_to_dept:
        return 0
    return 1 if file_to_dept[file_name] != user_dept else 0

def circular_hour_diff(h1, h2):
    diff = np.abs(h1 - h2)
    return np.minimum(diff, 24.0 - diff)

class RiskEngine:
    def __init__(self, model_pkl_path=None):
        if model_pkl_path is None:
            model_pkl_path = DEFAULT_MODEL_PATH
        print(f"Initializing Risk Engine from {model_pkl_path}...")
        with open(model_pkl_path, 'rb') as f:
            self.model_data = pickle.load(f)
            
        self.model_type = self.model_data['model_type']
        self.feature_cols = self.model_data['feature_cols']
        
        # Load specific model assets based on type
        if self.model_type == 'isolation_forest':
            self.model = self.model_data['model']
            self.min_max = self.model_data['min_max']
        elif self.model_type == 'autoencoder':
            self.scaler = self.model_data['scaler']
            self.min_max = self.model_data['min_max']
            keras_path = self.model_data['keras_model_path']
            # Resolve relative Keras model path if needed
            if not os.path.isabs(keras_path):
                keras_path = os.path.join(PROJECT_ROOT, keras_path)
            # Load the Keras autoencoder model
            self.keras_model = tf.keras.models.load_model(keras_path)
            
    def compute_daily_features(self, new_row, history_path=None):
        if history_path is None:
            history_path = DEFAULT_HISTORY_PATH
        # Load historical logs
        df_hist = pd.read_csv(history_path)
        
        user_id = new_row['user_id']
        date_str = new_row['date']
        date_dt = pd.to_datetime(date_str)
        
        # Filter history for this specific user
        user_hist = df_hist[df_hist['user_id'] == user_id].copy()
        user_hist['date_dt'] = pd.to_datetime(user_hist['date'])
        
        # Format the new incoming activity row
        new_row_df = pd.DataFrame([new_row])
        new_row_df['date_dt'] = pd.to_datetime(new_row_df['date'])
        new_row_df['is_outside_dept_file'] = new_row_df.apply(
            lambda r: check_outside_dept(r['files_accessed'], r['department']), axis=1
        )
        new_row_df['file_accessed_flag'] = new_row_df['files_accessed'].apply(
            lambda x: 0 if x == 'None' or pd.isna(x) else 1
        )
        new_row_df['login_hour'] = pd.to_datetime(new_row_df['login_time']).dt.hour
        new_row_df['usb_connected_int'] = new_row_df['usb_connected'].astype(int)
        
        # Format user history rows
        user_hist['is_outside_dept_file'] = user_hist.apply(
            lambda r: check_outside_dept(r['files_accessed'], r['department']), axis=1
        )
        user_hist['file_accessed_flag'] = user_hist['files_accessed'].apply(
            lambda x: 0 if x == 'None' or pd.isna(x) else 1
        )
        user_hist['login_hour'] = pd.to_datetime(user_hist['login_time']).dt.hour
        user_hist['usb_connected_int'] = user_hist['usb_connected'].astype(int)
        
        # Combine user history with new row
        combined = pd.concat([user_hist, new_row_df], ignore_index=True)
        
        # Aggregate to daily user summaries
        daily_agg = combined.groupby('date').agg(
            is_weekend_access=('date_dt', lambda x: 1 if x.iloc[0].weekday() >= 5 else 0),
            daily_data_transfer=('data_transferred_mb', 'sum'),
            daily_usb_count=('usb_connected_int', 'sum'),
            total_file_accesses=('file_accessed_flag', 'sum'),
            outside_file_accesses=('is_outside_dept_file', 'sum'),
            earliest_login_hour=('login_hour', 'min'),
            locations=('login_location', lambda x: list(set(x)))
        ).reset_index()
        
        daily_agg['date_dt'] = pd.to_datetime(daily_agg['date'])
        daily_agg = daily_agg.sort_values('date_dt').reset_index(drop=True)
        
        # Locate the record for the date we want to evaluate
        today_idx = daily_agg[daily_agg['date'] == date_str].index[0]
        
        # 1. Weekend access
        is_weekend = daily_agg.at[today_idx, 'is_weekend_access']
        
        # 2. Files outside role percentage
        total_files = daily_agg.at[today_idx, 'total_file_accesses']
        outside_files = daily_agg.at[today_idx, 'outside_file_accesses']
        files_outside_pct = outside_files / total_files if total_files > 0 else 0.0
        
        # 3. Data transfer zscore (vs historic daily stats)
        mean_transfer = daily_agg['daily_data_transfer'].mean()
        std_transfer = daily_agg['daily_data_transfer'].std()
        today_transfer = daily_agg.at[today_idx, 'daily_data_transfer']
        data_zscore = (today_transfer - mean_transfer) / (std_transfer + 1e-5)
        
        # 4. Rolling 7-day USB connection count
        start_7d = date_dt - timedelta(days=6)
        usb_7d = daily_agg[
            (daily_agg['date_dt'] >= start_7d) & (daily_agg['date_dt'] <= date_dt)
        ]['daily_usb_count'].sum()
        
        # 5. Rolling 7-day distinct location count
        locs_7d = daily_agg[
            (daily_agg['date_dt'] >= start_7d) & (daily_agg['date_dt'] <= date_dt)
        ]['locations']
        unique_locs = set(loc for subset in locs_7d for loc in subset)
        distinct_locs = len(unique_locs)
        
        # 6. Login hour deviation (vs rolling 30-day earliest login mean)
        start_30d = date_dt - timedelta(days=29)
        login_hours_30d = daily_agg[
            (daily_agg['date_dt'] >= start_30d) & (daily_agg['date_dt'] <= date_dt)
        ]['earliest_login_hour']
        rolling_hour_mean = login_hours_30d.mean()
        today_login_hour = daily_agg.at[today_idx, 'earliest_login_hour']
        hour_dev = circular_hour_diff(today_login_hour, rolling_hour_mean)
        
        # Map values to a feature dictionary
        features = {
            'login_hour_deviation': hour_dev,
            'data_transfer_zscore': data_zscore,
            'is_weekend_access': is_weekend,
            'files_outside_role_pct': files_outside_pct,
            'usb_freq_7day': usb_7d,
            'distinct_locations_7day': distinct_locs
        }
        
        return features
        
    def evaluate_activity(self, new_row, history_path=None):
        if history_path is None:
            history_path = DEFAULT_HISTORY_PATH
        # 1. Compute dynamic daily aggregated features
        features = self.compute_daily_features(new_row, history_path)
        
        # 2. Build input array in correct order
        input_arr = np.array([features[c] for c in self.feature_cols]).reshape(1, -1)
        
        # 3. Model inference
        if self.model_type == 'isolation_forest':
            raw_score = -self.model.decision_function(input_arr)[0]
            risk_score = self.min_max.transform([[raw_score]])[0][0]
        elif self.model_type == 'autoencoder':
            scaled_input = self.scaler.transform(input_arr)
            pred = self.keras_model.predict(scaled_input, verbose=0)
            mse = np.mean(np.power(scaled_input - pred, 2))
            risk_score = self.min_max.transform([[mse]])[0][0]
            
        risk_score = float(np.clip(risk_score, 0.0, 100.0))
        
        # 4. Map score to risk level
        if risk_score < 40:
            risk_level = 'Low'
        elif risk_score <= 70:
            risk_level = 'Medium'
        else:
            risk_level = 'High'
            
        # 5. Alert Triggering
        if risk_level == 'High':
            print(f"\nALERT: user {new_row['name']} flagged - risk score {risk_score:.2f} ({risk_level})")
            self._log_alert_to_csv(new_row, risk_score, risk_level, features)
            
        return risk_score, risk_level, features

    def _log_alert_to_csv(self, new_row, risk_score, risk_level, features, alert_file=None):
        if alert_file is None:
            alert_file = DEFAULT_ALERTS_PATH
        alert_exists = os.path.exists(alert_file)
        
        alert_data = {
            'alert_timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'user_id': new_row['user_id'],
            'name': new_row['name'],
            'department': new_row['department'],
            'role': new_row['role'],
            'date': new_row['date'],
            'risk_score': round(risk_score, 2),
            'risk_level': risk_level,
            'application_used': new_row['application_used'],
            'files_accessed': new_row['files_accessed'],
            'login_hour_dev': round(features['login_hour_deviation'], 3),
            'data_zscore': round(features['data_transfer_zscore'], 3),
            'files_outside_pct': round(features['files_outside_role_pct'], 3)
        }
        
        df_alert = pd.DataFrame([alert_data])
        df_alert.to_csv(alert_file, mode='a', header=not alert_exists, index=False)
        print(f"Logged alert details to {alert_file}")

# ==========================================
# Module Testing & Verification
# ==========================================
if __name__ == '__main__':
    # Initialize engine
    engine = RiskEngine()
    
    # 1. Normal user activity (Should be categorized as LOW risk)
    print("\n" + "-"*40 + "\nTesting Normal Activity Row...")
    normal_row = {
        'user_id': 'EMP001',
        'name': 'Allison Hill',
        'department': 'Finance',
        'role': 'Finance Manager',
        'date': '2026-06-01',
        'login_time': '09:15:00',
        'logout_time': '10:30:00',
        'files_accessed': 'general_ledger.xlsx',
        'file_sensitivity': 'internal',
        'data_transferred_mb': 5.2,
        'usb_connected': False,
        'login_location': 'New York, USA',
        'ip_address': '10.100.1.45',
        'application_used': 'QuickBooks'
    }
    
    score, level, feats = engine.evaluate_activity(normal_row)
    print(f"Results -> Risk Score: {score:.2f} | Risk Level: {level}")
    print("Features extracted:", feats)
    
    # 2. Anomalous user activity (Should be categorized as HIGH risk and trigger alert)
    print("\n" + "-"*40 + "\nTesting Anomalous Activity Row (Exfiltration Scenario)...")
    anomalous_row = {
        'user_id': 'EMP001',
        'name': 'Allison Hill',
        'department': 'Finance',
        'role': 'Finance Manager',
        'date': '2026-06-02',
        'login_time': '02:15:00',
        'logout_time': '04:45:00',
        'files_accessed': 'active_directory_master_passwords.kdbx',  # outside role file
        'file_sensitivity': 'confidential',
        'data_transferred_mb': 12500.0,  # massive bulk download
        'usb_connected': True,           # unauthorized USB connection
        'login_location': 'Pyongyang, North Korea', # travel anomaly
        'ip_address': '175.45.176.1',     # foreign subnet
        'application_used': 'USB Mass Storage'
    }
    
    score, level, feats = engine.evaluate_activity(anomalous_row)
    print(f"Results -> Risk Score: {score:.2f} | Risk Level: {level}")
    print("Features extracted:", feats)
    print("-" * 40 + "\n")
