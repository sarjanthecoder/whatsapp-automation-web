from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import threading
import os

app = Flask(__name__)

# Global driver variable
driver = None

# -----------------------------
# INITIALIZE SELENIUM
# -----------------------------
def initialize_driver():
    global driver
    
    if driver is not None:
        return driver
    
    chrome_options = webdriver.ChromeOptions()
    
    # Keep WhatsApp login session
    chrome_options.add_argument("--user-data-dir=./User_Data")
    chrome_options.add_argument("--profile-directory=Default")
    
    # Performance options
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Headless mode (optional - comment out to see browser)
    # chrome_options.add_argument("--headless")
    
    service = Service()
    
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get("https://web.whatsapp.com")
        print("✅ WhatsApp Web opened successfully!")
        print("📌 Please scan QR code if not logged in...")
        
        # Wait for WhatsApp to load
        time.sleep(15)
        
        return driver
    except Exception as e:
        print(f"❌ Error initializing driver: {e}")
        return None


# -----------------------------
# SEND MESSAGES FUNCTION
# -----------------------------
def send_whatsapp_messages(contact, message, count):
    global driver
    
    try:
        if driver is None:
            raise Exception("Driver not initialized")
        
        # Wait for search box to be available
        wait = WebDriverWait(driver, 20)
        
        # Find and click search box
        search_box = wait.until(
            EC.presence_of_element_located((
                By.XPATH,
                '//div[@contenteditable="true" and @data-tab="3"]'
            ))
        )
        
        search_box.clear()
        search_box.send_keys(contact)
        time.sleep(2)
        
        # Click on the contact
        try:
            user = wait.until(
                EC.presence_of_element_located((
                    By.XPATH,
                    f'//span[@title="{contact}"]'
                ))
            )
            user.click()
        except:
            # Try alternative method if exact match fails
            user = wait.until(
                EC.presence_of_element_located((
                    By.XPATH,
                    '//div[@class="_ak8l"]//span[@dir="auto"]'
                ))
            )
            user.click()
        
        time.sleep(2)
        
        # Find message input box
        msg_box = wait.until(
            EC.presence_of_element_located((
                By.XPATH,
                '//div[@contenteditable="true" and @data-tab="10"]'
            ))
        )
        
        # Send messages
        success_count = 0
        for i in range(count):
            try:
                msg_box.send_keys(message)
                msg_box.send_keys(Keys.ENTER)
                success_count += 1
                time.sleep(0.5)  # Small delay between messages
            except Exception as e:
                print(f"❌ Error sending message {i+1}: {e}")
                break
        
        print(f"✅ Successfully sent {success_count}/{count} messages to {contact}")
        return success_count
        
    except Exception as err:
        print(f"❌ ERROR in send_whatsapp_messages: {err}")
        raise err


# -----------------------------
# ROUTES
# -----------------------------
@app.route("/")
def index():
    """Serve the main HTML page"""
    return render_template("index.html")


@app.route("/send", methods=["POST"])
def send():
    """Handle message sending requests"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        contact = data.get("contact", "").strip()
        message = data.get("message", "").strip()
        count = int(data.get("count", 1))
        
        # Validation
        if not contact:
            return jsonify({"error": "Contact name/number is required"}), 400
        
        if not message:
            return jsonify({"error": "Message content is required"}), 400
        
        if count <= 0 or count > 100:
            return jsonify({"error": "Message count must be between 1 and 100"}), 400
        
        # Initialize driver if not already done
        global driver
        if driver is None:
            driver = initialize_driver()
            if driver is None:
                return jsonify({"error": "Failed to initialize WhatsApp Web"}), 500
        
        # Send messages in background thread
        def send_in_thread():
            try:
                send_whatsapp_messages(contact, message, count)
            except Exception as e:
                print(f"❌ Thread error: {e}")
        
        thread = threading.Thread(target=send_in_thread, daemon=True)
        thread.start()
        
        return jsonify({
            "message": f"Sending {count} message(s) to {contact}... 🚀"
        }), 200
        
    except ValueError:
        return jsonify({"error": "Invalid count value"}), 400
    except Exception as e:
        print(f"❌ Error in /send route: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/status")
def status():
    """Check if WhatsApp Web is connected"""
    global driver
    try:
        if driver is None:
            return jsonify({"status": "disconnected", "message": "Driver not initialized"})
        
        # Check if WhatsApp is loaded
        driver.find_element(By.XPATH, '//div[@contenteditable="true"]')
        return jsonify({"status": "connected", "message": "WhatsApp Web is ready"})
    except:
        return jsonify({"status": "disconnected", "message": "WhatsApp Web not loaded"})


# -----------------------------
# CLEANUP
# -----------------------------
def cleanup():
    """Clean up resources on shutdown"""
    global driver
    if driver:
        try:
            driver.quit()
            print("✅ Driver closed successfully")
        except:
            pass


# Register cleanup function
import atexit
atexit.register(cleanup)


# -----------------------------
# RUN SERVER
# -----------------------------
if __name__ == "__main__":
    # Initialize driver on startup
    print("🚀 Starting WhatsApp Automation Server...")
    initialize_driver()
    
    # Run Flask app
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        use_reloader=False  # Important: prevents driver duplication
    )
  # Python dependencies
