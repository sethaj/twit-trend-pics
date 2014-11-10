#!/usr/bin/env python -tt
import tweepy
import pprint
from ConfigParser import SafeConfigParser

parser = SafeConfigParser()
parser.read('config.ini')

auth = tweepy.OAuthHandler(parser.get('twitter', 'consumer_key'), parser.get('twitter', 'consumer_secret'))
auth.set_access_token(parser.get('twitter', 'access_token'), parser.get('twitter', 'access_token_secret'))
api = tweepy.API(auth)

pp = pprint.PrettyPrinter(indent=2, depth=8)

# Get top 10 global trends
trends = api.trends_place(1)

# For each trend, try to get 20 images posted w/ tweets
for t in trends[0]["trends"]:

  pictures = list()
  max_id = 0
  max_tries = 10
  tries = 0

  while len(pictures) < 20 and tries < max_tries:

    print str(tries) + "\t" + t["name"]

    if max_id > 0:
      messages = api.search(q = t["name"], since_id = max_id)
    else:
      messages = api.search(q = t["name"])

    for m in messages:
      #print "\t" + m.text
      #print m.coordinates, almost never there, we really want m.corrdinates["coordinates"] I think
      #print m.author.screen_name
      #print m.created_at, UTC time in this format: "Wed Aug 27 13:08:45 +0000 2008"

      if "media" in m.entities:
        if m.entities["media"][0]["media_url"]:
          print "\t" + m.entities["media"][0]["media_url"]
          # images must be unique? A lot of duplicates happen through re-tweets
          pictures.append(m.entities["media"][0]["media_url"])

      max_id = m.id
    tries += 1

