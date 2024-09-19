import hmac
import hashlib
import json
import threading
from flask import Flask, request, jsonify

from database import get_chat_id_by_order_id, get_order_id, get_status_by_order_id, update_transaction_by_order_id, update_transaction_status, get_chat_id
from spoofer import send_status_change, worker
import logging
import os
from decouple import config


log_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(log_dir, 'webhook.log')
# logging.basicConfig(
#     filename=log_file,
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s'
# )
logger = logging.getLogger(__name__)
handler = logging.FileHandler(log_file)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


app = Flask(__name__)
merchant_api_key = config('MERCHANT_KEY')

# @app.route('/callback', methods=['POST'])
# def handle_callback():
#     # Get HMAC from headers
#     received_hmac = request.headers.get('HMAC')
    
#     # Verify the HMAC signature
#     raw_data = request.get_data(as_text=True)
#     generated_hmac = hmac.new(merchant_api_key.encode(), raw_data.encode(), hashlib.sha512).hexdigest()

#     print('request recieved')
#     # print(request.json)
#     if hmac.compare_digest(received_hmac, generated_hmac):
#         callback_data = request.json

#         # with open('static_callback.json', 'w') as f:
#         #     json.dump(callback_data,f, indent=4)
        
#         # Update the transaction status in the database
#         track_id = callback_data['trackId']
#         new_status = callback_data['status']
        
#         update_transaction_status(track_id, new_status)
#         user_id = get_chat_id(track_id)
#         order_id = get_order_id(track_id)
        
#         threading.Thread(target=worker, args=(user_id, track_id, order_id)).start()

#         return jsonify({"message": "Callback processed successfully."}), 200
#     else:
#         return jsonify({"message": "Invalid HMAC signature."}), 400

@app.route('/callback', methods=['POST'])
def handle_callback():
    logger.info('request recieved')
    
    # Get HMAC from headers
    received_hmac = request.headers.get('HMAC')
    
    # Verify the HMAC signature
    raw_data = request.get_data(as_text=True)
    generated_hmac = hmac.new(merchant_api_key.encode(), raw_data.encode(), hashlib.sha512).hexdigest()

    # print(request.json)
    if hmac.compare_digest(received_hmac, generated_hmac):
        callback_data = request.json
        
        logger.info(f'request data: {callback_data}')
        # with open('test_webhook.json', 'w') as f:
        #     json.dump(callback_data,f, indent=4)
        
        # Update the transaction status in the database
        try:
            track_id = callback_data['trackId']
            new_status = callback_data['status']
            order_id = callback_data['orderId']
            amount = callback_data['amount']
            currency = callback_data['currency']
            user_id = get_chat_id_by_order_id(order_id)
            
            

            db_status = get_status_by_order_id(order_id)
            if db_status != 'Paid' and new_status == 'Paid':
                update_transaction_by_order_id(order_id, track_id,new_status, amount, currency)
                
                threading.Thread(target=worker, args=(user_id, amount, currency, order_id)).start()
            elif new_status != 'Paid' and db_status != new_status:
                update_transaction_by_order_id(order_id, track_id,new_status, amount, currency)
                send_status_change(user_id, new_status, amount, currency)

            return jsonify({"message": "Callback processed successfully."}), 200
        except:
            logger.error('processing oxapay request failed')
            return jsonify({"message": "internal server error."}), 500
    else: 
        logger.warning('Request rejected: Invalid HMAC signature')
        return jsonify({"message": "Invalid HMAC signature."}), 400

if __name__ == '__main__':
    app.run(port=5000)