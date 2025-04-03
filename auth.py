from flask import jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from app import create_app

app = create_app()

def register_user(email, password, role='standard'):
    if User.query.filter_by(email=email).first():
        return None  # User already exists
    
    hashed_password = generate_password_hash(password)
    new_user = User(email=email, password=hashed_password, role=role)
    db.session.add(new_user)
    db.session.commit()
    return new_user

def login_user(email, password):
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        return None
    
    access_token = create_access_token(identity={
        'id': user.id,
        'email': user.email,
        'role': user.role
    })
    return access_token

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    user = register_user(data['email'], data['password'], data.get('role', 'standard'))
    if not user:
        return jsonify({'message': 'User already exists'}), 400
    return jsonify({'message': 'User created successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    token = login_user(data['email'], data['password'])
    if not token:
        return jsonify({'message': 'Invalid credentials'}), 401
    return jsonify({'access_token': token}), 200

@app.route('/api/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200