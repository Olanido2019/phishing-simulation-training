from flask import Flask, render_template, request, jsonify
import os
import smtplib
from email.message import EmailMessage

app = Flask(__name__)

# Read email credentials from environment variables
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")



# Home page
@app.route("/")
def home():
    return render_template("index.html")


# Website page routes
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


# Email API
@app.post("/api/send-code")
def send_code():
    data = request.get_json()

    target_email = data.get("email")
    pin = data.get("pin")

    if not target_email or not pin:
        return jsonify({
            "status": "error",
            "message": "Missing email or PIN."
        }), 400

    try:
        msg = EmailMessage()
        msg.set_content(
            f"Your secure verification code is:\n\n"
            f"{pin}\n\n"
            "Please enter this on the verification page."
        )

        msg["Subject"] = "Security Verification Code"
        msg["From"] = SENDER_EMAIL
        msg["To"] = target_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        return jsonify({"status": "success"})

    except Exception as e:
        print(e)

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/test")
def test():
    return "Flask is working!"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )