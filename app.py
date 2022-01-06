from decouple import config
import tweepy
import requests
from datetime import datetime
import sqlite3
import math
import humanize
import time

connection = sqlite3.connect('records.db')

cursor = connection.cursor()

# twitter API

ACCESS_TOKEN = config('ACCESS_TOKEN')
ACCESS_SECRET = config('ACCESS_SECRET')
CONSUMER_KEY = config('CONSUMER_KEY')
CONSUMER_SECRET = config('CONSUMER_SECRET')
BEARER_TOKEN = config('BEARER_TOKEN')

# bscscan API

BSC_API_KEY = config('BSC_API_KEY')

# token address for safemoon

TOKEN_ADDRESS = '0x42981d0bfbAf196529376EE702F2a9Eb9092fcB5'

# safemoon burn wallet address 

BURN_WALLET_ADDRESS = '0x0000000000000000000000000000000000000001'

# total safemoon supply

TOTAL_SUPPLY = 1000000000000 

# bscscan wallet total

bsc_scan_endpoint = ('https://api.bscscan.com/api?module=account&action=tokenbalance&contractaddress='
            + TOKEN_ADDRESS
            + '&address='
            + BURN_WALLET_ADDRESS
            + '&tag=latest&apikey='  
            + BSC_API_KEY)

# coingecko token price

coingecko_endpoint = ('https://api.coingecko.com/api/v3/coins/safemoon-2?market_data=true')

# tweepy posting

def post_tweet(tweet_body, **kwargs):
        
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
    
    api = tweepy.API(auth)

    try:
        try:
            api.update_status(tweet_body, in_reply_to_status_id = kwargs)      
        except tweepy.TweepError:
            print('Duplicate Post')

    except:
        try:
            api.update_status(tweet_body)  
        except tweepy.TweepError:
            print('Duplicate Post')

    kwargs = id
    return id
    
def percent_tweet_text(supply_api, price_api):

    supply_response = requests.get(supply_api).json()
    burned_supply = float(supply_response['result'])/1000000000
    burned_supply_percentage = burned_supply/TOTAL_SUPPLY

    price_response = requests.get(price_api).json()
    token_price = "{:.10f}".format(float(price_response['market_data']['current_price']['usd']))

    tweet_text = ("{:.4%}".format(burned_supply_percentage) + 
            " of Safemoon supply has been sent to burn wallet. ")

    return {'tweet_text': tweet_text, 'token_price': token_price, 'burned_supply': burned_supply}

def add_tweet_record(connection, burned_supply, token_price):

    cursor.execute("INSERT INTO history (date, token_supply, price) VALUES (?, ?, ?)", (datetime.now(), burned_supply, token_price))
    connection.commit()
 
def burn_update(connection):

    latest_record = connection.execute("SELECT * FROM history ORDER BY date DESC LIMIT 1;").fetchall()
    previous_record = connection.execute("SELECT * FROM history ORDER BY date DESC LIMIT 1 OFFSET 1;").fetchall()
    date_diff = datetime.strptime(latest_record[0][0], '%Y-%m-%d %H:%M:%S.%f') - datetime.strptime(previous_record[0][0], '%Y-%m-%d %H:%M:%S.%f')
    date_diff_formatted = humanize.naturaldelta(date_diff)
    supply_diff = float(latest_record[0][1]) - float(previous_record[0][1])
    supply_diff_formatted = "{:,}".format(math.trunc(supply_diff))
    last_price = "{:.8f}".format(float(latest_record[0][2]))
    dollar_value_delta = float(last_price) * float(supply_diff)
    dollar_value_delta_formatted = "${:0,.0f}".format(math.trunc(dollar_value_delta))

    return {'date_diff': date_diff, 'date_diff_formatted': date_diff_formatted,'supply_diff': supply_diff,'supply_diff_formatted': supply_diff_formatted, 'last_price': last_price, 'dollar_value_delta_formatted': dollar_value_delta_formatted}

def burn_tweet_text(date_diff_formatted,supply_diff_formatted,last_price,dollar_value_delta_formatted):

    burn_tweet=f"{'@safemoonburned ' + dollar_value_delta_formatted} in Safemoon tokens have been burned in the last {date_diff_formatted}. ({supply_diff_formatted} tokens at {last_price} price)"

    return burn_tweet

def burn_time_tweet(supply_burned, time_elapsed, total_burned):

    burn_time = (TOTAL_SUPPLY - total_burned) / supply_burned * time_elapsed.total_seconds()

    time_to_one_trillion = 1000000000000 / supply_burned * time_elapsed

    return {'burn_time': burn_time, 'time_to_one_trillion': time_to_one_trillion}




    #
    # "meta" "newest_id": "1435743065302573056",

def get_latest_tweet_id():

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)

    url = "https://api.twitter.com/2/tweets/search/recent?query=from:safemoonburned&"
    payload={}
    headers = {
    'Authorization': 'Bearer '+ BEARER_TOKEN
    }
    response = requests.request("GET", url, headers=headers, data=payload).json()

    return response["meta"]["newest_id"]

def tweet_loop():

    tweet_body = percent_tweet_text(bsc_scan_endpoint,coingecko_endpoint)

    # add stats to db

    add_tweet_record(connection, tweet_body['burned_supply'], tweet_body['token_price'])

    # build second tweet with burn stats

    burn_tweet_body = burn_update(connection)

    # build third tweet with burn time to 0

    burn_time_tweet_body = burn_time_tweet(burn_tweet_body['supply_diff'],burn_tweet_body['date_diff'],tweet_body['burned_supply'])

    # multiline tweet

    #with open('temp.txt', 'w') as f:
    #    f.write('@safemoonburned Time to burn 1T Safemoon: ' + humanize.precisedelta(burn_time_tweet_body['time_to_one_trillion']) + '\n' +
    #            'Time to burn 10T Safemoon: ' + humanize.precisedelta(burn_time_tweet_body['time_to_one_trillion']*10) + '\n' +
    #            'Time to burn 100T Safemoon: ' + humanize.precisedelta(burn_time_tweet_body['time_to_one_trillion']*100) + '\n')

    #with open('temp.txt','r') as f:
    #    time_to_burn_tweet = f.read()
        

    tweet1_body = tweet_body['tweet_text']
    #tweet2_body = burn_tweet_text(burn_tweet_body['date_diff_formatted'], burn_tweet_body['supply_diff_formatted'], burn_tweet_body['last_price'], burn_tweet_body['dollar_value_delta_formatted'])
    #tweet3_body = '@safemoonburned At this rate it will take ' + humanize.precisedelta(burn_time_tweet_body['burn_time']) + ' to burn Safemoon supply (theoretically, supply will not go to 0)'
    #tweet4_body = time_to_burn_tweet

    tweet1 = post_tweet(tweet1_body)
    time.sleep(15)
    #tweet2 = post_tweet(tweet2_body,in_reply_to_status_id=get_latest_tweet_id(), auto_populate_reply_metadata=True)
    #time.sleep(15)
    #tweet3 = post_tweet(tweet3_body,in_reply_to_status_id=get_latest_tweet_id(), auto_populate_reply_metadata=True)
    #time.sleep(15)
    #tweet4 = post_tweet(tweet4_body,in_reply_to_status_id=get_latest_tweet_id(), auto_populate_reply_metadata=True)

tweet_loop()

exit()
