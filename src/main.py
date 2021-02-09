import tweepy
import psycopg2
import sys
import utils
from kosuzubot import KosuzuBot
from decouple import config

if __name__ == "__main__":
    consumer_key = config('CONSUMER_KEY')
    consumer_secret = config('CONSUMER_SECRET')
    access_token = config('ACCESS_TOKEN')
    access_token_secret = config('ACCESS_TOKEN_SECRET')
    db_pass = config('DB_PASS')
    db_ip = config('DB_IP')

    connection = psycopg2.connect(user="pi", dbname="kosuzudb", host=db_ip, port=5432, password=db_pass)
    cursor = connection.cursor()
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True)
    bot = KosuzuBot(api, cursor)

    try:
        bot.scheduler.enter(5, 1, bot.make_tweet)
        bot.scheduler.enter(5, 2, bot.suzunaanfootscroll)
        bot.scheduler.enter(5, 3, bot.checkStream)
        bot.scheduler.run()
    except KeyboardInterrupt:
        sys.exit()
    except Exception as e:
        with open("/home/pi/Desktop/kosuzubot/log.txt", 'a+') as logfile:
            logfile.write(e)
        
