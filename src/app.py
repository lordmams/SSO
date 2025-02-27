from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from lifxlan import LifxLAN
from connect import (
    connect_to_dynamodb, 
    add_user, 
    login_user, 
    logout_user, 
    save_face_encoding, 
    verify_face
)
from face_auth import process_face_image
import os
from datetime import timedelta
from functools import wraps
import numpy as np

num_lights = None
lifx = LifxLAN(num_lights)
lifx.get_power_all_lights()

app = Flask(__name__)
app.secret_key = os.getenv('JWT_SECRET_KEY')
app.permanent_session_lifetime = timedelta(days=1)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'token' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=['GET'])
def index():
   return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        use_face_auth = request.form.get('use_face_auth') == 'on'
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        if not use_face_auth and not password:
            return jsonify({'error': 'Password is required'}), 400
        
        db = connect_to_dynamodb()
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500
            
        users_table = db.Table('Users')

        token = login_user(users_table, email, password, use_face_auth)
        if token:
            session.permanent = True
            session['token'] = token
            session['email'] = email
            return redirect(url_for('index'))
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    
    return render_template('login.html')

@app.route('/login/face', methods=['POST'])
def face_login():
    try:
        data = request.get_json()
        email = data.get('email')
        image_data = data.get('image')
        
        if not email or not image_data:
            return jsonify({'error': 'Missing data'}), 400
            
        face_encoding = process_face_image(image_data)
        if face_encoding is None:
            return jsonify({'error': 'No face detected'}), 400
            
        db = connect_to_dynamodb()
        users_table = db.Table('Users')
        
        if verify_face(users_table, email, face_encoding):
            token = login_user(users_table, email, None, face_auth=True)
            if token:
                session.permanent = True
                session['token'] = token
                session['email'] = email
                return jsonify({
                    'success': True,
                    'redirect': url_for('index')  
                })
                
        return jsonify({'error': 'Face verification failed'}), 401
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/verify-face', methods=['POST'])
def verify_face_capture():
    try:
        data = request.get_json()
        image_data = data.get('image')
        
        if not image_data:
            return jsonify({'error': 'No image data'}), 400
            
        face_encoding = process_face_image(image_data)
        
        if face_encoding is None:
            return jsonify({'success': False, 'error': 'No face detected'}), 400
            
        # Stocker temporairement l'encodage dans la session
        session['temp_face_encoding'] = face_encoding.tolist()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        use_face_auth = request.form.get('use_face_auth') == 'on'
        
        if not all([email, password, confirm_password]):
            return jsonify({'error': 'Tous les champs sont requis'}), 400
            
        if password != confirm_password:
            return jsonify({'error': 'Les mots de passe ne correspondent pas'}), 400
            
        db = connect_to_dynamodb()
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500
            
        users_table = db.Table('Users')
       
        if add_user(users_table, email, password):
            if use_face_auth and 'temp_face_encoding' in session:
                # Sauvegarder l'encodage facial
                face_encoding = np.array(session['temp_face_encoding'])
                save_face_encoding(users_table, email, face_encoding)
                session.pop('temp_face_encoding', None)
                
            return redirect(url_for('login'))
            
        return jsonify({'error': 'Failed to create user'}), 500
        
    return render_template('register.html')

@app.route('/logout')
def logout():
    if 'email' in session:
        db = connect_to_dynamodb()
        if db:
            users_table = db.Table('Users')
            logout_user(users_table, session['email'])
    
    session.clear()
    return redirect(url_for('login'))

@app.route('/lights')
@login_required
def lights_control():
    return render_template('lights_control.html')

@app.route('/lights/on', methods=['GET'])
@login_required
def turn_on_lights():
    try:
        lifx.set_power_all_lights("on")
        return jsonify({'message': 'Lights turned on successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/lights/off', methods=['GET']) 
@login_required
def turn_off_lights():
    try:
        lifx.set_power_all_lights("off")
        return jsonify({'message': 'Lights turned off successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)