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
import secrets
from time import time
from email.mime.text import MIMEText

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Security Configurations
_secret_key = os.getenv("SECRET_KEY")
if not _secret_key:
    _secret_key = secrets.token_hex(32)
    app.logger.warning("SECRET_KEY is not set. Using an ephemeral key; sessions reset on restart.")

app.config['SECRET_KEY'] = _secret_key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 1800

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)

# Brute-force protection (in-memory; swap for Redis/DB in production)
RATE_WINDOW = 300      # seconds
RATE_MAX_ATTEMPTS = 5  # failures allowed per window
RATE_LOCKOUT = 900     # seconds
_rate_limits = {}


def _rate_record(key, now):
    rec = _rate_limits.get(key)
    if rec and now - rec['window_start'] > RATE_WINDOW:
        _rate_limits.pop(key, None)
        return None
    return rec


def is_rate_limited(key):
    rec = _rate_record(key, time())
    if not rec:
        return False
    if rec['locked_until'] > time():
        return True
    return rec['attempts'] >= RATE_MAX_ATTEMPTS


def register_failure(key):
    now = time()
    rec = _rate_record(key, now)
    if not rec:
        rec = {'attempts': 0, 'window_start': now, 'locked_until': 0}
        _rate_limits[key] = rec
    rec['attempts'] += 1
    if rec['attempts'] >= RATE_MAX_ATTEMPTS:
        rec['locked_until'] = now + RATE_LOCKOUT


def clear_failures(key):
    _rate_limits.pop(key, None)


def client_key(kind, identifier=''):
    return f"{kind}:{request.remote_addr or 'unknown'}:{identifier}"


# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    otp_secret = db.Column(db.String(32), nullable=False)


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

    if not sender_email or not sender_password:
        app.logger.error("EMAIL_ADDRESS / EMAIL_PASSWORD not configured; OTP email not sent.")
        return False

    msg = MIMEText(f"Your OTP code is: {otp}")
    msg['Subject'] = "Your Login OTP"
    msg['From'] = sender_email
    msg['To'] = receiver_email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True

    except Exception as e:
        app.logger.error("Failed to send OTP email: %s", e)
        return False


# Home
@app.route('/')
def index():
    return render_template('index.html')


# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':

        username = (request.form.get('username') or '').strip()
        email = (request.form.get('email') or '').strip()
        password = request.form.get('password') or ''

        # Validation
        if not username or not email or not password:
            flash("All fields are required!", "danger")
            return redirect(url_for('register'))

        if len(username) > 100:
            flash("Username must be 100 characters or fewer.", "danger")
            return redirect(url_for('register'))

        # Email validation (no live DNS lookup)
        try:
            email = validate_email(email, check_deliverability=False).email
        except EmailNotValidError:
            flash("Invalid email address!", "danger")
            return redirect(url_for('register'))

        if len(email) > 150:
            flash("Email address is too long.", "danger")
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

        email = (request.form.get('email') or '').strip()
        password = request.form.get('password') or ''

        rate_key = client_key('login', email)
        if is_rate_limited(rate_key):
            flash("Too many attempts. Try again in 15 minutes.", "danger")
            return redirect(url_for('login'))

        user = User.query.filter_by(email=email).first()

        if user and password and bcrypt.check_password_hash(user.password, password):

            clear_failures(rate_key)

            # Generate OTP
            totp = pyotp.TOTP(user.otp_secret)
            otp = totp.now()

            if not send_otp_email(user.email, otp):
                flash("Could not send OTP email. Please try again later.", "danger")
                return redirect(url_for('login'))

            session['temp_user_id'] = user.id

            flash("OTP sent to your email.", "info")
            return redirect(url_for('verify_otp'))

        else:
            register_failure(rate_key)
            flash("Invalid credentials!", "danger")

    return render_template('login.html')


# Verify OTP
@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():

    if 'temp_user_id' not in session:
        return redirect(url_for('login'))

    user = db.session.get(User, session['temp_user_id'])

    if user is None:
        session.pop('temp_user_id', None)
        return redirect(url_for('login'))

    if request.method == 'POST':

        otp_input = (request.form.get('otp') or '').strip()

        rate_key = client_key('otp', str(user.id))
        if is_rate_limited(rate_key):
            session.pop('temp_user_id', None)
            clear_failures(rate_key)
            flash("Too many failed OTP attempts. Please log in again.", "danger")
            return redirect(url_for('login'))

        totp = pyotp.TOTP(user.otp_secret)

        # Allow small time delay
        if otp_input and totp.verify(otp_input, valid_window=2):

            clear_failures(rate_key)

            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username
            session.permanent = True

            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))

        else:
            register_failure(rate_key)
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
    app.run(
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=int(os.getenv("FLASK_PORT", "5000")),
    )
