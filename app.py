import os
from decouple import config
import tweepy
from tweepy.auth import OAuthHandler
import requests
import time
from datetime import timedelta, datetime
import logging

# Twitter API
ACCESS_TOKEN = config('ACCESS_TOKEN')
ACCESS_SECRET = config('ACCESS_SECRET')
CONSUMER_KEY = config('CONSUMER_KEY')
CONSUMER_SECRET = config('CONSUMER_SECRET')
# BSCScan API
BSC_API_KEY = config('BSC_API_KEY')

logging.basicConfig(filename="std.log", 
					format='%(asctime)s %(message)s', 
					filemode='w') 
logger=logging.getLogger()
logger.setLevel(logging.DEBUG) 

TOKEN_ADDRESS = '0x8076c74c5e3f5852037f31ff0093eeb8c8add8d3' # Safemoon Token Address on BSC
BURN_WALLET_ADDRESS = '0x0000000000000000000000000000000000000001' # Safemoon Burn Wallet Address
TOTAL_SUPPLY = 1000000000000000 # Total Safemoon Supply
bsc_scan_api_endpoint = ('https://api.bscscan.com/api?module=account&action=tokenbalance&contractaddress='
            + TOKEN_ADDRESS
            + '&address='
            + BURN_WALLET_ADDRESS
            + '&tag=latest&apikey='  
            + BSC_API_KEY)

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
        print('Burn Percentage has not changed')
    

while 1:

    response = requests.get(bsc_scan_api_endpoint)
    burned_supply = float(response.json()['result'])/1000000000/TOTAL_SUPPLY
    tweet = "{:.4%}".format(burned_supply) + " of Safemoon supply has been sent to burn wallet"
    
    print(tweet)
    post_tweet(tweet)
    now = datetime.now()
    print("Current date and time: ")
    print(str(now))
    logger.info(tweet)
    dt = datetime.now() + timedelta(hours=4)
    dt = dt.replace(minute=0)

    while datetime.now() < dt:
        time.sleep(1)