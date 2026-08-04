import os
import random
import numpy as np
import pandas as pd

# Set path constants
RAW_CSV_PATH = 'data/synthetic_insider_logs.csv'
FEATURES_CSV_PATH = 'data/features.csv'

# Define normal files mapping (to determine file access department origin)
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

# Construct reverse lookup to determine a file's department
file_to_dept = {}
for dept, files in NORMAL_FILES.items():
    for f in files:
        file_to_dept[f] = dept
for dept, files in CONFIDENTIAL_FILES.items():
    for f in files:
        file_to_dept[f] = dept

def check_outside_dept(row):
    file = row['files_accessed']
    if not file or file == 'None' or file not in file_to_dept:
        return 0
    # Returns 1 if file department doesn't match employee department
    return 1 if file_to_dept[file] != row['department'] else 0

def run_feature_pipeline():
    print(f"Loading raw log data from {RAW_CSV_PATH}...")
    df = pd.read_csv(RAW_CSV_PATH)
    
    # 1. Row-level preprocessing
    df['login_hour'] = pd.to_datetime(df['login_time'], format='%H:%M:%S').dt.hour
    df['is_outside_dept_file'] = df.apply(check_outside_dept, axis=1)
    df['file_accessed_flag'] = df['files_accessed'].apply(lambda x: 0 if x == 'None' or pd.isna(x) else 1)
    
    # Check day of week for weekend access (Saturday=5, Sunday=6)
    df['date_dt'] = pd.to_datetime(df['date'])
    df['is_weekend_access'] = df['date_dt'].dt.weekday.apply(lambda x: 1 if x >= 5 else 0)
    
    # Convert usb_connected to integer flag
    df['usb_connected_int'] = df['usb_connected'].astype(int)
    
    # 2. Aggregation to Daily Level per User
    print("Aggregating log events to daily user profiles...")
    daily_df = df.groupby(['user_id', 'date']).agg(
        name=('name', 'first'),
        department=('department', 'first'),
        role=('role', 'first'),
        is_weekend_access=('is_weekend_access', 'first'),
        daily_data_transfer=('data_transferred_mb', 'sum'),
        daily_usb_count=('usb_connected_int', 'sum'),
        total_file_accesses=('file_accessed_flag', 'sum'),
        outside_file_accesses=('is_outside_dept_file', 'sum'),
        earliest_login_hour=('login_hour', 'min'), # Earliest login hour of the day
        locations=('login_location', lambda x: list(set(x))),
        is_anomaly=('is_anomaly', 'max') # 1 if any session that day was anomalous
    ).reset_index()
    
    # Sort for rolling operations
    daily_df = daily_df.sort_values(by=['user_id', 'date']).reset_index(drop=True)
    
    # 3. Calculate files_outside_role_pct
    daily_df['files_outside_role_pct'] = np.where(
        daily_df['total_file_accesses'] > 0,
        daily_df['outside_file_accesses'] / daily_df['total_file_accesses'],
        0.0
    )
    
    # 4. Calculate login_hour_deviation (vs 30-day rolling average)
    print("Computing rolling login hour deviations...")
    # Calculate rolling mean of the earliest login hour per user (window=30 days)
    daily_df['rolling_login_hour_30d'] = daily_df.groupby('user_id')['earliest_login_hour'].transform(
        lambda x: x.rolling(window=30, min_periods=1).mean()
    )
    
    # Circular hour distance (handling 24h wraps)
    def circular_hour_diff(h1, h2):
        diff = np.abs(h1 - h2)
        return np.minimum(diff, 24.0 - diff)
    
    daily_df['login_hour_deviation'] = circular_hour_diff(
        daily_df['earliest_login_hour'],
        daily_df['rolling_login_hour_30d']
    )
    
    # 5. Calculate data_transfer_zscore (vs user's own historical average/std)
    print("Computing historical data transfer z-scores...")
    user_stats = daily_df.groupby('user_id')['daily_data_transfer'].agg(['mean', 'std']).reset_index()
    user_stats.rename(columns={'mean': 'user_hist_mean', 'std': 'user_hist_std'}, inplace=True)
    
    daily_df = daily_df.merge(user_stats, on='user_id', how='left')
    # Use 1e-5 epsilon to avoid division by zero
    daily_df['data_transfer_zscore'] = (daily_df['daily_data_transfer'] - daily_df['user_hist_mean']) / (daily_df['user_hist_std'] + 1e-5)
    
    # 6. Calculate usb_freq_7day (rolling 7-day sum of usb count)
    print("Computing rolling USB frequency metrics...")
    daily_df['usb_freq_7day'] = daily_df.groupby('user_id')['daily_usb_count'].transform(
        lambda x: x.rolling(window=7, min_periods=1).sum()
    )
    
    # 7. Calculate distinct_locations_7day (rolling unique count)
    print("Computing rolling geolocation diversity...")
    def get_rolling_unique_locations(group):
        loc_series = group['locations']
        rolling_counts = []
        for i in range(len(group)):
            start = max(0, i - 6)
            window_locs = loc_series.iloc[start:i+1]
            unique_set = set(loc for subset in window_locs for loc in subset)
            rolling_counts.append(len(unique_set))
        return pd.Series(rolling_counts, index=group.index)
        
    daily_df['distinct_locations_7day'] = daily_df.groupby('user_id', group_keys=False).apply(get_rolling_unique_locations)
    
    # 8. Clean up and format final output columns
    output_cols = [
        'user_id', 'name', 'department', 'role', 'date',
        'login_hour_deviation', 'data_transfer_zscore', 'is_weekend_access',
        'files_outside_role_pct', 'usb_freq_7day', 'distinct_locations_7day',
        'is_anomaly'
    ]
    
    features_df = daily_df[output_cols].copy()
    
    # Save features dataset
    features_df.to_csv(FEATURES_CSV_PATH, index=False)
    print(f"\nFeature engineering pipeline complete! Features saved to {FEATURES_CSV_PATH}\n")
    
    # Report summary stats for validation
    print("=" * 60)
    print("                    DAILY FEATURES SUMMARY                    ")
    print("=" * 60)
    print(f"Total Aggregated Daily Records: {len(features_df):,}")
    print(f"Anomalous Daily Records:        {features_df['is_anomaly'].sum()} ({features_df['is_anomaly'].mean()*100:.2f}%)")
    print("-" * 60)
    print("Mean values of features by label (Normal vs Anomaly):")
    print(features_df.groupby('is_anomaly')[[
        'login_hour_deviation', 'data_transfer_zscore', 
        'files_outside_role_pct', 'usb_freq_7day', 'distinct_locations_7day'
    ]].mean().round(3).T)
    print("=" * 60)

if __name__ == '__main__':
    run_feature_pipeline()
