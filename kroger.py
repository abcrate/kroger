import sys
import config
import sqlite3
import requests
from base64 import b64encode
from datetime import datetime


DATABASE = 'prices.db'

client_id = config.CLIENT_ID
client_secret = config.CLIENT_SECRET

zip_code = 38138

search_term = 'eggs'

auth = b64encode(f"{client_id}:{client_secret}".encode()).decode()


def get_token():
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {auth}'
    }
    
    response = requests.post('https://api.kroger.com/v1/connect/oauth2/token', headers=headers, data={
        'grant_type': 'client_credentials',
        'scope': 'product.compact'
    })

    response.raise_for_status()
    return response.json()['access_token']

def get_stores(token, zip_code):
    headers = {'Authorization': f'Bearer {token}'}
    params = {
        'filter.zipCode.near': zip_code,
        'filter.limit': 50 
    }
    
    response = requests.get('https://api.kroger.com/v1/locations', headers=headers, params=params)
    response.raise_for_status()
    return response.json()['data']

def get_prices(token, location_id):
    headers = {'Authorization': f'Bearer {token}'}
    params = {
        'filter.term': search_term,
        'filter.locationId': location_id,
        'filter.limit': 10
    }
    
    response = requests.get('https://api.kroger.com/v1/products', headers=headers, params=params)
    response.raise_for_status()
    return response.json()['data']

def db_save(products, store_info):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        store_id INTEGER,
        store_name TEXT,
        store_address TEXT,
        store_city TEXT,
        store_state TEXT,
        store_zip TEXT,
        product_id INTEGER,
        product_name TEXT,
        price REAL
    )
    ''')

    for item in products:
        product_id = item['productId']
        product_name = item['description']
        price = item['items'][0]['price']['regular']
        date = datetime.now().strftime('%Y-%m-%d')

        cursor.execute('INSERT INTO prices (date, store_id, store_name, store_address, store_city, store_state, store_zip, product_id, product_name, price) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', 
                       (date, store_info['id'], store_info['name'], store_info['address'], store_info['city'], store_info['state'], store_info['zip'], product_id, product_name, price))

    conn.commit()
    conn.close()

def price_check():
    token = get_token()
    stores = get_stores(token, zip_code)
    for store in stores:
        store_info = {
            'id': store['locationId'],
            'name': store['name'],
            'address': store['address']['addressLine1'],
            'city': store['address']['city'],
            'state': store['address']['state'],
            'zip': store['address']['zipCode']
        }
        eggs = get_prices(token, store_info['id'])
        db_save(eggs, store_info)

if __name__ == '__main__':
    price_check()
    sys.exit(0)
