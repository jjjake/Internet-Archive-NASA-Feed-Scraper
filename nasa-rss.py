#!/usr/bin/env python

import logging,logging.config
import datetime,time
import urllib
import lxml.html
from subprocess import call
import re
import os

import feedparser

import ia


root_dir = os.getcwd()
logging.config.fileConfig('logging.conf')
cLogger = logging.getLogger('console')

def get_feed_list():
    masterFeedList = "http://www.nasa.gov/rss/internetarchive/index.html"
    parsed = lxml.html.fromstring(urllib.urlopen(masterFeedList).read())
    feedList =  ([link[2] for link in parsed.iterlinks() if link[2].endswith(
                 'rss')])
    feedList = list(set(feedList))
    return feedList

def build_collection_dict():
    collection_file = '/home/jake/rsscollections.txt'
    collection_list = open(collection_file,'rb').read().split('\n')
    dictionary = {}
    for collection in collection_list:
        k,v = collection.split(',')[0], collection.split(',')[-1]
        dictionary[v] = k
        if not k:
            continue
    return dictionary

def wget(mediaLink):
    wget = 'wget -q -nc %s' % mediaLink
    retcode = call(wget,shell=True)

def main():                                                                  
    ia.make('/1/incoming/tmp/nasa-rss').dir()
    home = os.getcwd()            

    # Build facet and collection dictionaries.
    facet_file = os.path.join(root_dir, 'facets.txt')
    facet = ia.facets(facet_file)
    facet_dict, longest_key = facet.build_dict()
    collection_dict = build_collection_dict()

    for feed in get_feed_list():
        parsed = feedparser.parse(feed)                                                                 
        if parsed.bozo == 1: 
            logging.warning('%s is a bozo!' % feed)                                    
        for entry in parsed.entries:                                                                    
            metaDict = {}                                                                               

            try:                                                                                        
                identifier = ( entry.media_content[0]['url'].split('/')
                               [-1].split('.')[0] )
                metaDict['identifier'] = identifier.replace('_full','')
                print '\n\n~~~~\n\nCreating item: %s\n\n' % metaDict['identifier']

                if ia.details(metaDict['identifier']).exists():
                    cLogger.info('the identifier "%s" is not available' %
                                 metaDict['identifier'] )
                    continue

                ia.make(metaDict['identifier']).dir()

                # re.sub('<[^<]+?> strips HTML tags from description                                  
                metaDict['description'] = re.sub('<[^<]+?>', '', 
                                                 entry.description).strip()
                metaDict['collection'] = collection_dict[feed]
                metaDict['source'] = entry.link                                                         
                metaDict['title'] = entry.title                                                         
                metaDict['licenseurl'] = 'http://www.nasaimages.org/Terms.html'                         
                metaDict['date'] = time.strftime("%Y-%m-%d", entry.updated_parsed)                      
                metaDict['mediatype'] = entry.media_content[0]['type'].split('/')[0]

                # Generate facets, and create subjects
                facet_string = '%s %s %s' % (metaDict['description'],
                                             metaDict['title'],
                                             entry['media_keywords'])
                facet_dict = facet.get_facets(facet_string, facet_dict, longest_key)
                facet_list = []
                for v in facet_dict.itervalues():
                    facet_list.append(v)
                if facet_list:
                    metaDict['subject'] = ';'.join(facet_list)

                cLogger.info('Generating Metadata files')
                ia.make(metaDict['identifier'], metaDict).metadata()
                cLogger.info('Downloading images')
                wget(entry.media_content[0]['url'])

            except AttributeError:                                                                      
                noMedia = ("%s doesn't appear to have any media!" % 
                           entry.links[0].href)                 
                logging.warning(noMedia)                                                                

            os.chdir(home)           

if __name__ == "__main__":
    main()

