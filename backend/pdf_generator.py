import os
import pandas as pd
import numpy as np
from fpdf import FPDF
from datetime import datetime

class IncidentReportPDF(FPDF):
    def __init__(self, user_meta):
        super().__init__()
        self.user_meta = user_meta
        self.set_margins(15, 15, 15)
        self.set_auto_page_break(auto=True, margin=15)
        
    def header(self):
        # Top banner decoration
        self.set_fill_color(30, 41, 59)  # Slate dark primary
        self.rect(0, 0, 210, 15, 'F')
        
        self.set_text_color(255, 255, 255)
        self.set_font("helvetica", "B", 9)
        self.set_y(4)
        self.cell(0, 8, "APEX SENTINEL MONITORING PIPELINE - AUDIT & COMPLIANCE INCIDENT REPORT", align="C")
        
        self.set_text_color(0, 0, 0)
        self.set_y(20)
        
    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Generated dynamically on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Page {self.page_no()}/{{nb}}", align="L")
        self.cell(0, 10, "CONFIDENTIAL - AUDIT REVIEW ONLY", align="R")

def generate_user_pdf(user_meta, daily_activity, raw_anomalous_sessions, output_path):
    pdf = IncidentReportPDF(user_meta)
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # 1. Document Title Header
    pdf.set_font("helvetica", "B", 18)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 12, "BEHAVIORAL INCIDENT REPORT", ln=True)
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 6, f"TARGET AUDIT USER: {user_meta['name'].upper()} ({user_meta['user_id']})", ln=True)
    pdf.ln(3)
    
    # Border line
    pdf.set_draw_color(226, 232, 240)
    pdf.set_line_width(0.5)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(5)
    
    # 2. Metadata Grid (Key-Value)
    pdf.set_font("helvetica", "B", 9)
    pdf.set_fill_color(241, 245, 249)
    pdf.set_text_color(51, 65, 85)
    
    meta_items = [
        ("Employee ID:", user_meta['user_id'], "Department:", user_meta['department']),
        ("Name:", user_meta['name'], "Role:", user_meta['role']),
        ("Report Date:", datetime.now().strftime('%Y-%m-%d'), "Assessment Scope:", "120-Day Baseline")
    ]
    
    for label1, val1, label2, val2 in meta_items:
        # Col 1
        pdf.cell(30, 8, label1, fill=True)
        pdf.set_font("helvetica", "", 9)
        pdf.cell(60, 8, val1, fill=True)
        # Col 2
        pdf.set_font("helvetica", "B", 9)
        pdf.cell(30, 8, label2, fill=True)
        pdf.set_font("helvetica", "", 9)
        pdf.cell(60, 8, val2, fill=True, ln=True)
    pdf.ln(6)
    
    # Calculate key statistics
    scores = [day['risk_score'] for day in daily_activity]
    max_score = max(scores) if scores else 0.0
    avg_score = sum(scores) / len(scores) if scores else 0.0
    anomalous_days = sum(1 for day in daily_activity if day['is_anomaly'] == 1)
    
    overall_level = "LOW"
    if max_score > 70:
        overall_level = "HIGH"
    elif max_score >= 40:
        overall_level = "MEDIUM"
        
    # 3. Executive Summary
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 8, "EXECUTIVE ASSESSMENT SUMMARY", ln=True)
    pdf.ln(1)
    
    pdf.set_font("helvetica", "", 9.5)
    pdf.set_text_color(30, 41, 59)
    summary_text = (
        f"Behavioral tracking analysis conducted over 120 baseline logging cycles indicates a "
        f"general '{overall_level}' risk score signature for this employee. The maximum risk score "
        f"calculated by the Keras Autoencoder is {max_score:.2f}/100, with an average daily baseline of "
        f"{avg_score:.2f}/100. A total of {anomalous_days} days triggered model reconstruction warnings. "
        f"The primary anomaly clusters are detailed below."
    )
    pdf.multi_cell(0, 5, summary_text)
    pdf.ln(4)
    
    # Risk Level Alert banner
    if overall_level == "HIGH":
        pdf.set_fill_color(254, 226, 226)  # Light red
        pdf.set_text_color(185, 28, 28)    # Red text
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(0, 10, "  CRITICAL ACTION REQUIRED: MEETS MANDATORY RISK AUDIT INTERVENTION PROTOCOLS.", fill=True, ln=True)
    elif overall_level == "MEDIUM":
        pdf.set_fill_color(254, 243, 199)  # Light yellow
        pdf.set_text_color(217, 119, 6)    # Amber text
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(0, 10, "  WARNING STATUS: USER SHOWS MODERATE RISK DEVIATIONS. MONITORING ESCALATED.", fill=True, ln=True)
    else:
        pdf.set_fill_color(209, 250, 229)  # Light green
        pdf.set_text_color(4, 120, 87)     # Green text
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(0, 10, "  STANDARD COMPLIANCE: NO DEVIANT SIGNATURES DETECTED. SYSTEM ACTIVE.", fill=True, ln=True)
    pdf.ln(6)
    
    # 4. Table: Risk score peaks
    pdf.set_text_color(30, 41, 59)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 8, "RECORDED METRIC TIMELINE PEAKS", ln=True)
    pdf.ln(1)
    
    pdf.set_fill_color(226, 232, 240)
    pdf.set_font("helvetica", "B", 8.5)
    pdf.cell(25, 7, "Date", border=1, fill=True)
    pdf.cell(20, 7, "Risk Score", border=1, fill=True)
    pdf.cell(20, 7, "Level", border=1, fill=True)
    pdf.cell(35, 7, "Login Dev (hrs)", border=1, fill=True)
    pdf.cell(35, 7, "Data Z-Score", border=1, fill=True)
    pdf.cell(45, 7, "Files Outside Role", border=1, fill=True, ln=True)
    
    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(0, 0, 0)
    
    # Print the top 8 highest risk score days
    sorted_days = sorted(daily_activity, key=lambda x: x['risk_score'], reverse=True)[:8]
    for day in sorted_days:
        pdf.cell(25, 6, day['date'], border=1)
        pdf.cell(20, 6, f"{day['risk_score']:.2f}", border=1)
        pdf.cell(20, 6, day['risk_level'], border=1)
        pdf.cell(35, 6, f"{day['login_hour_deviation']:.2f}h", border=1)
        pdf.cell(35, 6, f"{day['data_transfer_zscore']:.2f}", border=1)
        pdf.cell(45, 6, f"{day['files_outside_role_pct']*100:.1f}%", border=1, ln=True)
    pdf.ln(6)
    
    # 5. Table: Anomalous Session Detail
    # Filter raw logs for anomalous sessions
    raw_anomalies = [s for s in raw_anomalous_sessions if s['is_anomaly'] == 1]
    if raw_anomalies:
        pdf.set_text_color(30, 41, 59)
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(0, 8, "ANOMALOUS SESSION EVENT DEVIATIONS", ln=True)
        pdf.ln(1)
        
        pdf.set_fill_color(226, 232, 240)
        pdf.set_font("helvetica", "B", 8)
        pdf.cell(22, 7, "Date/Time", border=1, fill=True)
        pdf.cell(42, 7, "File Accessed", border=1, fill=True)
        pdf.cell(20, 7, "Vol (MB)", border=1, fill=True)
        pdf.cell(12, 7, "USB", border=1, fill=True)
        pdf.cell(30, 7, "Location", border=1, fill=True)
        pdf.cell(29, 7, "IP Address", border=1, fill=True)
        pdf.cell(25, 7, "Application", border=1, fill=True, ln=True)
        
        pdf.set_font("helvetica", "", 7.5)
        pdf.set_text_color(0, 0, 0)
        
        # Display up to 10 anomalous sessions
        for s in raw_anomalies[:10]:
            time_str = f"{s['date']} {s['login_time']}"
            pdf.cell(22, 6, time_str, border=1)
            
            fn = s['files_accessed']
            if len(fn) > 23:
                fn = fn[:21] + ".."
            pdf.cell(42, 6, fn, border=1)
            pdf.cell(20, 6, f"{s['data_transferred_mb']:.1f}", border=1)
            pdf.cell(12, 6, "TRUE" if s['usb_connected'] else "FALSE", border=1)
            pdf.cell(30, 6, s['login_location'][:18], border=1)
            pdf.cell(29, 6, s['ip_address'], border=1)
            pdf.cell(25, 6, s['application_used'][:15], border=1, ln=True)
        pdf.ln(8)
        
    # 6. Compliance / Audit Sign-off block
    if pdf.get_y() > 230:
        pdf.add_page()
        
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 6, "AUDIT APPROVAL & ACTION LOG", ln=True)
    pdf.ln(1.5)
    
    pdf.set_font("helvetica", "", 8.5)
    pdf.set_text_color(51, 65, 85)
    pdf.cell(0, 5, "Under threat monitoring compliance directives, I have audited this report and verified its behavioral indices.", ln=True)
    pdf.ln(8)
    
    pdf.cell(90, 5, "Security Officer Signature: ____________________", ln=False)
    pdf.cell(90, 5, "Verification Date: ________________________", ln=True)
    pdf.ln(3)
    pdf.cell(90, 5, "Officer Name/Title: ___________________________", ln=False)
    pdf.cell(90, 5, "Action taken:  [ ] Escalate to HR  [ ] Block Account  [ ] Monitor", ln=True)
    
    pdf.output(output_path)
