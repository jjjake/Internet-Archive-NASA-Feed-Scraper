#!/opt/local/bin/python

import logging,logging.config
#import datetime,time
import urllib
#from subprocess import call
from lxml import etree
#import re
import os

#import feedparser


logging.config.fileConfig('logging.conf')
cLogger = logging.getLogger('console')

def parseChannel(channel):
    xml = "https://gdata.youtube.com/feeds/api/users/%s/uploads?v=2" % (channel)
    parsed = etree.parse(urllib.urlopen(xml)) 
    return parsed

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
    wget = 'wget -nc %s' % mediaLink
    retcode = call(wget,shell=True)

def main():                                                                  
    #mkdir('nasa-rss')    
    home = os.getcwd()            
    print(etree.tostring(parseChannel('nasaeclips'), pretty_print=True))

if __name__ == "__main__":
    main()

