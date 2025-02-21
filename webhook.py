from flask import Flask, request, jsonify, render_template
import threading
from main import process_leads

app = Flask(__name__)

def process_leads_async():
    process_leads(1501858, 'Campaign_Leads.csv')

@app.route('/')
def dashboard():
    return render_template('index.html')

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    if request.method == 'POST':
        data = request.json  # Extract JSON payload
        
        # Start the process in a new thread
        thread = threading.Thread(target=process_leads_async)
        thread.start()

        return jsonify({"message": "Webhook received, processing started"}), 200
    return jsonify({"message": "Send a POST request"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
