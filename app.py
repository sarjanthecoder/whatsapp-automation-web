from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import threading

app = Flask(__name__)

# -----------------------------
# START SELENIUM (ONCE)
# -----------------------------
chrome_options = webdriver.ChromeOptions()
# Commented out user-data-dir to avoid conflicts on first run
# chrome_options.add_argument("--user-data-dir=./User_Data")   # keep WhatsApp login
# chrome_options.add_argument("--profile-directory=Default")
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

# For Python 3.13 + new Selenium:
service = Service(ChromeDriverManager().install())

driver = webdriver.Chrome(service=service, options=chrome_options)
driver.get("https://web.whatsapp.com")
print("📌 Scan QR Code if not logged in...")
time.sleep(10)


# -----------------------------
# SEND MESSAGES FUNCTION
# -----------------------------
def send_whatsapp_messages(contact, message, count):
    try:
        # Search bar
        search_box = driver.find_element(
            By.XPATH,
            '//div[@contenteditable="true" and @data-tab="3"]'
        )
        search_box.clear()
        search_box.send_keys(contact)
        time.sleep(1)

        # Click contact
        user = driver.find_element(
            By.XPATH,
            f'//span[@title="{contact}"]'
        )
        user.click()
        time.sleep(1)

        # Message box
        msg_box = driver.find_element(
            By.XPATH,
            '//div[@contenteditable="true" and @data-tab="10"]'
        )

        # Loop sending
        for i in range(count):
            msg_box.send_keys(message + Keys.ENTER)
            time.sleep(0.05)

    except Exception as err:
        print("❌ ERROR sending messages:", err)
        raise err


# -----------------------------
# ROUTES
# -----------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/send", methods=["POST"])
def send():
    try:
        data = request.get_json() or request.form

        contact = data.get("contact", "").strip()
        message = data.get("message", "").strip()
        count = int(data.get("count", "1"))

        if not contact or not message or count <= 0:
            return jsonify({"error": "Invalid input"}), 400

        # Send messages in a separate thread (fast)
        threading.Thread(
            target=send_whatsapp_messages,
            args=(contact, message, count),
            daemon=True
        ).start()

        return jsonify({"message": "Messages sending… 🚀"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------
# RUN SERVER
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
