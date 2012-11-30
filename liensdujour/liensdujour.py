#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Imports
import datetime
import locale
import math

from flask import Flask, render_template, redirect
import pymongo
import twitter_text
from werkzeug.contrib.fixers import ProxyFix

# Configuration
config = dict()
config['twitter'] = {'user': u'liensdujour',
                     'profile_image_url': ('https://twimg0-a.akamaihd.net/'
                     'profile_images/1649182510/icon.png'),
                     'tweets_per_page': 20}
config['mongo'] = {'server': u'localhost',
                   'database': u'liensdujour',
                   'collection': u'liens'}

# Context for the template
template_context = {'site_address': 'http://liensdujour.fr',
                    'site_description': (u'Tous les liens du jour sur '
                                         u'liensdujour.fr — @liensdujour'),
                    'twitter_name': u'✩ Liens du jour',
                    'twitter_user': config['twitter']['user'],
                    'profile_image_url': (config['twitter']
                                          ['profile_image_url']),
                    'list_dates': list(),
                    'pagination': dict()}

# Creating the app
app = Flask(__name__)


# Home and pages routes
@app.route('/', defaults={'page': 1})
@app.route('/<int:page>')
def show_page(page):
    del template_context['list_dates'][:]
    tweets_json = get_tweets(page)
    if not tweets_json:
        return redirect('/')
    template_context['pagination'] = get_pagination(page)
    return render_template('index.html',
                           tweets=tweets_json,
                           params=template_context)


# Favicon route
@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('img/favicon.ico')


# Fonctions used "as-is" in the template
def print_date(timestamp):
    """ Check if the date is already printed in the page
        Template will print the date if False
    """
    date_to_display = get_datefr(timestamp, '%A %d %B')
    if not date_to_display in template_context['list_dates']:
        template_context['list_dates'].append(date_to_display)
        return True
    else:
        return False
app.jinja_env.globals.update(print_date=print_date)


def is_timestamp_today(timestamp):
    """ Check if timestamp is today
        Template will print "Aujourd'hui" if True
    """
    return bool(datetime.date.fromtimestamp(timestamp)
                == datetime.date.today())
app.jinja_env.globals.update(is_timestamp_today=is_timestamp_today)


# Custom filters used in the template
@app.template_filter('get_datefr')
def get_datefr(timestamp, pattern='%A %d %B'):
    """ Get strftime_fr for timestamp following the given pattern
        /!\ get_datefr is also used by print_date()
    """
    locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
    # .replace to deal with encoding hell
    return (datetime.datetime.fromtimestamp(timestamp).strftime(pattern)
                    .replace('\xFB', 'u').replace('\xE9', 'e'))


@app.template_filter('clickable')
def clickable(tweet):
    """ Makes tweet links, @usernames and #hashtags clickable
        CSS classes : .username & .hashtag
    """
    return twitter_text.Autolink(tweet).auto_link()


# Internals fonctions
def get_pagination(page):
    """ Get pagination from page number """
    collection = get_collection()
    page_max = int(math.ceil(collection.count()
                   / config['twitter']['tweets_per_page']))
    result = {'prev': page - 1,
              'active': page,
              'next': page + 1,
              'after': page + 2,
              'teasing': True}
    if page == 1:
        result['prev'] = False
    elif page == (page_max - 2):
        result['teasing'] = False
    elif page == (page_max - 1):
        result['after'] = False
        result['teasing'] = False
    elif page == page_max:
        result['next'] = False
        result['after'] = False
        result['teasing'] = False
    return result


def get_tweets(page):
    """ Get tweets from mongodb """
    collection = get_collection()
    # check if <page> is valid
    if (page <= int(math.ceil(collection.count()
                    / config['twitter']['tweets_per_page']))):
        return (collection.find(
                fields={'id': True, 'timestamp': True, 'tweet': True})
                .sort('timestamp', pymongo.DESCENDING)
                .skip(config['twitter']['tweets_per_page'] * (page - 1))
                .limit(config['twitter']['tweets_per_page']))
    else:
        return None


def connect_mongodb(server=config['mongo']['server']):
    """ Connection to MongoDB """
    try:
        connection = pymongo.Connection(server)
    except:
        print 'Error: Unable to Connect'
        connection = None
    return connection


def get_collection(connection=None):
    """ Get MongoDB Collection """
    if not connection:
        connection = connect_mongodb()
    try:
        collection = connection.liensdujour.liens
    except:
        print 'Error: Unable to select Collection'
        collection = None
    return collection

# Gunicorn
app.wsgi_app = ProxyFix(app.wsgi_app)

# Fire up the server
if __name__ == '__main__':
    app.run(debug=True)
