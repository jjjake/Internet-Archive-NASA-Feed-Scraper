#!/home/jake/.virtualenvs/nasa-ingest/bin/python
import os
import re
import time

import feedparser
import logging,logging.config
import lxml.html
import urllib
from subprocess import call

import ia


ROOT_DIR = os.getcwd()
HOME_DIR = os.getcwd()
DOWNLOAD_DIR = '/1/incoming/tmp/nasa-rss'

logging.config.fileConfig('logging.conf')
console_logger = logging.getLogger('console')
mkdir = lambda x: os.mkdir(x) if not os.path.exists(x) else None


#______________________________________________________________________________
def get_feed_list():
    master_feed_list = "http://www.nasa.gov/rss/internetarchive/index.html"
    parsed = lxml.html.fromstring(urllib.urlopen(master_feed_list).read())
    feedList =  ([link[2] for link in parsed.iterlinks() if link[2].endswith(
                 'rss')])
    return list(set(feedList))

#______________________________________________________________________________
def build_collection_dict():
    collection_file = open('./rsscollections.txt').readlines()
    collection_list = [x.strip() for x in collection_file]
    dictionary = {}
    for collection in collection_list:
        k,v = collection.split(',')[-1], collection.split(',')[0]
        dictionary[k] = v
        if not v:
            continue
    return dictionary

#______________________________________________________________________________
def wget(mediaLink):
    wget = 'wget -q -nc %s' % mediaLink
    retcode = call(wget,shell=True)

#______________________________________________________________________________
def main():
    mkdir(DOWNLOAD_DIR)
    os.chdir(HOME_DIR)
    facet_file = os.path.join(ROOT_DIR, 'facets.txt')
    facet = ia.facets(facet_file)
    facet_dict, longest_key = facet.build_dict()
    collection_dict = build_collection_dict()
    for feed in get_feed_list():
        if not feed in collection_dict:
            print feed
            logging.warning('This feed needs to be assigned a collection: %s' % feed)
            continue
        parsed = feedparser.parse(feed)
        if parsed.bozo: logging.warning('%s is a bozo!' % feed)
        for entry in parsed.entries:
            try:
                long_id = ( entry.media_content[0]['url'].split('/') [-1].split('.')[0] )
                identifier = long_id.replace('_full','').replace('-full','')

                # Avoid duplicating items on archive.org
                if ia.details(identifier).exists() or ia.details(long_id).exists():
                    console_logger.info('SKIPPING :: %s already exists!' % identifier )
                    continue

                """ CREATE ITEM >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> """
                logging.info('CREATING :: %s' % identifier)
                mkdir(identifier)
                meta_dict = {'description': re.sub('<[^<]+?>', '', entry.description).strip(),
                             'collection': collection_dict[feed],
                             'source': entry.link,
                             'title': entry.title,
                             'licenseurl': 'http://www.nasaimages.org/Terms.html',
                             'date': time.strftime("%Y-%m-%d", entry.updated_parsed),
                             'mediatype': entry.media_content[0]['type'].split('/')[0]}
                # Generate facets, and create subjects
                facet_string = '%s %s %s' % (identifier,
                                             meta_dict['title'],
                                             entry['media_keywords'])
                item_facets = facet.get_facets(facet_string, facet_dict, longest_key)
                facet_list = [x for x in item_facets.itervalues()]
                #facet_list = []
                #for v in item_facets.itervalues():
                #    facet_list.append(v)
                if facet_list:
                    meta_dict['subject'] = ';'.join(facet_list)
                console_logger.info('Generating Metadata files')
                ia.make(meta_dict['identifier'], meta_dict).metadata()
                console_logger.info('Downloading images')
                wget(entry.media_content[0]['url'])
                """ <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< CREATED ITEM """

            except Exception, e:
                logging.error(e)
                pass
if __name__ == "__main__":
    main()
