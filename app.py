from decouple import config
import tweepy
from tweepy.auth import OAuthHandler
import requests
import time
from datetime import timedelta, datetime
import logging
import sqlite3
import math
import humanize

# sqlite

connection = sqlite3.connect('records.db')

cursor = connection.cursor()

# twitter API

ACCESS_TOKEN = config('ACCESS_TOKEN')
ACCESS_SECRET = config('ACCESS_SECRET')
CONSUMER_KEY = config('CONSUMER_KEY')
CONSUMER_SECRET = config('CONSUMER_SECRET')

# bscscan API

BSC_API_KEY = config('BSC_API_KEY')

# logging

logging.basicConfig(filename="log.log", 
					format='%(asctime)s %(message)s', 
					filemode='w') 
logger=logging.getLogger()
logger.setLevel(logging.DEBUG) 

# token address for safemoon

TOKEN_ADDRESS = '0x8076c74c5e3f5852037f31ff0093eeb8c8add8d3'

# safemoon burn wallet address 

BURN_WALLET_ADDRESS = '0x0000000000000000000000000000000000000001'

# total safemoon supply

TOTAL_SUPPLY = 1000000000000000 

# bscscan wallet total

bsc_scan_endpoint = ('https://api.bscscan.com/api?module=account&action=tokenbalance&contractaddress='
            + TOKEN_ADDRESS
            + '&address='
            + BURN_WALLET_ADDRESS
            + '&tag=latest&apikey='  
            + BSC_API_KEY)

# coingecko token price

coingecko_endpoint = ('https://api.coingecko.com/api/v3/coins/safemoon?market_data=true')

# tweepy posting

def post_tweet(tweet_body):
        
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
    
    api = tweepy.API(auth)
    
    try:
        redirect_url = auth.get_authorization_url()
    except tweepy.TweepError:
        print('Error! Failed to get request token.')

    try:
        api.update_status(tweet_body)    
    except tweepy.TweepError:
        print('Duplicate Post')


def percent_tweet_text(supply_api, price_api):

    supply_response = requests.get(supply_api).json()
    burned_supply = float(supply_response['result'])/1000000000
    burned_supply_percentage = burned_supply/TOTAL_SUPPLY

    price_response = requests.get(price_api).json()
    token_price = "{:.10f}".format(float(price_response['market_data']['current_price']['usd']))

    tweet_text = ("{:.4%}".format(burned_supply_percentage) + 
            " of Safemoon supply has been sent to burn wallet. " +
            token_price +
            " is the token price."
            )
    return {'tweet_text': tweet_text, 'token_price': token_price, 'burned_supply': burned_supply}




def add_tweet_record(connection, burned_supply, token_price):

    cursor.execute("INSERT INTO history (date, token_supply, price) VALUES (?, ?, ?)", (datetime.now(), burned_supply, token_price))
    connection.commit()
    cursor.close()

def burn_update(connection):

    latest_record = connection.execute("SELECT * FROM history ORDER BY date DESC LIMIT 1;").fetchall()
    previous_record = connection.execute("SELECT * FROM history ORDER BY date DESC LIMIT 1 OFFSET 1;").fetchall()
    date_diff = humanize.naturaldelta(datetime.strptime(latest_record[0][0], '%Y-%m-%d %H:%M:%S.%f') - datetime.strptime(previous_record[0][0], '%Y-%m-%d %H:%M:%S.%f'))
    supply_diff = float(latest_record[0][1]) - float(previous_record[0][1])
    supply_diff_formatted = "{:,}".format(math.trunc(supply_diff))
    #price_diff = float(latest_record[0][2]) - float(previous_record[0][2])
    last_price = "{:.8f}".format(float(latest_record[0][2]))
    dollar_value_delta = float(last_price) * float(supply_diff)
    dollar_value_delta_formatted = "${:0,.0f}".format(math.trunc(dollar_value_delta))

    cursor.close()
    connection.close()

    return {'date_diff': date_diff,'supply_diff_formatted': supply_diff_formatted, 'last_price': last_price, 'dollar_value_delta_formatted': dollar_value_delta_formatted}

def burn_tweet_text(date_diff,supply_diff_formatted,last_price,dollar_value_delta_formatted):

    burn_tweet=f"{dollar_value_delta_formatted} in Safemoon tokens have been burned in the last {date_diff}. {supply_diff_formatted} tokens at {last_price} price)"

    return burn_tweet

while 1:
    
    # build first tweet with % sent to burn wallet
    tweet_body = percent_tweet_text(bsc_scan_endpoint,coingecko_endpoint)

    # add stats to db
    add_tweet_record(connection, tweet_body['burned_supply'], tweet_body['token_price'])

    # build second tweet with burn stats
    burn_tweet_body = burn_update(connection)


    print(tweet_body['tweet_text'])
    print(burn_tweet_text(burn_tweet_body['date_diff'], burn_tweet_body['supply_diff_formatted'], burn_tweet_body['last_price'], burn_tweet_body['dollar_value_delta_formatted']))
    
    post_tweet(tweet_body['tweet_text'])
    post_tweet(burn_tweet_text(burn_tweet_body['date_diff'], burn_tweet_body['supply_diff_formatted'], burn_tweet_body['last_price'], burn_tweet_body['dollar_value_delta_formatted']))
    print("Current date and time: ", str(datetime.now()))

    logger.info(percent_tweet_text(bsc_scan_endpoint,coingecko_endpoint))
    dt = datetime.now() + timedelta(hours=4)
    dt = dt.replace(minute=0)

    while datetime.now() < dt:
        time.sleep(1)