from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import threading

app = Flask(__name__)

# Global driver
driver = None

# Initialize Selenium
def initialize_driver():
    global driver
    
    if driver is not None:
        return driver
    
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--user-data-dir=./User_Data")
    chrome_options.add_argument("--profile-directory=Default")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-notification")
    
    service = Service()
    
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get("https://web.whatsapp.com")
        print("✅ WhatsApp Web opened! Scan QR if needed...")
        time.sleep(15)
        return driver
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# Send messages
def send_whatsapp_messages(contact, message, count):
    global driver
    
    try:
        wait = WebDriverWait(driver, 20)
        
        # Search box
        search_box = wait.until(
            EC.presence_of_element_located((
                By.XPATH,
                '//div[@contenteditable="true" and @data-tab="3"]'
            ))
        )
        search_box.clear()
        search_box.send_keys(contact)
        time.sleep(2)
        
        # Click contact
        user = wait.until(
            EC.presence_of_element_located((
                By.XPATH,
                f'//span[@title="{contact}"]'
            ))
        )
        user.click()
        time.sleep(2)
        
        # Message box
        msg_box = wait.until(
            EC.presence_of_element_located((
                By.XPATH,
                '//div[@contenteditable="true" and @data-tab="10"]'
            ))
        )
        
        # Send messages
        for i in range(count):
            msg_box.send_keys(message)
            msg_box.send_keys(Keys.ENTER)
            time.sleep(0.5)
        
        print(f"✅ Sent {count} messages to {contact}")
        
    except Exception as err:
        print(f"❌ Error: {err}")
        raise err

# Routes
@app.route("/")
def index():
    """Serve index.html from templates folder"""
    return render_template("index.html")

@app.route("/send", methods=["POST"])
def send():
    try:
        data = request.get_json()
        
        contact = data.get("contact", "").strip()
        message = data.get("message", "").strip()
        count = int(data.get("count", 1))
        
        if not contact or not message or count <= 0:
            return jsonify({"error": "Invalid input"}), 400
        
        global driver
        if driver is None:
            driver = initialize_driver()
            if driver is None:
                return jsonify({"error": "Failed to init WhatsApp"}), 500
        
        # Send in background
        threading.Thread(
            target=send_whatsapp_messages,
            args=(contact, message, count),
            daemon=True
        ).start()
        
        return jsonify({"message": f"Sending {count} messages... 🚀"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Cleanup
def cleanup():
    global driver
    if driver:
        try:
            driver.quit()
        except:
            pass

import atexit
atexit.register(cleanup)

# Run
if __name__ == "__main__":
    print("🚀 Starting server...")
    initialize_driver()
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)

