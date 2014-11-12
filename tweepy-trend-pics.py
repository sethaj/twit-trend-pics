#!/usr/bin/env python -tt
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import tweepy
import pprint
import os
from ConfigParser import SafeConfigParser
#from wand.image import Image
from PIL import Image
from StringIO import StringIO
import sqlite3 as sqlite
import datetime
import re
import requests

def create_tables(db_name):
    with sqlite.connect(db_name) as con:
        cur = con.cursor()
        cur.execute("drop table if exists trends")
        sql = """
        create table trends (
            id integer primary key,
            trend_name text,
            trend_rank integer,
            created text
        )"""
        cur.execute(sql)

        cur.execute("drop table if exists pictures")
        sql = """
        create table pictures (
            id integer primary key,
            trend_id integer,
            tweet text,
            author text,
            created text,
            image_url text,
            image_file text,
            coordinates text,
            tweet_number integer
        )"""
        cur.execute(sql)


def mkdir_p(path):
    # 'mkdir -p' functionality taken from: http://stackoverflow.com/a/600612
    try:
        os.makedirs(path)
    except OSError as exc:
        #if exc.errno == errno.EEXIST and os.path.isdir(path):
        if exc.errno and os.path.isdir(path):
            pass
        else: raise


def image_file_location(image_url, today):
    # turns a twitter image url into a location on disk
    # http://pbs.twimg.com/media/B2HS2lrIAAEOdZs.jpg
    # into 
    # images/YYYY-MM-DD/B2HS2lrIAAEOdZs.jpg
    m = re.search(r'.*/(.*?)$', image_url)
    return 'images/' + today.strftime("%Y-%m-%d") + '/' + m.group(1)


def download_image(image_url, today):
    mkdir_p ('images/' + today.strftime("%Y-%m-%d"))
    image_file = image_file_location(image_url, today)
    if not os.path.isfile(image_file):
        try:
            response = requests.get(image_url)
            try:
                Image.open(StringIO(response.content)).save(image_file)
            except IOError, e:
                print "can't save" + image_file + ": " + e
        except: 
            pass
            
    return image_file

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

# 
DB_NAME = "trends.db"
PICTURES = 20 # 20
MAX_TRIES_PER_TREND = 10  # 10

#
parser = SafeConfigParser()
parser.read('config.ini')

# get tweepy
auth = tweepy.OAuthHandler(parser.get('twitter', 'consumer_key'), parser.get('twitter', 'consumer_secret'))
auth.set_access_token(parser.get('twitter', 'access_token'), parser.get('twitter', 'access_token_secret'))
api = tweepy.API(auth)

#pp = pprint.PrettyPrinter(indent=2, depth=8)

today = datetime.date.today()

# create tables if this is the first time run
if not os.path.isfile(DB_NAME):
    create_tables(DB_NAME)


# Get top 10 global trends
trends = api.trends_place(1)
# For each trend, try to get PICTURES posted w/ tweets
trend_rank = 1
for t in trends[0]["trends"]:

    pictures = list()
    max_id = 0
    tries = 0
    tweet_number = 1
    trend_id = 0

    with sqlite.connect(DB_NAME) as con:
        cur = con.cursor()
        sql = "insert into trends (trend_name, trend_rank, created) values (?,?,?)"
        cur.execute(sql, [t["name"], trend_rank, datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%m:%S")])

        trend_id = cur.lastrowid

    while len(pictures) < PICTURES and tries < MAX_TRIES_PER_TREND:

        #print str(tries) + "\t" + t["name"]

        if max_id > 0:
            messages = api.search(q = t["name"], since_id = max_id)
        else:
            messages = api.search(q = t["name"])

        for m in messages:
            if "media" in m.entities:
                if m.entities["media"][0]["media_url"]:

                    image_url   = m.entities["media"][0]["media_url"]
                    image_file  = download_image(image_url, today)
                    created     = m.created_at.strftime("%Y-%m-%d %H:%m:%S")
                    tweet       = m.text
                    coords      = m.coordinates["coordinates"] if m.coordinates else ''
                    author      = m.author.screen_name

                    with sqlite.connect(DB_NAME) as con:
                        cur = con.cursor()
                        sql = """
                            insert into pictures 
                            (trend_id, tweet, author, created, image_url, image_file, coordinates, tweet_number)
                            values
                            (?, ?, ?, ?, ?, ?, ?, ?)"""
                        values = [trend_id, tweet, author, created, image_url, image_file, str(coords), tweet_number]
                        #print values
                        cur.execute(sql, values)

                    pictures.append(m.entities["media"][0]["media_url"])
            tweet_number += 1
        max_id = m.id
        tries += 1
    trend_rank += 1

