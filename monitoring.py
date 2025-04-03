import psutil
from flask import jsonify
from flask_jwt_extended import jwt_required
from models import db, ScanResult, Policy
from app import create_app
from apscheduler.schedulers.background import BackgroundScheduler
import json
from datetime import datetime

app = create_app()
scheduler = BackgroundScheduler()

def detect_software():
    """Detect installed software and classify against policies"""
    software_list = []
    for proc in psutil.process_iter(['name', 'exe', 'username']):
        try:
            software_list.append({
                'name': proc.info['name'],
                'path': proc.info['exe'],
                'user': proc.info['username']
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return software_list

def classify_software(software_list, policy_id=None):
    """Classify software as compliant/non-compliant based on policies"""
    if policy_id:
        policy = Policy.query.get(policy_id)
        rules = policy.rules if policy else {}
    else:
        rules = Policy.query.first().rules  # Default to first policy

    compliant = []
    non_compliant = []
    
    for software in software_list:
        # Simple classification logic - can be replaced with ML model
        if any(rule.lower() in software['name'].lower() for rule in rules.get('allowed', [])):
            compliant.append(software)
        else:
            non_compliant.append(software)
    
    return {
        'compliant': compliant,
        'non_compliant': non_compliant,
        'timestamp': datetime.utcnow()
    }

@app.route('/api/scan', methods=['POST'])
@jwt_required()
def perform_scan():
    """Endpoint for manual scan trigger"""
    software_list = detect_software()
    classification = classify_software(software_list)
    
    # Store scan result
    scan = ScanResult(
        hostname=psutil.users()[0].name if psutil.users() else 'unknown',
        software_list=software_list,
        compliance_status=classification
    )
    db.session.add(scan)
    db.session.commit()
    
    return jsonify(classification), 200

def scheduled_scan():
    """Scheduled scan job"""
    with app.app_context():
        software_list = detect_software()
        classification = classify_software(software_list)
        
        scan = ScanResult(
            hostname=psutil.users()[0].name if psutil.users() else 'unknown',
            software_list=software_list,
            compliance_status=classification
        )
        db.session.add(scan)
        db.session.commit()

# Start scheduler when module loads
if not scheduler.running:
    scheduler.add_job(scheduled_scan, 'interval', minutes=15)
    scheduler.start()