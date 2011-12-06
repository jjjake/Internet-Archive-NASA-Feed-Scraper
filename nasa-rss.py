#!/1/data/ENV/bin/python

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
    ff = open("%s_meta.xml" % metaDict['identifier'], "wb")                                             
    ff.write(metaXml)                                                                                   
    ff.close()

def wget(mediaLink):
    wget = '"wget -nc %s"' % mediaLink
    retcode = call(wget,shell=True)

def main():                                                                  
    mkdir('nasa-rss')    
    home = os.getcwd()            
    for feed in getFeedList():
        parsed = feedparser.parse(feed)                                                                 
        print '\n\n------------------------\n\n'                                                        
        if parsed.bozo == 1: logging.warning('%s is a bozo!' % feed)                                    
        for entry in parsed.entries:                                                                    
            metaDict = {}                                                                               
            try:                                                                                        
                metaDict['fname'] = entry.media_content[0]['url'].split('/')[-1]                        
                identifier = ( entry.media_content[0]['url'].split('/')
                               [-1].split('.')[0] )
                metaDict['identifier'] = identifier.replace('_full','')
                if checkArchive(metaDict['identifier']) != 0: continue                                  
                mkdir(metaDict['identifier'])                                                           
                ### re.sub('<[^<]+?> strips HTML tags from description                                  
                metaDict['description'] = re.sub('<[^<]+?>', '', entry.description)                     
                metaDict['source'] = entry.link                                                         
                metaDict['title'] = entry.title                                                         
                metaDict['licenseurl'] = 'http://www.nasaimages.org/Terms.html'                         
                metaDict['date'] = time.strftime("%Y-%m-%d", entry.updated_parsed)                      
                metaDict['mediatype'] = entry.media_content[0]['type'].split('/')[0]
                makeMeta(metaDict)
                wget(entry.media_content[0]['url'])
            except AttributeError:                                                                      
                noMedia = "%s doesn't appear to have any media!" % entry.links[0].href                  
                logging.warning(noMedia)                                                                
            os.chdir(home)           

if __name__ == "__main__":
    main()

