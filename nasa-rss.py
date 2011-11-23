#!/1/data/ENV/bin/python

import logging
import datetime
import urllib
import lxml.html

import feedparser

def dlog(logger):
    date = datetime.date.today().strftime('%Y-%m-%d')
    formatter = logging.Formatter(
            '%(asctime)-6s: %(name)s - %(levelname)s - %(message)s')
    consoleLogger = logging.StreamHandler()
    consoleLogger.setLevel(logging.INFO)
    consoleLogger.setFormatter(formatter)
    logging.getLogger('').addHandler(consoleLogger)
    
    fileLogger = logging.FileHandler(filename='nasaRSS-%s.log' % date)
    fileLogger.setLevel(logging.WARNING)
    fileLogger.setFormatter(formatter)
    logging.getLogger('').addHandler(fileLogger)
    logger = logging.getLogger(logger)
    logger.setLevel(logging.INFO)
    return logger

def getFeedList():
    masterFeedList = "http://www.nasa.gov/rss/internetarchive/index.html"
    parsed = lxml.html.fromstring(urllib.urlopen(masterFeedList).read())
    feedList =  ([link[2] for link in parsed.iterlinks() if link[2].endswith(
                 'rss')])
    feedList = list(set(feedList))
    return feedList

def main():
    for feed in getFeedList():
        parsed = feedparser.parse(feed)
        bozo = parsed.bozo
        print '\n\n----\n\n'
        dlog('root.bozo').warning('%s is a bozo!' % feed)

if __name__ == "__main__":
    main()

