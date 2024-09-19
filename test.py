import requests

data = {
    "status": "confirming",
    "trackId": "81653261",
    "address": "0xc05a778c9C15B45e53e202A08BE8d7308937CAee",
    "txID": "0x1b6b970fb2b63582757ceaaeb5a6cdb44d0ac596a699f83877615b7ba598d361",
    "amount": "3",
    "currency": "USDT",
    "price": "2.94",
    "payAmount": "3",
    "payCurrency": "USDT",
    "receivedAmount": "2.94",
    "network": "ERC20",
    "rate": "0",
    "feePaidByPayer": 0,
    "underPaidCover": 0,
    "email": "",
    "orderId": "fe38815c-f4e5-4530-851d-2a17de07e5d8",
    "description": "Static-wallet order for user 5748713709",
    "date": "1726593827",
    "payDate": "1726593923",
    "type": "payment"
}

url = 'https://193.160.130.149:8443/callback'
x = requests.post(url, json=data, headers={'HMAC':'hevsjagsheje'}, verify=False)

print(x.text)