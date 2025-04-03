from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_mail import Message
from models import db, Alert, ScanResult, User
from app import create_app
from monitoring import classify_software
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText

app = create_app()

def check_for_non_compliance(scan_result):
    """Check scan results and generate alerts if needed"""
    non_compliant = scan_result.compliance_status.get('non_compliant', [])
    if non_compliant:
        # Create alert record
        new_alert = Alert(
            scan_id=scan_result.id,
            severity='high' if len(non_compliant) > 5 else 'medium',
            message=f"Found {len(non_compliant)} non-compliant software items"
        )
        db.session.add(new_alert)
        db.session.commit()
        
        # Send email notification to admins
        send_alert_notification(new_alert, scan_result)
        
        return new_alert
    return None

def send_alert_notification(alert, scan_result):
    """Send email notification about non-compliance"""
    admins = User.query.filter_by(role='admin').all()
    if not admins:
        return
        
    # Simple email sending (configure SMTP settings in production)
    sender = "alerts@compliancesystem.com"
    subject = f"Compliance Alert: {alert.message}"
    body = f"""
    Non-compliance detected:
    
    Scan ID: {scan_result.id}
    Host: {scan_result.hostname}
    Time: {scan_result.timestamp}
    
    Non-compliant items: {len(scan_result.compliance_status['non_compliant'])}
    """
    
    for admin in admins:
        try:
            msg = Message(subject, sender=sender, recipients=[admin.email])
            msg.body = body
            app.mail.send(msg)
        except Exception as e:
            app.logger.error(f"Failed to send alert email: {str(e)}")

@app.route('/api/alerts', methods=['GET'])
@jwt_required()
def get_alerts():
    """Get all alerts (admin only)"""
    current_user = get_jwt_identity()
    if current_user['role'] != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403
    
    days = request.args.get('days', default=7, type=int)
    since_date = datetime.utcnow() - timedelta(days=days)
    
    alerts = Alert.query.filter(Alert.created_at >= since_date).order_by(Alert.created_at.desc()).all()
    return jsonify([{
        'id': alert.id,
        'scan_id': alert.scan_id,
        'severity': alert.severity,
        'message': alert.message,
        'resolved': alert.resolved,
        'created_at': alert.created_at
    } for alert in alerts]), 200

@app.route('/api/alerts/<int:alert_id>/resolve', methods=['PUT'])
@jwt_required()
def resolve_alert(alert_id):
    """Mark alert as resolved"""
    current_user = get_jwt_identity()
    if current_user['role'] != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403
    
    alert = Alert.query.get_or_404(alert_id)
    alert.resolved = True
    db.session.commit()
    
    return jsonify({'message': 'Alert resolved successfully'}), 200