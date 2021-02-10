import json
import os
import tweepy
import psycopg2
import sched
import time
import requests
import random
import utils as utils
from typing import Tuple
from typing import List

class KosuzuBot(tweepy.StreamListener):

    def __init__(self, api: tweepy.API, cursor: psycopg2._psycopg.cursor):
        self.api = api
        self.__cursor = cursor
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.chapters = set()
        self.stream = tweepy.Stream(auth=self.api.auth, listener=self)
        self.stream.filter(track=['@KosuzuBot'], is_async=True)
        self.initialize_chapters()

    def checkStream(self) -> None:
        if not self.stream.running:
            del self.stream
            self.stream = tweepy.Stream(auth=self.api.auth, listener=self)
            self.stream.filter(track=['@KosuzuBot'], is_async=True)
        self.scheduler.enter(10, 3, self.checkStream)

    def initialize_chapters(self) -> None:
        self.__cursor.execute("select max(chapter) from images")
        max = self.__cursor.fetchone()[0]
        self.chapters = set(range(1, max+1))

    def make_tweet(self, status: tweepy.Status = None) -> None:
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

    def on_status(self, status: tweepy.Status) -> None:
        if not utils.checkreplychain(status, self.api) or hasattr(status, "retweeted_status"):
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

    def __getkosuzu(self) -> Tuple[List[str], int]:
        """This method grabs a random Kosuzu from the database. Returns a list of filenames."""
        random_query = 'SELECT * FROM images WHERE chapter=%s LIMIT 1'
        series_query = 'SELECT * FROM images I, seriesinfo S WHERE I.name=%s AND I.id=S.id ORDER BY num'
        
        if(len(self.chapters) < 1):
            self.initialize_chapters()

        random_chapter = random.choice(list(self.chapters))
        self.chapters.discard(random_chapter)
        print(f"Discarding {random_chapter}...")
        print(f"Chapters left:\n{self.chapters}")
        self.__cursor.execute(random_query, [random_chapter])
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
