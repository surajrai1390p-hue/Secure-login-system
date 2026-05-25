from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from email_validator import validate_email, EmailNotValidError
import pyotp
import smtplib
import os
import re
from email.mime.text import MIMEText

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Security Configurations
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = 1800

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    otp_secret = db.Column(db.String(20), nullable=False)

# Create database
with app.app_context():
    db.create_all()

# Password Validation
def validate_password(password):
    if len(password) < 8:
        return False

    if not re.search(r"[A-Z]", password):
        return False

    if not re.search(r"[a-z]", password):
        return False

    if not re.search(r"[0-9]", password):
        return False

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False

    return True

# Send OTP Email
def send_otp_email(receiver_email, otp):
    sender_email = os.getenv("EMAIL_ADDRESS")
    sender_password = os.getenv("EMAIL_PASSWORD")

    subject = "Your Login OTP"
    body = f"Your OTP code is: {otp}"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

    except Exception as e:
        print("Email Error:", e)

# Home
@app.route('/')
def index():
    return render_template('index.html')

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':

        username = request.form.get('username').strip()
        email = request.form.get('email').strip()
        password = request.form.get('password')

        # Validation
        if not username or not email or not password:
            flash("All fields are required!", "danger")
            return redirect(url_for('register'))

        # Email validation
        try:
            validate_email(email)
        except EmailNotValidError:
            flash("Invalid email address!", "danger")
            return redirect(url_for('register'))

        # Password validation
        if not validate_password(password):
            flash(
                "Password must contain uppercase, lowercase, number, special character and be 8+ characters.",
                "danger"
            )
            return redirect(url_for('register'))

        # Existing user check
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            flash("Username or Email already exists!", "danger")
            return redirect(url_for('register'))

        # Hash password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Generate OTP Secret
        otp_secret = pyotp.random_base32()

        # Save user
        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            otp_secret=otp_secret
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Registration Successful!", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        email = request.form.get('email').strip()
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):

            # Generate OTP
            totp = pyotp.TOTP(user.otp_secret)
            otp = totp.now()

            send_otp_email(user.email, otp)

            session['temp_user_id'] = user.id

            flash("OTP sent to your email.", "info")
            return redirect(url_for('verify_otp'))

        else:
            flash("Invalid credentials!", "danger")

    return render_template('login.html')

# Verify OTP
@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():

    if 'temp_user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['temp_user_id'])

    if request.method == 'POST':

        otp_input = request.form.get('otp')

        totp = pyotp.TOTP(user.otp_secret)

        # Allow small time delay
        if totp.verify(otp_input, valid_window=2):

            session.pop('temp_user_id', None)

            session['user_id'] = user.id
            session['username'] = user.username

            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))

        else:
            flash("Invalid or Expired OTP!", "danger")

    return render_template('verify_otp.html')

# Dashboard
@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template(
        'dashboard.html',
        username=session.get('username')
    )

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for('login'))

# Run
if __name__ == '__main__':
    app.run(debug=True)