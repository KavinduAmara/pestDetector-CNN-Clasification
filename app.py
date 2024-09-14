import os
import sqlite3, requests
from flask import Flask, request, render_template, redirect, url_for, session
from werkzeug.utils import secure_filename
from ultralytics import YOLO
from admin import admin_bp

app = Flask(__name__)

# Folder to store uploaded files
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.secret_key = 'f3d6d2b5c4b8e9d8f4c7a6b1a7c9e2f5'

# Ensure the folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Load YOLOv8 model (ensure 'last.pt' is the path to your trained model)
model = YOLO('last.pt')

def get_db_connection():
    conn = sqlite3.connect('pest.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/test')
def test():
    return "Test route is working"

def get_weather_data(latitude, longitude):
    api_url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json()
    else:
        return None


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_type = request.form['login_type']
        email = request.form['email']
        password = request.form['password']

        if login_type == 'user':
            conn = sqlite3.connect('pest.db')
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute('SELECT * FROM users WHERE email = ? AND password_hash = ?', (email, password))
            user = cur.fetchone()
            conn.close()

            if user:
                session['user_id'] = user['id']
                session['user_type'] = 'user'
                return redirect(url_for('index'))
            else:
                return 'Invalid email or password for user login'

        elif login_type == 'admin':
            if email == 'kavidu@gmail.com' and password == '123456':
                session['user_id'] = None
                session['user_type'] = 'admin'
                return render_template('admin/index.html')
            else:
                return 'Invalid email or password for admin login'

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_type', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'user_id' in session:
        user_id = session['user_id']
        user_type = session.get('user_type')

        # Connect to the database and fetch user details
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cur.fetchone()
        conn.close()

        if user:
            user_info = {
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
                # Add more fields if needed
            }
            return render_template('index.html', user_type=user_type, user_info=user_info)
        
        else:
            return redirect(url_for('login'))

    return redirect(url_for('login'))


# Your existing routes
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return 'No file uploaded'
    
    file = request.files['file']
    if file.filename == '':
        return 'No file selected'
    
    if file:
        filename = secure_filename(file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(image_path)

        results = model(image_path)  # Run inference with YOLOv8

        detections = results[0].boxes if hasattr(results[0], 'boxes') else []
        classes = results[0].names if hasattr(results[0], 'names') else []

        # Fetch weather data
        latitude = 52.52
        longitude = 13.41
        weather_data = get_weather_data(latitude, longitude)
        
        current_weather = weather_data.get('current', {}) if weather_data else {}
        hourly_weather = weather_data.get('hourly', {}) if weather_data else {}

        hourly_forecast = []
        if hourly_weather:
            for i in range(len(hourly_weather['time'])):
                hourly_forecast.append({
                    'time': hourly_weather['time'][i],
                    'temperature': hourly_weather['temperature_2m'][i],
                    'humidity': hourly_weather['relative_humidity_2m'][i],
                    'wind_speed': hourly_weather['wind_speed_10m'][i]
                })

        detection_results = []
        
        conn = sqlite3.connect('pest.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        for box in detections:
            class_id = int(box.cls[0]) if hasattr(box, 'cls') else -1
            confidence = box.conf[0].item() if hasattr(box, 'conf') else 0.0
            bbox = box.xyxy[0].tolist() if hasattr(box, 'xyxy') else []

            pest_name = 'Unknown'
            pest_info = None
            recommendations = []
            
            if class_id >= 0 and class_id < len(classes):
                pest_name = classes[class_id]
                
                cur.execute('SELECT * FROM pests WHERE name = ?', (pest_name,))
                pest_info_row = cur.fetchone()
                
                if pest_info_row:
                    pest_info = {
                        'name': pest_info_row['name'],
                        'description': pest_info_row['description'],
                        'image_url': pest_info_row['image_url'],
                        'control_methods': pest_info_row['control_methods']
                    }

                    cur.execute('SELECT * FROM recommendations WHERE pest_id = ?', (pest_info_row['id'],))
                    recommendations = cur.fetchall()
            
            detection_results.append({
                'class': pest_name,
                'confidence': round(confidence, 2),
                'bbox': bbox,
                'pest_info': pest_info,
                'recommendations': recommendations
            })

        conn.close()

        return render_template('result.html', image_path=image_path, detections=detection_results, current_weather=current_weather, hourly_forecast=hourly_forecast)


@app.route('/chat', methods=['GET'])
def chat():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Fetch chat messages
    conn = sqlite3.connect('pest.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute('SELECT c.message, c.created_at, u.username FROM chats c JOIN users u ON c.user_id = u.id ORDER BY c.created_at ASC')
    messages = cur.fetchall()

    conn.close()

    return render_template('chat.html', messages=messages)


@app.route('/chat/send', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    message = request.form['message']
    user_id = session['user_id']

    conn = sqlite3.connect('pest.db')
    cur = conn.cursor()

    cur.execute('INSERT INTO chats (user_id, message) VALUES (?, ?)', (user_id, message))
    conn.commit()
    conn.close()

    return redirect(url_for('chat'))



app.register_blueprint(admin_bp, url_prefix='/admin')

if __name__ == '__main__':
    app.run(debug=True)