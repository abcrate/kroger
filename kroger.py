import config
import requests
import schedule
import time
from datetime import datetime
import sqlite3

DATABASE = 'kroger_prices.db'

def get_token():
    """Authenticate with Kroger API and get access token."""
    response = requests.post(config.TOKEN_URL, data={
        'grant_type': 'client_credentials',
        'scope': 'product.compact'
    }, auth=(config.CLIENT_ID, config.CLIENT_SECRET))

    response.raise_for_status()
    return response.json()['access_token']

def get_prices(token, zip=config.ZIP_CODE):
    """Fetch egg prices from Kroger API."""
    headers = {'Authorization': f'Bearer {token}'}
    params = {
        'filter.term': 'eggs',
        'filter.locationId': zip,
        'filter.limit': 10
    }
    
    response = requests.get('https://api.kroger.com/v1/products', headers=headers, params=params)
    response.raise_for_status()
    return response.json()['data']

def db_save(data):
    """Save product data to SQLite database."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT,
        price REAL,
        currency TEXT,
        date TEXT
    )
    ''')

    # Insert data
    for item in data:
        product_name = item['description']
        price = item['items'][0]['price']['regular']
        currency = item['items'][0]['price']['currency']
        date = datetime.now().strftime('%Y-%m-%d')

        cursor.execute('INSERT INTO prices (product_name, price, currency, date) VALUES (?, ?, ?, ?)', 
                       (product_name, price, currency, date))

    conn.commit()
    conn.close()

def daily_check():
    """Perform daily check for egg prices."""
    token = get_token()
    egg_price = get_prices(token)
    db_save(egg_price)

# Schedule the script to run daily at the specified time
# schedule.every().day.at(config.CHECK_TIME).do(daily_check)

if __name__ == '__main__':
    while True:
        daily_check()
        # schedule.run_pending()
        # time.sleep(60)
