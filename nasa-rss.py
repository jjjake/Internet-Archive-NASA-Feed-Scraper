#!/usr/bin/env python

import logging,logging.config
import datetime,time
import urllib
import lxml.html
from subprocess import call
from lxml import etree
import re
import os

import feedparser


rootDir = os.getcwd()
logging.config.fileConfig('logging.conf')
cLogger = logging.getLogger('console')

def get_feed_list():
    masterFeedList = "http://www.nasa.gov/rss/internetarchive/index.html"
    parsed = lxml.html.fromstring(urllib.urlopen(masterFeedList).read())
    feedList =  ([link[2] for link in parsed.iterlinks() if link[2].endswith(
                 'rss')])
    feedList = list(set(feedList))
    return feedList

def mkdir(dirname):                                                                                     
    if not os.path.exists(dirname):                                                                     
        os.mkdir(dirname)                                                                               
    os.chdir(dirname)        

def check_archive(identifier):
    url = "http://www.archive.org/services/check_identifier.php?identifier="
    retMessage = etree.parse(url + identifier).getroot().findtext('message')
    if retMessage == 'The identifier you have chosen is available': 
        return 0
    else: 
        return 1

def build_facet_dict():
    facet_file = '/home/jake/facets.txt'
    facet_list = open(facet_file,'rb').read().split('\n')
    dictionary = {}
    max_words_in_key = 0
    for facet in facet_list:
        k,v = facet.split(',')[0], facet.split(',')[-1]
        k = k.strip().lower()
        if not k:
            continue
        words_in_key = len(k.split(' '))
        if words_in_key > max_words_in_key:
            max_words_in_key = words_in_key
        dictionary[k] = v.strip()
    return dictionary, max_words_in_key

def get_phrase(words, phrase_length, start_pos):
    s = ''
    for i in range(phrase_length):
        s += words[start_pos+i] + ' '
        exclude =set(['!', '#', '"', '%', '$', "'", '&', ')', '(', '+', '*', ',',
                      '/', '.', ';', ':', '=', '<', '?', '>', '@', '[', ']', '\\',
                      '^', '`', '{', '}', '|', '~'])
        s = ''.join(ch for ch in s if ch not in exclude)
    return s[:-1]

def get_facets(string, dictionary, longest_key):
    faceted = {}
    words = string.split()
    num_words = len(words)
    pos = 0
    while pos < num_words:
        phrase_length = min(longest_key, num_words-pos)
        found_phrase = False
        while phrase_length > 0:
            phrase = get_phrase(words, phrase_length, pos)
            if phrase.lower() in dictionary:
                found_phrase = phrase.lower()
                break
            phrase_length -= 1
        if False != found_phrase:
            faceted[found_phrase] = dictionary[found_phrase]
            pos += phrase_length
        else:
            pos += 1
    return faceted

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

def make_meta(metaDict):                                                                                 
    f = open("%s_files.xml" % metaDict['identifier'], "wb")                                             
    f.write("</files>")                                                                                 
    f.close()                                                                                           
    root = etree.Element("metadata")                                                                    
    for k,v in metaDict.iteritems():                                                                    
        subElement = etree.SubElement(root,k)                                                           
        subElement.text = v                                                                             
    metaXml = etree.tostring(root, pretty_print=True,                                                   
                             xml_declaration=True, encoding="utf-8")                                    
    print metaXml
    ff = open("%s_meta.xml" % metaDict['identifier'], "wb")                                             
    ff.write(metaXml)                                                                                   
    ff.close()

def wget(mediaLink):
    wget = 'wget -nc %s' % mediaLink
    retcode = call(wget,shell=True)

def main():                                                                  
    mkdir('/1/incoming/tmp/nasa-rss')    
    home = os.getcwd()            

    # Build facet and collection dictionaries.
    facet_dict, longest_key = build_facet_dict()
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
                if check_archive(metaDict['identifier']) != 0: 
                    cLogger.info('the identifier "%s" is not available' % 
                                 metaDict['identifier'] )
                    continue                                  
                mkdir(metaDict['identifier'])                                                           

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
                facets = get_facets(facet_string, facet_dict, longest_key)
                facet_list = []
                for v in facets.itervalues():
                    facet_list.append(v)
                if facet_list:
                    metaDict['subject'] = ';'.join(facet_list)

                make_meta(metaDict)
                wget(entry.media_content[0]['url'])

            except AttributeError:                                                                      
                noMedia = ("%s doesn't appear to have any media!" % 
                           entry.links[0].href)                 
                logging.warning(noMedia)                                                                

            os.chdir(home)           

if __name__ == "__main__":
    main()

