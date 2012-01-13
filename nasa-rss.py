#!/usr/bin/env python


"""
Facets: petabox/sw/nasa/facets/driver.pl
./driver.pl --rule $facet_file --metadata $metadata_file --output $outputfile --ignorefile $ignore_path/$ignore_file --archivemode --unfilteredfile $unfilteredfile 2> /dev/null";
"""

import logging,logging.config
import datetime,time
import urllib
import lxml.html
from subprocess import call
from lxml import etree
import re
import os

import feedparser


logging.config.fileConfig('logging.conf')
cLogger = logging.getLogger('console')

def getFeedList():
    masterFeedList = "http://www.nasa.gov/rss/internetarchive/index.html"
    parsed = lxml.html.fromstring(urllib.urlopen(masterFeedList).read())
    feedList =  ([link[2] for link in parsed.iterlinks() if link[2].endswith(
                 'rss')])
    feedList = list(set(feedList))
    return feedList

def checkArchive(identifier):
    url = "http://www.archive.org/services/check_identifier.php?identifier="
    retMessage = etree.parse(url + identifier).getroot().findtext('message')
    if retMessage == 'The identifier you have chosen is available': return 0
    else: return 1

def mkdir(dirname):                                                                                     
    if not os.path.exists(dirname):                                                                     
        os.mkdir(dirname)                                                                               
    os.chdir(dirname)        

def facet_dict(string):
    facet_list = open('/Users/jake/Desktop/Internet-Archive-NASA-Feed-Scraper/facets.txt','rb').read().split('\n')
    dictionary = {}
    for facet in facet_list:
        k,v = facet.split(',')[0], facet.split(',')[-1]
        dictionary[k] = v
    faceted = {}
    for k,v in dictionary.iteritems():
        if k in string:
            faceted[k] = v
    return faceted

def makeMeta(metaDict):                                                                                 
    f = open("%s_files.xml" % metaDict['identifier'], "wb")                                             
    f.write("</files>")                                                                                 
    f.close()                                                                                           
    root = etree.Element("metadata")                                                                    
    for k,v in metaDict.iteritems():                                                                    
        subElement = etree.SubElement(root,k)                                                           
        subElement.text = v                                                                             
    metaXml = etree.tostring(root, pretty_print=True,                                                   
                             xml_declaration=True, encoding="utf-8")                                    
    return metaXml
    ff = open("%s_meta.xml" % metaDict['identifier'], "wb")                                             
    ff.write(metaXml)                                                                                   
    ff.close()

def wget(mediaLink):
    wget = 'wget -nc %s' % mediaLink
    retcode = call(wget,shell=True)

def main():                                                                  
    mkdir('nasa-rss')    
    home = os.getcwd()            
    for feed in getFeedList():
        parsed = feedparser.parse(feed)                                                                 
        if parsed.bozo == 1: logging.warning('%s is a bozo!' % feed)                                    
        for entry in parsed.entries:                                                                    
            metaDict = {}                                                                               
            try:                                                                                        
                #metaDict['fname'] = entry.media_content[0]['url'].split('/')[-1]                        
                identifier = ( entry.media_content[0]['url'].split('/')
                               [-1].split('.')[0] )
                metaDict['identifier'] = identifier.replace('_full','')
                if checkArchive(metaDict['identifier']) != 0: 
                    cLogger.info('the identifier "%s" is not available' % 
                                 metaDict['identifier'] )
                    continue                                  
                mkdir(metaDict['identifier'])                                                           
                ### re.sub('<[^<]+?> strips HTML tags from description                                  
                metaDict['description'] = re.sub('<[^<]+?>', '', entry.description).strip()
                metaDict['source'] = entry.link                                                         
                metaDict['title'] = entry.title                                                         
                metaDict['licenseurl'] = 'http://www.nasaimages.org/Terms.html'                         
                metaDict['date'] = time.strftime("%Y-%m-%d", entry.updated_parsed)                      
                metaDict['mediatype'] = entry.media_content[0]['type'].split('/')[0]

                # Generate facets, and create subjects
                facet_string = '%s %s %s' % (metaDict['description'],metaDict['title'],entry['media_keywords'])
                fdict = facet_dict(metaDict['description'])
                fl = []
                for k,v in fdict.iteritems():
                    if k:
                        fl.append(('%s %s' % (v,k)))
                if fl:
                    metaDict['subject'] = ';'.join(fl)

                makeMeta(metaDict)
                wget(entry.media_content[0]['url'])
            except AttributeError:                                                                      
                noMedia = "%s doesn't appear to have any media!" % entry.links[0].href                  
                logging.warning(noMedia)                                                                
            os.chdir(home)           

if __name__ == "__main__":
    main()

