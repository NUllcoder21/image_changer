from flask import Flask, render_template, request, flash, redirect, url_for, session
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
import imageio.v2 as imageio  # Correct import for newer versions

import os
import cv2
import numpy as np
from PIL import Image

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'webp', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.secret_key = 'super_secret'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # SQLite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Create database tables
with app.app_context():
    db.create_all()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def processImage(filename, operation):
    print(f"The operation is {operation} and filename is {filename}")
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    newfilename = f"static/{filename.split('.')[0]}"
    
    img = imageio.imread(filepath)
    if img is None:
        flash("Error loading image!")
        return None

    match operation:
        case "cgray":
            imgProcessed = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            newfilename += ".png"
        case "cwebp":
            newfilename += ".webp"
        case "cjpg":
            newfilename += ".jpg"
        case "cpng":
            newfilename += ".png"
        case "cbmp":
            newfilename += ".bmp"
        case "ctiff":
            newfilename += ".tiff"
        case "cresized":
            imgProcessed = cv2.resize(img, (300, 300))
            newfilename += "_resized.png"
        case "rotate":
            imgProcessed = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
            newfilename += "_rotated.png"
        case "flip":
            imgProcessed = cv2.flip(img, 1)
            newfilename += "_flipped.png"
        case "cgif":
            newfilename += ".gif"
            imageio.mimsave(newfilename, [img], duration=0.5)
            return newfilename
        case "cpdf":
            newfilename += ".pdf"
            Image.fromarray(img).save(newfilename, "PDF")
            return newfilename
        case "cheic":
            newfilename += ".heic"
        case "capng":
            newfilename += ".apng"
        case "cico":
            newfilename += ".ico"
        case "craw":
            newfilename += ".raw"
        case "cdng":
            newfilename += ".dng"
        case "cexr":
            newfilename += ".exr"
        case "chdr":
            newfilename += ".hdr"
        case _:
            flash("Invalid operation!")
            return None
    
    imageio.imwrite(newfilename, imgProcessed if 'imgProcessed' in locals() else img)
    return newfilename
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/how")
def how():
    return render_template("how.html")

@app.route("/contact")
def contect():
    return render_template("contact.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already exists. Please log in.")
            return redirect(url_for("login"))
        
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        
        flash("Signup successful! Please log in.")
        return redirect(url_for("login"))
    
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session["user_id"] = user.id
            session["username"] = user.username
            flash("Login successful!")
            return redirect(url_for("home"))
        else:
            flash("Invalid credentials. Please try again.")
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    flash("Logged out successfully.")
    return redirect(url_for("home"))

@app.route("/edit", methods=["GET", "POST"])
def edit():
    if "user_id" not in session:
        flash("You must sign up or log in first!")
        return redirect(url_for("login"))
    
    if request.method == "POST":
        operation = request.form.get("operation")
        
        if 'file' not in request.files:
            flash('No file part')
            return redirect(url_for("home"))
        
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(url_for("home"))
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            new = processImage(filename, operation)
            if new:
                flash(f"Your image has been processed and is available <a href='/{new}' target=_blank> here </a>", "success")
            return render_template("index.html")

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
