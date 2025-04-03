from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Policy, User
from app import create_app

app = create_app()

@app.route('/api/policies', methods=['GET'])
@jwt_required()
def get_policies():
    current_user = get_jwt_identity()
    if current_user['role'] != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403
    
    policies = Policy.query.all()
    return jsonify([{
        'id': policy.id,
        'name': policy.name,
        'description': policy.description,
        'rules': policy.rules,
        'created_at': policy.created_at
    } for policy in policies]), 200

@app.route('/api/policies', methods=['POST'])
@jwt_required()
def create_policy():
    current_user = get_jwt_identity()
    if current_user['role'] != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403
    
    data = request.get_json()
    new_policy = Policy(
        name=data['name'],
        description=data.get('description', ''),
        rules=data['rules'],
        created_by=current_user['id']
    )
    db.session.add(new_policy)
    db.session.commit()
    return jsonify({'message': 'Policy created successfully'}), 201

@app.route('/api/policies/<int:policy_id>', methods=['PUT'])
@jwt_required()
def update_policy(policy_id):
    current_user = get_jwt_identity()
    if current_user['role'] != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403
    
    policy = Policy.query.get_or_404(policy_id)
    data = request.get_json()
    
    policy.name = data.get('name', policy.name)
    policy.description = data.get('description', policy.description)
    policy.rules = data.get('rules', policy.rules)
    
    db.session.commit()
    return jsonify({'message': 'Policy updated successfully'}), 200

@app.route('/api/policies/<int:policy_id>', methods=['DELETE'])
@jwt_required()
def delete_policy(policy_id):
    current_user = get_jwt_identity()
    if current_user['role'] != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403
    
    policy = Policy.query.get_or_404(policy_id)
    db.session.delete(policy)
    db.session.commit()
    return jsonify({'message': 'Policy deleted successfully'}), 200