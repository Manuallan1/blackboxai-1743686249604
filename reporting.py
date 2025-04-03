from flask import jsonify, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, ScanResult, Policy
from app import create_app
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from datetime import datetime, timedelta
import io

app = create_app()

def generate_pdf_report(scan_results, policy):
    """Generate PDF compliance report"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Report content
    elements = []
    elements.append(Paragraph("Compliance Monitoring Report", styles['Title']))
    elements.append(Spacer(1, 12))
    
    # Summary section
    elements.append(Paragraph("Summary", styles['Heading2']))
    compliant_count = sum(len(r.compliance_status.get('compliant', [])) for r in scan_results)
    non_compliant_count = sum(len(r.compliance_status.get('non_compliant', [])) for r in scan_results)
    
    summary_data = [
        ["Total Scans", len(scan_results)],
        ["Compliant Software", compliant_count],
        ["Non-Compliant Software", non_compliant_count],
        ["Compliance Rate", f"{round(compliant_count/(compliant_count+non_compliant_count)*100, 2)}%"]
    ]
    
    summary_table = Table(summary_data, colWidths=[200, 200])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 12))
    
    # Non-compliant details
    elements.append(Paragraph("Non-Compliant Software Details", styles['Heading2']))
    non_compliant_data = [["Software Name", "Host", "Scan Time"]]
    
    for scan in scan_results:
        for item in scan.compliance_status.get('non_compliant', []):
            non_compliant_data.append([
                item.get('name', 'Unknown'),
                scan.hostname,
                scan.timestamp.strftime("%Y-%m-%d %H:%M")
            ])
    
    if len(non_compliant_data) > 1:
        details_table = Table(non_compliant_data, colWidths=[200, 150, 150])
        details_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(details_table)
    else:
        elements.append(Paragraph("No non-compliant software found", styles['BodyText']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

@app.route('/api/reports/pdf', methods=['GET'])
@jwt_required()
def generate_report():
    """Generate and download PDF report"""
    current_user = get_jwt_identity()
    if current_user['role'] != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403
    
    days = request.args.get('days', default=7, type=int)
    policy_id = request.args.get('policy_id', type=int)
    
    since_date = datetime.utcnow() - timedelta(days=days)
    scan_results = ScanResult.query.filter(ScanResult.timestamp >= since_date).all()
    policy = Policy.query.get(policy_id) if policy_id else None
    
    pdf_buffer = generate_pdf_report(scan_results, policy)
    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=compliance_report_{datetime.now().date()}.pdf'
    
    return response

@app.route('/api/reports/summary', methods=['GET'])
@jwt_required()
def get_report_summary():
    """Get compliance summary data"""
    current_user = get_jwt_identity()
    if current_user['role'] != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403
    
    days = request.args.get('days', default=7, type=int)
    since_date = datetime.utcnow() - timedelta(days=days)
    
    scan_results = ScanResult.query.filter(ScanResult.timestamp >= since_date).all()
    compliant_count = sum(len(r.compliance_status.get('compliant', [])) for r in scan_results)
    non_compliant_count = sum(len(r.compliance_status.get('non_compliant', [])) for r in scan_results)
    total = compliant_count + non_compliant_count
    
    return jsonify({
        'total_scans': len(scan_results),
        'compliant_count': compliant_count,
        'non_compliant_count': non_compliant_count,
        'compliance_rate': round(compliant_count/total*100, 2) if total > 0 else 0,
        'time_period': f"Last {days} days"
    }), 200