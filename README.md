# 🔐 Secure Login System

A professional and secure login authentication system built using **Flask**, **SQLite**, **bcrypt**, and **Email OTP Two-Factor Authentication (2FA)**.

This project demonstrates real-world authentication security practices including password hashing, session management, SQL injection protection, CSRF protection, and email-based OTP verification.

---

# 🚀 Features

✅ User Registration  
✅ Secure Login System  
✅ bcrypt Password Hashing  
✅ SQL Injection Protection using SQLAlchemy ORM  
✅ Session Management  
✅ Logout Functionality  
✅ Email OTP Verification (2FA)  
✅ Strong Password Validation  
✅ CSRF Protection  
✅ Secure Authentication Flow  
✅ Responsive UI Design  
✅ Real-World Security Practices  

---

# 🛡 Security Features

| Feature | Purpose |
|---|---|
| bcrypt Hashing | Secure password storage |
| SQLAlchemy ORM | Prevent SQL Injection |
| CSRF Protection | Prevent CSRF attacks |
| Session Handling | Secure user sessions |
| OTP Verification | Two-Factor Authentication |
| Input Validation | Prevent invalid data |
| Rate Limiting | Blocks brute-force login attempts |
| Account Lockout | Locks an IP/email after repeated failures |

---

# 🖥 Technologies Used

- Python
- Flask
- SQLite
- Flask-Bcrypt
- Flask-WTF
- SQLAlchemy
- PyOTP
- HTML
- CSS

---

# 📂 Project Structure

```plaintext
secure-login-system/
│
├── app.py
├── requirements.txt
├── .gitignore
├── .env              (you create this; never committed)
│
├── instance/
│   └── database.db   (auto-created on first run)
│
├── templates/
│   ├── index.html
│   ├── register.html
│   ├── login.html
│   ├── verify_otp.html
│   ├── dashboard.html
│
├── static/
│   └── style.css
```

---

# ⚙ Installation

## 1️⃣ Clone Repository

```bash
git clone https://github.com/surajrai1390p-hue/Secure-login-system.git
```

---

## 2️⃣ Open Project Folder

```bash
cd Secure-login-system
```

---

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🔑 Configure Environment Variables

Create a `.env` file in the project root folder.

Add:

```env
SECRET_KEY=replace_with_a_long_random_string
EMAIL_ADDRESS=yourgmail@gmail.com
EMAIL_PASSWORD=yourapppassword
```

Optional:

```env
FLASK_DEBUG=1        # set to 1 only for local development
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
SESSION_COOKIE_SECURE=1   # set to 1 when serving over HTTPS
```

⚠ `.env` is listed in `.gitignore` and must **never** be committed. Generate a strong `SECRET_KEY` with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

# 📧 Gmail App Password Setup

Enable Google App Passwords:

https://myaccount.google.com/apppasswords

Generate App Password and paste it inside `.env`.

⚠ Do NOT use your normal Gmail password.

---

# ▶ Run Project

```bash
python app.py
```

Enable debug mode locally (never in production):

```bash
set FLASK_DEBUG=1     # Windows
python app.py
```

---

# 🌐 Open In Browser

```plaintext
http://127.0.0.1:5000
```

---

# 🔐 Authentication Flow

## User Registration

- User creates account
- Password gets hashed using bcrypt
- User data stored securely in database

---

## Login

- User enters email and password
- Password verified securely

---

## OTP Verification

- OTP sent to registered email
- User verifies OTP before login access

---

## Dashboard Access

- Secure session created
- User enters protected dashboard

---

## Logout

- Session destroyed securely

---

# 🧪 Example Strong Password

```plaintext
Suraj@123
```

---

# 📦 requirements.txt

```txt
Flask>=3.1.0,<4
Flask-SQLAlchemy>=3.1.1,<4
Flask-Bcrypt>=1.0.1,<2
Flask-WTF>=1.2.2,<2
email-validator>=2.3.0,<3
pyotp>=2.9.0,<3
python-dotenv>=1.0.1,<2
```

---

# 📸 Screenshots

## Home Page

- Register
- Login

## Registration Page

- Username
- Email
- Password Validation

## Login Page

- Secure Authentication

## OTP Verification

- Email-based OTP Authentication

## Dashboard

- Secure Logged-In User Area

---

# 🚀 Future Improvements

➕ Password Reset Feature  
➕ Google OAuth Login  
➕ JWT Authentication  
➕ PostgreSQL Database  
➕ Docker Deployment  
➕ HTTPS SSL Security  
➕ Admin Panel  
➕ Persistent rate limiting (Redis/DB instead of in-memory)

---

# 🎯 Learning Outcomes

This project helps understand:

- Authentication Systems
- Password Security
- Session Management
- Two-Factor Authentication
- Flask Web Development
- Web Application Security
- SQL Injection Prevention

---

# 👨‍💻 Author

## Suraj Rai

GitHub Repository:

https://github.com/surajrai1390p-hue/Secure-login-system

---

# ⭐ Support

If you like this project, give it a ⭐ on GitHub.
