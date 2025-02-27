from flask import Flask, render_template, request, redirect,url_for,jsonify
from lifxlan import LifxLAN
from connect import connect_to_dynamodb, add_user, login_user,logout_user
from flask import session
import os
from datetime import timedelta
from functools import wraps
num_lights = None
lifx = LifxLAN(num_lights)
lifx.get_power_all_lights()

app = Flask(__name__)
app.secret_key = os.urandom(24)
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
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        db = connect_to_dynamodb()
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500
            
        users_table = db.Table('Users')

        token = login_user(users_table, email, password)
        if token:
            # Stocker le token et l'email dans la session
            session.permanent = True
            session['token'] = token
            session['email'] = email
            return redirect(url_for('index')) 
             
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if not all([ email, password, confirm_password]):
            return jsonify({'error': 'Tous les champs sont requis'}), 400
            
        if password != confirm_password:
            return jsonify({'error': 'Les mots de passe ne correspondent pas'}), 400
            
        db = connect_to_dynamodb()
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500
            
        users_table = db.Table('Users')
        
        if add_user(users_table, email, password):
             return redirect(url_for('login'))    
    return render_template('register.html')

@app.route('/logout')
def logout():
    if 'email' in session:
        db = connect_to_dynamodb()
        if db:
            users_table = db.Table('Users')
            logout_user(users_table, session['email'])
    
    # Nettoyer la session
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


@app.route('/search', methods=['GET'])
def search():
    try:
        query = request.args.get('q')
        if not query:
            return jsonify({'error': 'q parameter is required'}), 400
            
        return jsonify({'query': query})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
