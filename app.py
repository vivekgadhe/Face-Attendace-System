from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_session import Session  # Import Flask-Session
import os
import base64
import numpy as np
import cv2
import sqlite3
import datetime
import face_recognition

app = Flask(__name__)

# Configure server-side session storage
app.config["SESSION_TYPE"] = "filesystem"  # Store sessions in files
app.config["SESSION_PERMANENT"] = False
app.config["SECRET_KEY"] = "your_secret_key_here"  # Change this to a strong, random key
Session(app)  # Initialize session management

# Load known faces from "static/images" folder
known_faces = []
known_names = []

for filename in os.listdir("static/images"):
    if filename.endswith(".jpg") or filename.endswith(".png"):
        image_path = os.path.join("static/images", filename)
        image = face_recognition.load_image_file(image_path)
        encoding = face_recognition.face_encodings(image)

        if encoding:  # Make sure at least one face encoding exists
            known_faces.append(encoding[0])
            known_names.append(filename.split('.')[0])  # Use filename as name

print(f"✅ Loaded {len(known_faces)} known faces!")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Simple admin authentication
        if username == "vivek" and password == "12345":
            session["admin"] = True  # Store login state in session
            print("✅ Admin logged in. Session Data:", session)  # Debugging
            return redirect(url_for("home"))  # Redirect to home page

        print("❌ Invalid login attempt")
        return render_template('login.html', error="Invalid credentials!")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop("admin", None)  # Remove admin session
    return redirect(url_for("login"))  # Redirect to login page

@app.route('/')
def home():
    print("🔍 Checking session data:", session)  # Debugging

    if "admin" not in session:
        print("🔒 No admin session found! Redirecting to login...")
        return redirect(url_for("login"))

    print("✅ Admin session found! Rendering home page.")

    with sqlite3.connect(r"C:\face recognition system\attendance.db") as conn:
        c = conn.cursor()
        # Fetch columns explicitly and order by date and time
        c.execute("SELECT id, name, date, time FROM attendance ORDER BY date DESC, time DESC")
        records = c.fetchall()

    print("📊 Attendance Records (Debugging Output):", records)  # Debugging output in console

    return render_template('index.html', records=records)



@app.route('/recognize', methods=['POST'])
def recognize_face():
    try:
        data = request.get_json()
        if not data or "image" not in data:
            return jsonify({"error": "Missing 'image' field in request"}), 400

        base64_string = data["image"].replace("data:image/jpeg;base64,", "").replace("data:image/png;base64,", "")
        image_data = base64.b64decode(base64_string)
        np_arr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({"error": "Invalid image data"}), 400

        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)

        with sqlite3.connect(r"C:\face recognition system\attendance.db", check_same_thread=False) as conn:
            c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS attendance (name TEXT, date TEXT, time TEXT)")

            for encoding in face_encodings:
                matches = face_recognition.compare_faces(known_faces, encoding)
                name = "Unknown"

                if True in matches:
                    match_index = matches.index(True)
                    name = known_names[match_index]

                    now = datetime.datetime.now()
                    c.execute("INSERT INTO attendance (name, date, time) VALUES (?, ?, ?)", 
                              (name, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")))
                    conn.commit()
                    return jsonify({"message": f"Attendance marked for {name}!"})

        return jsonify({"message": "Face not recognized!"})

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/attendance')
def attendance():
    if "admin" not in session:
        return redirect(url_for("login"))

    with sqlite3.connect(r"C:\face recognition system\attendance.db") as conn:
        conn.row_factory = sqlite3.Row  # Allows access via column names
        c = conn.cursor()
        c.execute("SELECT * FROM attendance")
        records = c.fetchall()

    print(f"📊 Attendance Data Retrieved: {records}")  # Debugging output

    return render_template('attendance.html', attendance_data=records)  # Updated variable name


if __name__ == '__main__':
    app.run(debug=True)



