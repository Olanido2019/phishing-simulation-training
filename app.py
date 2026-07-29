from flask import Flask, render_template, request, jsonify
import os
import smtplib
import ssl
import requests
from email.message import EmailMessage

app = Flask(__name__)


# --------------------------------------------------
# Environment variables
# --------------------------------------------------

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "").strip()

SENDER_PASSWORD = (
    os.environ.get("SENDER_PASSWORD", "")
    .replace(" ", "")
    .strip()
)

GOOGLE_SCRIPT_URL = os.environ.get(
    "GOOGLE_SCRIPT_URL",
    ""
).strip()

GOOGLE_LOG_SECRET = os.environ.get(
    "GOOGLE_LOG_SECRET",
    ""
).strip()


# --------------------------------------------------
# Website routes
# --------------------------------------------------

@app.route("/")
@app.route("/index.html")
def home():
    return render_template("index.html")


@app.route("/verify")
@app.route("/verify.html")
def verify():
    return render_template("verify.html")


@app.route("/training")
@app.route("/training.html")
def training():
    return render_template("training.html")


@app.route("/quiz")
@app.route("/quiz.html")
def quiz():
    return render_template("quiz.html")


@app.route("/reveal")
@app.route("/reveal.html")
def reveal():
    return render_template("reveal.html")


@app.route("/cancel")
@app.route("/cancel.html")
def cancel():
    return render_template("cancel.html")


@app.route("/otp")
@app.route("/otp.html")
@app.route("/OTP.html")
def otp():
    return render_template("OTP.html")


# --------------------------------------------------
# Send verification code
# --------------------------------------------------

@app.post("/api/send-code")
def send_code():
    data = request.get_json(silent=True) or {}

    target_email = str(data.get("email", "")).strip().lower()
    pin = str(data.get("pin", "")).strip()

    if not target_email or "@" not in target_email:
        return jsonify({
            "status": "error",
            "message": "A valid email address is required."
        }), 400

    if not pin.isdigit() or len(pin) != 4:
        return jsonify({
            "status": "error",
            "message": "The verification code must contain four digits."
        }), 400

    if not SENDER_EMAIL or not SENDER_PASSWORD:
        return jsonify({
            "status": "error",
            "message": "Email credentials are not configured."
        }), 500

    try:
        msg = EmailMessage()

        msg.set_content(
            f"Your secure verification code is:\n\n"
            f"{pin}\n\n"
            "Please enter this code on the verification page."
        )

        msg["Subject"] = "Security Verification Code"
        msg["From"] = SENDER_EMAIL
        msg["To"] = target_email

        smtp_context = ssl.create_default_context()

        with smtplib.SMTP(
            "smtp.gmail.com",
            587,
            timeout=30
        ) as server:

            server.ehlo()
            server.starttls(context=smtp_context)
            server.ehlo()

            server.login(
                SENDER_EMAIL,
                SENDER_PASSWORD,
                initial_response_ok=True
            )

            server.send_message(msg)

        print(f"[+] Verification code sent to {target_email}")

        return jsonify({
            "status": "success"
        })

    except Exception as error:
        print(f"[-] Email error: {error}")

        return jsonify({
            "status": "error",
            "message": "The verification code could not be sent."
        }), 500


# --------------------------------------------------
# Record Yes/No verification choice
# --------------------------------------------------

@app.post("/api/log-choice")
def log_choice():
    data = request.get_json(silent=True) or {}

    email = str(data.get("email", "")).strip().lower()
    login_time = str(data.get("loginTime", "")).strip()
    choice = str(data.get("choice", "")).strip()

    allowed_choices = {
        "Yes, it is me",
        "No, it is not me"
    }

    if not email or "@" not in email:
        return jsonify({
            "status": "error",
            "message": "A valid email address is required."
        }), 400

    if choice not in allowed_choices:
        return jsonify({
            "status": "error",
            "message": "Invalid verification choice."
        }), 400

    if not GOOGLE_SCRIPT_URL or not GOOGLE_LOG_SECRET:
        return jsonify({
            "status": "error",
            "message": "Google Sheets logging is not configured."
        }), 500

    payload = {
        "action": "verification_choice",
        "secret": GOOGLE_LOG_SECRET,
        "email": email,
        "loginTime": login_time,
        "choice": choice
    }

    try:
        response = requests.post(
            GOOGLE_SCRIPT_URL,
            json=payload,
            timeout=15
        )

        response.raise_for_status()

        try:
            result = response.json()

        except ValueError:
            print(
                "[-] Google Apps Script returned non-JSON:",
                response.text[:500]
            )

            return jsonify({
                "status": "error",
                "message": "Google Sheets returned an invalid response."
            }), 502

        if result.get("status") != "success":
            raise RuntimeError(
                result.get(
                    "message",
                    "Google Sheets rejected the entry."
                )
            )

        print(f"[+] Recorded '{choice}' for {email}")

        return jsonify({
            "status": "success"
        })

    except Exception as error:
        print(f"[-] Google Sheets logging error: {error}")

        return jsonify({
            "status": "error",
            "message": "The verification choice could not be recorded."
        }), 502


# --------------------------------------------------
# Test route
# --------------------------------------------------

@app.route("/test")
def test():
    return "Flask is working!"


# --------------------------------------------------
# Local development server
# --------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )