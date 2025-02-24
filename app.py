from flask import Flask, request, jsonify
import threading
from main import process_leads

app = Flask(__name__)

def process_leads_async(campaign_id, lead_email, lead_name):
    process_leads(campaign_id, lead_email, lead_name)

@app.route('/', methods=['POST', 'GET'])
def webhook():
    if request.method == 'POST':
        data = request.json  # Extract JSON payload
        reply_data = {
            'campaign_id': data['campaign_id'],
            'to_email': data['to_email'],
            'to_name': data['to_name'],
            'reply_message': data['reply_message'],
        }
        # print(data)
        # Start the process in a new thread
        thread = threading.Thread(target=process_leads_async,args=(
            # 1501858, 'dung.pham@jesselton.capital', 'Dung'
            reply_data['campaign_id'],
            reply_data['to_email'],
            reply_data['to_name'],
            ))
        thread.start()

        return jsonify({"message": "Webhook received, processing started"}), 200
    return jsonify({"message": "Send a POST request"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
