import json
import os
import tweepy
import psycopg2
import sched
import time
import requests
import utils


class KosuzuBot(tweepy.StreamListener):

    def __init__(self, api: tweepy.API, cursor: psycopg2._psycopg.cursor):
        self.api = api
        self.__cursor = cursor
        self.scheduler = sched.scheduler(time.time, time.sleep)

    def make_tweet(self, status: tweepy.Status = None):
        """This method constructs and posts a new tweet. I've configured it to post every 3 hours."""
        kosuzus, chapter = self.__getkosuzu()
        media_ids = []
        tweet_text = f"Forbidden Scrollery Chapter {chapter}" if chapter else ""

        if status:
            tweet_text = f"@{status.user.screen_name} {tweet_text}"

        print(tweet_text)
        print(kosuzus)
        for filename in kosuzus:
            response = self.api.media_upload(filename)
            media_ids.append(response.media_id)
            os.remove(filename)

        if not status:
            self.api.update_status(status=tweet_text, media_ids=media_ids)
            self.scheduler.enter(10800, 1, self.make_tweet)
        else:
            self.api.update_status(status=tweet_text, media_ids=media_ids, in_reply_to_status_id=status.id)

    def on_status(self, status) -> None:
        if not utils.checkreplychain(status, self.api):
            return
        else:
            self.make_tweet(status)

    def on_error(self, status_code) -> None:
        if status_code == 420:
            return False

    def suzunaanfootscroll(self) -> None:
        seki_tweets = self.api.user_timeline(screen_name="seki_ebooks", count=1)

        for tweet in seki_tweets:
            if "suzunaan" in tweet.text.lower() and not tweet.retweeted:
                print("FOOT SCROLL DETECTED")
                self.api.retweet(tweet.id)
            else:
                print("no foot scroll today")
        self.scheduler.enter(3600, 2, self.suzunaanfootscroll)

    def __getkosuzu(self) -> tuple[list[str], int]:
        """This method grabs a random Kosuzu from the database. Returns a list of filenames."""
        random_query = 'SELECT * FROM images OFFSET floor(random() * (SELECT COUNT(*) FROM images)) LIMIT 1'
        series_query = 'SELECT * FROM images I, seriesinfo S WHERE I.name=%s AND I.id=S.id ORDER BY num'

        self.__cursor.execute(random_query)
        row = self.__cursor.fetchone()
        chapter = row[3]
        kosuzus = []

        # series check
        if row[4]:
            self.__cursor.execute(series_query, [row[1]])
            rows = self.__cursor.fetchall()
            for row in rows:
                filename = f"{row[1]}{row[8]}-{row[9]}.png"
                self.__downloadimage(row[2], filename)
                kosuzus.append(filename)
        else:
            filename = f"{row[1]}.png"
            self.__downloadimage(row[2], filename)
            kosuzus.append(filename)
        return (kosuzus, chapter)

    def __downloadimage(self, url: str, filename: str) -> None:
        response = requests.get(url)
        with open(filename, 'wb') as f:
            f.write(response.content)
        return
