import uuid
import requests
import json

from database import add_transaction
from decouple import config

def create_invoice(chat_id, payment_type, amount, order_id):
    url = 'https://api.oxapay.com/merchants/request'
    # order_id = f"ORD-{payment_type.upper()}-{uuid.uuid4()}"
    data = {
        'merchant': config('MERCHANT_KEY'),
        'amount': amount,
        'currency': 'EUR',
        'lifeTime': 30,
        'feePaidByPayer': 0,
        'underPaidCover': 0.2,
        'callbackUrl': 'https://193.160.130.149:8443/callback',
        'returnUrl': 'https://t.me/Test_Perso_bot',
        'description': f'Order for user {chat_id}',
        'orderId': order_id,
        'email': 'user@example.com'
    }
    
    response = requests.post(url, data=json.dumps(data))
    result = response.json()

    print(result)
    if result['result'] == 100:
        track_id = result['trackId']
        pay_link = result['payLink']

        # Add the transaction to the database
        # add_transaction(chat_id, 'Invoice', amount, 'EUR', track_id, 'Pending', order_id)

        return pay_link, track_id
    else:
        return None, None
    
def create_white_label_invoice(chat_id,amount,payment_type,order_id, network=None):
    url = 'https://api.oxapay.com/merchants/request/whitelabel'
    # order_id = f"ORD-WL-{payment_type.upper()}-{uuid.uuid4()}"
    data = {
        'merchant': config('MERCHANT_KEY'), 
        'amount': amount,
        'currency': 'EUR',      
        'payCurrency': payment_type.upper(),  
        'lifeTime': 30,         
        'feePaidByPayer': 0,    
        'underPaidCover': 0.2,   
        'callbackUrl': 'https://193.160.130.149:8443/callback',  
        'description': f'White-label order for user {chat_id}',
        'orderId': order_id,
        'email': 'user@example.com' 
    }

    if network:
        data['network'] = network

    response = requests.post(url, data=json.dumps(data))
    result = response.json()

    print(result)
    if result['result'] == 100:
        track_id = result['trackId']
        pay_link = result['QRCode']
        address= result['address'] 
        payamount = result['payAmount']

        # add_transaction(chat_id, f'{payment_type}-Whitelabel', amount, 'EUR', track_id, 'Pending', order_id)

        return pay_link, track_id, address, payamount
    else:
        return None, None
def create_static_address(chat_id, payment_type,order_id, network=None):
    url = 'https://api.oxapay.com/merchants/request/staticaddress'
    data = {
        'merchant': config('MERCHANT_KEY'), 
        'currency': payment_type,
        'callbackUrl': 'https://193.160.130.149:8443/callback',
        'description': f'Static-wallet order for user {chat_id}',
        'orderId': order_id,
        'network': network
    }

    response = requests.post(url, data=json.dumps(data))
    result = response.json()

    print(result)
    if result['result'] == 100:
        # track_id = result['trackId']
        # pay_link = result['QRCode']
        address= result['address'] 

        # add_transaction(chat_id, f'{payment_type}-Whitelabel', amount, 'EUR', track_id, 'Pending', order_id)

        return address
    else:
        return None
def confirm_payment_status(track_id):
    url = 'https://api.oxapay.com/merchants/inquiry'
    data = {
        'merchant': config('MERCHANT_KEY'),
        'trackId': track_id
    }
    response = requests.post(url, data=json.dumps(data))
    
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'Paid':
            return 'completed'
        elif data['status'] == 'Expired':
            return 'Expired'
    return 'pending'

def confirm_oxa_payment(track_id):
    url = 'https://api.oxapay.com/merchants/inquiry'
    data = {
        'merchant': config('MERCHANT_KEY'),
        'trackId': track_id
    }
    response = requests.post(url, data=json.dumps(data))
    
    if response.status_code == 200:
        data = response.json()
        data['track_id'] = track_id
        with open('test_webhook.json', 'w') as f:
            json.dump(data,f, indent=4)

        if data['status'] == 'Paid':
            return data['payAmount'], data['amount'], data['payCurrency']
        elif data['status'] == 'Expired':
            return None, None, None
    return None, None, None
