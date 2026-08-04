import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from faker import Faker

# Set random seeds for reproducibility
Faker.seed(42)
np.random.seed(42)
random.seed(42)

fake = Faker()

# Define structural constants
DEPARTMENTS = {
    'Finance': ['Financial Analyst', 'Accountant', 'Finance Manager'],
    'HR': ['HR Specialist', 'Recruiter', 'HR Manager'],
    'IT': ['SysAdmin', 'IT Support', 'Network Engineer', 'Security Analyst'],
    'Sales': ['Sales Representative', 'Account Manager', 'Sales Director'],
    'R&D': ['Software Engineer', 'Research Scientist', 'QA Engineer', 'R&D Manager']
}

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

NORMAL_APPS = {
    'Finance': ['Excel', 'SAP', 'QuickBooks', 'Slack', 'Outlook', 'Chrome'],
    'HR': ['Workday', 'GreenHouse', 'Slack', 'Outlook', 'Chrome', 'Word'],
    'IT': ['Terminal', 'VS Code', 'PuTTY', 'Wireshark', 'Active Directory Admin', 'Slack', 'Chrome', 'PowerShell'],
    'Sales': ['Salesforce', 'Chrome', 'Outlook', 'Slack', 'PowerPoint', 'Excel'],
    'R&D': ['VS Code', 'Git', 'Jupyter Notebook', 'Slack', 'Terminal', 'Chrome', 'IntelliJ', 'Docker']
}

def choose_app_for_file(file_name, dept):
    if not file_name or file_name == 'None':
        # Generic communication/browser app
        return random.choice([app for app in NORMAL_APPS[dept] if app in ['Slack', 'Outlook', 'Chrome']])
    
    ext = file_name.split('.')[-1]
    if ext in ['xlsx', 'csv']:
        if dept == 'Finance':
            return random.choice(['Excel', 'SAP', 'QuickBooks'])
        elif dept == 'Sales':
            return random.choice(['Excel', 'Salesforce'])
        else:
            return 'Excel'
    elif ext in ['py', 'ipynb', 'go', 'cpp', 'yml', 'docker-compose']:
        return random.choice(['VS Code', 'Git', 'Jupyter Notebook', 'IntelliJ'])
    elif ext in ['sh', 'conf', 'ps1', 'json', 'txt', 'bin', 'log', 'kdbx', 'key']:
        return random.choice(['Terminal', 'VS Code', 'PowerShell', 'PuTTY'])
    elif ext in ['docx', 'pdf', 'pptx']:
        if dept == 'Sales':
            return random.choice(['PowerPoint', 'Word', 'Chrome'])
        elif dept == 'HR':
            return random.choice(['Word', 'Workday', 'Chrome'])
        else:
            return 'Word'
    return random.choice(NORMAL_APPS[dept])

# Generate Employees metadata
print("Generating employee registry...")
employees = []
emp_id_counter = 1
locations_pool = ["New York, USA", "San Francisco, USA", "London, UK", "Bangalore, India", "Sydney, Australia"]

# Map each department to its leadership/manager role
DEPT_MANAGERS = {
    'Finance': 'Finance Manager',
    'HR': 'HR Manager',
    'IT': 'SysAdmin',
    'Sales': 'Sales Director',
    'R&D': 'R&D Manager'
}

for dept, roles in DEPARTMENTS.items():
    manager_role = DEPT_MANAGERS[dept]
    other_roles = [r for r in roles if r != manager_role]
    
    # Generate exactly 12 employees per department
    dept_roles = [manager_role]
    while len(dept_roles) < 12:
        dept_roles.append(random.choice(other_roles))
        
    for role in dept_roles:
        emp_id = f"EMP{emp_id_counter:03d}"
        name = fake.name()
        base_location = random.choice(locations_pool)
        is_remote = random.random() < 0.3
        
        # IP settings
        if is_remote:
            base_ip = fake.ipv4_public()
        else:
            loc_idx = locations_pool.index(base_location) + 1
            base_ip = f"10.100.{loc_idx}.{random.randint(10, 250)}"
            
        # Work hours based on department and role
        if dept == 'Finance':
            work_hours = (9, 18)
        elif dept == 'HR':
            work_hours = (9, 18)
        elif dept == 'IT':
            if 'Support' in role:
                work_hours = random.choice([(8, 17), (9, 18), (12, 21)])
            else:
                work_hours = (9, 18)
        elif dept == 'Sales':
            work_hours = (8, 17)
        elif dept == 'R&D':
            work_hours = (10, 19)
        else:
            work_hours = (9, 18)
            
        employees.append({
            'user_id': emp_id,
            'name': name,
            'department': dept,
            'role': role,
            'base_location': base_location,
            'is_remote': is_remote,
            'base_ip': base_ip,
            'work_hours': work_hours,
            'resignation_date': None
        })
        emp_id_counter += 1

# Assign 3 resignees near the end of 120 days
start_date = datetime(2026, 4, 1)
resignation_day = start_date + timedelta(days=114) # Day 115
resigning_indices = [5, 41, 53]  # Finance, Sales, R&D employees

for idx in resigning_indices:
    employees[idx]['resignation_date'] = resignation_day.date()
    print(f"Resignee Assigned: {employees[idx]['user_id']} ({employees[idx]['name']}) - Dept: {employees[idx]['department']}, Role: {employees[idx]['role']}, Resignation Date: {resignation_day.date()}")

# Generate Base Normal Logs
print("Simulating baseline employee activity...")
logs = []

for day in range(120):
    curr_date = start_date + timedelta(days=day)
    curr_date_str = curr_date.strftime("%Y-%m-%d")
    is_weekend = curr_date.weekday() >= 5
    
    for emp in employees:
        # Check if resigning employee has already resigned (shouldn't log after resignation)
        if emp['resignation_date'] and curr_date.date() > emp['resignation_date']:
            continue
            
        # Determine number of sessions today
        if is_weekend:
            if random.random() < 0.05: # 5% chance of weekend check-in
                num_sess = random.randint(1, 2)
            else:
                num_sess = 0
        else:
            num_sess = random.randint(8, 13)
            
        if num_sess == 0:
            continue
            
        # Generate login/logout windows
        if is_weekend:
            sessions = []
            for _ in range(num_sess):
                h = random.randint(10, 20)
                m = random.randint(0, 59)
                s = random.randint(0, 59)
                login_dt = datetime.strptime(f"{curr_date_str} {h:02d}:{m:02d}:{s:02d}", "%Y-%m-%d %H:%M:%S")
                duration = random.randint(300, 1800)
                logout_dt = login_dt + timedelta(seconds=duration)
                sessions.append((login_dt, logout_dt))
            sessions.sort(key=lambda x: x[0])
        else:
            start_h, end_h = emp['work_hours']
            day_start = datetime.strptime(f"{curr_date_str} {start_h:02d}:00:00", "%Y-%m-%d %H:%M:%S") - timedelta(minutes=30)
            day_end = datetime.strptime(f"{curr_date_str} {end_h:02d}:00:00", "%Y-%m-%d %H:%M:%S") + timedelta(minutes=60)
            
            total_secs = int((day_end - day_start).total_seconds())
            window_size = total_secs // num_sess
            sessions = []
            for i in range(num_sess):
                win_start = day_start + timedelta(seconds=i * window_size)
                login_offset = random.randint(0, window_size // 2)
                login_dt = win_start + timedelta(seconds=login_offset)
                max_dur = min(3600, window_size - login_offset - 60)
                if max_dur < 300:
                    max_dur = 300
                duration = random.randint(300, max_dur)
                logout_dt = login_dt + timedelta(seconds=duration)
                sessions.append((login_dt, logout_dt))
                
        # Fill session activities
        for login_dt, logout_dt in sessions:
            dept = emp['department']
            
            # File access behavior
            file_roll = random.random()
            if file_roll < 0.25:
                file_name = 'None'
                sensitivity = 'None'
            elif file_roll < 0.90:
                file_name = random.choice(NORMAL_FILES[dept])
                sensitivity = random.choice(['public', 'internal', 'internal'])
            else:
                file_name = random.choice(CONFIDENTIAL_FILES[dept])
                sensitivity = 'confidential'
                
            app = choose_app_for_file(file_name, dept)
            
            # Data transfer volume calculation
            if file_name == 'None':
                data_mb = round(np.random.exponential(0.8) + 0.05, 2)
                data_mb = min(data_mb, 5.0)
            else:
                if sensitivity == 'confidential':
                    data_mb = round(np.random.exponential(12.0) + 1.0, 2)
                    data_mb = min(data_mb, 120.0)
                else:
                    if dept == 'R&D':
                        data_mb = round(np.random.exponential(18.0) + 1.0, 2)
                        data_mb = min(data_mb, 180.0)
                    elif dept == 'IT':
                        data_mb = round(np.random.exponential(10.0) + 0.5, 2)
                        data_mb = min(data_mb, 100.0)
                    else:
                        data_mb = round(np.random.exponential(5.0) + 0.2, 2)
                        data_mb = min(data_mb, 50.0)
                        
            # USB usage: extremely rare in normal workflow
            usb = False
            if dept in ['Sales', 'IT'] and random.random() < 0.001:
                usb = True
                data_mb = round(random.uniform(5.0, 100.0), 2)
                
            ip = emp['base_ip']
            if emp['is_remote']:
                # IP dynamically changes occasionally for remote workers
                if random.random() < 0.05:
                    emp['base_ip'] = fake.ipv4_public()
                    ip = emp['base_ip']
                    
            logs.append({
                'user_id': emp['user_id'],
                'name': emp['name'],
                'department': dept,
                'role': emp['role'],
                'date': curr_date_str,
                'login_time': login_dt.strftime("%H:%M:%S"),
                'logout_time': logout_dt.strftime("%H:%M:%S"),
                'files_accessed': file_name,
                'file_sensitivity': sensitivity,
                'data_transferred_mb': data_mb,
                'usb_connected': usb,
                'login_location': emp['base_location'],
                'ip_address': ip,
                'application_used': app,
                'is_anomaly': 0
            })

df = pd.DataFrame(logs)
print(f"Generated baseline dataset with {len(df)} records.")

# Anomaly counters
anomaly_counts = {
    'odd_hour_download': 0,
    'outside_dept_access': 0,
    'unusual_location': 0,
    'odd_hour_usb': 0,
    'resignation_usb': 0
}

def apply_general_anomaly(dataframe, index, department):
    scenario = random.choice(['odd_hour_download', 'outside_dept_access', 'unusual_location', 'odd_hour_usb'])
    anomaly_counts[scenario] += 1
    
    if scenario == 'odd_hour_download':
        # Logging in between 11 PM and 4 AM, downloading large volumes of sensitive files
        login_h = random.choice([23, 0, 1, 2, 3])
        login_m = random.randint(0, 59)
        login_s = random.randint(0, 59)
        dur_mins = random.randint(45, 180)
        
        login_time = f"{login_h:02d}:{login_m:02d}:{login_s:02d}"
        logout_dt = datetime.strptime(f"2026-01-01 {login_time}", "%Y-%m-%d %H:%M:%S") + timedelta(minutes=dur_mins)
        logout_time = logout_dt.strftime("%H:%M:%S")
        
        # 5x - 20x Normal transfers (Normal max is ~120MB, so let's do 600MB to 5000MB)
        data_mb = round(random.uniform(600.0, 5000.0), 2)
        file_name = random.choice(CONFIDENTIAL_FILES[department])
        app = random.choice(['FileZilla', 'WinSCP', 'Python Exfil Script', 'MegaUploader'])
        
        dataframe.at[index, 'login_time'] = login_time
        dataframe.at[index, 'logout_time'] = logout_time
        dataframe.at[index, 'data_transferred_mb'] = data_mb
        dataframe.at[index, 'files_accessed'] = file_name
        dataframe.at[index, 'file_sensitivity'] = 'confidential'
        dataframe.at[index, 'application_used'] = app
        dataframe.at[index, 'usb_connected'] = False
        dataframe.at[index, 'is_anomaly'] = 1
        
    elif scenario == 'outside_dept_access':
        # Accessing critical files belonging to other departments
        other_depts = [d for d in DEPARTMENTS.keys() if d != department]
        target_dept = random.choice(other_depts)
        
        file_name = random.choice(CONFIDENTIAL_FILES[target_dept])
        data_mb = round(random.uniform(100.0, 800.0), 2)
        app = random.choice(['CMD', 'Git', 'File Explorer', 'Chrome'])
        
        dataframe.at[index, 'files_accessed'] = file_name
        dataframe.at[index, 'file_sensitivity'] = 'confidential'
        dataframe.at[index, 'data_transferred_mb'] = data_mb
        dataframe.at[index, 'application_used'] = app
        dataframe.at[index, 'is_anomaly'] = 1
        
    elif scenario == 'unusual_location':
        # Login from an unexpected foreign city/IP address
        unusual_locs = ["Beijing, China", "Moscow, Russia", "Reykjavik, Iceland", "Lagos, Nigeria", "Frankfurt, Germany", "Bucharest, Romania", "Pyongyang, North Korea"]
        loc = random.choice(unusual_locs)
        ip = fake.ipv4_public()
        
        file_name = random.choice(CONFIDENTIAL_FILES[department])
        data_mb = round(random.uniform(300.0, 2000.0), 2)
        app = random.choice(['Tor Browser', 'Chrome', 'CMD'])
        
        dataframe.at[index, 'login_location'] = loc
        dataframe.at[index, 'ip_address'] = ip
        dataframe.at[index, 'files_accessed'] = file_name
        dataframe.at[index, 'file_sensitivity'] = 'confidential'
        dataframe.at[index, 'data_transferred_mb'] = data_mb
        dataframe.at[index, 'application_used'] = app
        dataframe.at[index, 'is_anomaly'] = 1
        
    elif scenario == 'odd_hour_usb':
        # Late-night connection of unauthorized USB drives
        login_h = random.choice([22, 23, 0, 1, 2, 3, 4])
        login_m = random.randint(0, 59)
        login_s = random.randint(0, 59)
        login_time = f"{login_h:02d}:{login_m:02d}:{login_s:02d}"
        
        logout_dt = datetime.strptime(f"2026-01-01 {login_time}", "%Y-%m-%d %H:%M:%S") + timedelta(minutes=random.randint(20, 90))
        logout_time = logout_dt.strftime("%H:%M:%S")
        
        file_name = random.choice(CONFIDENTIAL_FILES[department])
        data_mb = round(random.uniform(500.0, 4000.0), 2)
        app = random.choice(['USB Copy Utility', 'File Explorer'])
        
        dataframe.at[index, 'login_time'] = login_time
        dataframe.at[index, 'logout_time'] = logout_time
        dataframe.at[index, 'usb_connected'] = True
        dataframe.at[index, 'files_accessed'] = file_name
        dataframe.at[index, 'file_sensitivity'] = 'confidential'
        dataframe.at[index, 'data_transferred_mb'] = data_mb
        dataframe.at[index, 'application_used'] = app
        dataframe.at[index, 'is_anomaly'] = 1

def apply_resignation_anomaly(dataframe, index, department):
    anomaly_counts['resignation_usb'] += 1
    
    # 30% chance of accessing files outside their department during resignation exfiltration
    if random.random() < 0.3:
        other_depts = [d for d in DEPARTMENTS.keys() if d != department]
        target_dept = random.choice(other_depts)
        file_name = random.choice(CONFIDENTIAL_FILES[target_dept])
    else:
        file_name = random.choice(CONFIDENTIAL_FILES[department])
        
    data_mb = round(random.uniform(1000.0, 9000.0), 2)
    app = random.choice(['USB Mass Storage', 'File Explorer', 'USB Copy Utility', 'CMD'])
    
    dataframe.at[index, 'usb_connected'] = True
    dataframe.at[index, 'files_accessed'] = file_name
    dataframe.at[index, 'file_sensitivity'] = 'confidential'
    dataframe.at[index, 'data_transferred_mb'] = data_mb
    dataframe.at[index, 'application_used'] = app
    dataframe.at[index, 'is_anomaly'] = 1

# Inject anomalies into ~3% of each user's rows
print("Injecting anomalous activities (~3% per user)...")
for user_id in df['user_id'].unique():
    user_mask = df['user_id'] == user_id
    user_rows = df[user_mask]
    n_total = len(user_rows)
    n_anom = int(round(n_total * 0.03))  # Target ~3% anomalies per user
    
    emp_meta = next(e for e in employees if e['user_id'] == user_id)
    dept = emp_meta['department']
    res_date = emp_meta['resignation_date']
    
    if res_date is not None:
        # Resigning employee simulation: concentrate USB anomalies in last 7 days of their activity
        user_dates = pd.to_datetime(user_rows['date'])
        cutoff_date = pd.to_datetime(res_date) - pd.Timedelta(days=7)
        
        res_period_indices = user_rows[user_dates >= cutoff_date].index.tolist()
        pre_period_indices = user_rows[user_dates < cutoff_date].index.tolist()
        
        # We concentrate 75% of resignation user anomalies inside the final week as repeated USB copies
        n_res_anom = int(round(n_anom * 0.75))
        n_pre_anom = n_anom - n_res_anom
        
        # Sample resignation anomalies
        if len(res_period_indices) >= n_res_anom:
            res_anom_indices = random.sample(res_period_indices, n_res_anom)
        else:
            res_anom_indices = res_period_indices
            n_pre_anom = n_anom - len(res_anom_indices)
            
        # Sample pre-resignation anomalies (general threats)
        pre_anom_indices = random.sample(pre_period_indices, min(n_pre_anom, len(pre_period_indices)))
        
        # Apply pre-resignation general anomalies
        for idx in pre_anom_indices:
            apply_general_anomaly(df, idx, dept)
            
        # Apply resignation USB copy anomalies
        for idx in res_anom_indices:
            apply_resignation_anomaly(df, idx, dept)
    else:
        # Normal employees get general anomalies distributed randomly across all their logs
        anom_indices = random.sample(user_rows.index.tolist(), n_anom)
        for idx in anom_indices:
            apply_general_anomaly(df, idx, dept)

# Ensure the data directory exists
os.makedirs('data', exist_ok=True)

# Save the dataset
csv_path = 'data/synthetic_insider_logs.csv'
df.to_csv(csv_path, index=False)
print(f"\nDataset successfully generated and saved to {csv_path}!\n")

# Summary statistics
print("=" * 60)
print("                    DATASET SUMMARY STATISTICS                    ")
print("=" * 60)
total_rows = len(df)
normal_rows = len(df[df['is_anomaly'] == 0])
anom_rows = len(df[df['is_anomaly'] == 1])

print(f"Total Log Records: {total_rows:,}")
print(f"Normal Records:    {normal_rows:,} ({normal_rows/total_rows*100:.2f}%)")
print(f"Anomalous Records: {anom_rows:,} ({anom_rows/total_rows*100:.2f}%)")
print("-" * 60)

print("Anomaly Category Breakdown:")
for scenario, count in anomaly_counts.items():
    print(f" - {scenario.replace('_', ' ').title()}: {count} ({count/anom_rows*100:.2f}% of anomalies)")
print("-" * 60)

print("Anomalies by Department:")
dept_anoms = df[df['is_anomaly'] == 1]['department'].value_counts()
for dept, count in dept_anoms.items():
    print(f" - {dept}: {count} anomalies")
print("-" * 60)

print("Data Transfer Volume (MB) Statistics:")
print(f" - Overall Average: {df['data_transferred_mb'].mean():.2f} MB")
print(f" - Normal Average:  {df[df['is_anomaly'] == 0]['data_transferred_mb'].mean():.2f} MB")
print(f" - Anomaly Average: {df[df['is_anomaly'] == 1]['data_transferred_mb'].mean():.2f} MB")
print("-" * 60)

print("USB Connections:")
print(f" - Normal USB Connections:  {len(df[(df['is_anomaly'] == 0) & (df['usb_connected'] == True)])}")
print(f" - Anomalous USB Connections: {len(df[(df['is_anomaly'] == 1) & (df['usb_connected'] == True)])}")
print("=" * 60)
