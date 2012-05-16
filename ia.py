#!/usr/bin/env python

import os
import requests
import simplejson
from urllib import urlencode
from lxml import etree
import re
import lxml.html


class details:

    def __init__(self, item):
        self.item = item
        self.request = requests.get('http://archive.org/metadata/%s' %
                                    self.item)
        self.headers = self.request.headers
        self.json_str = simplejson.loads(self.request.content)

    def files(self):
        return self.json_str['files']
    def metadata(self):
        return self.json_str['metadata']
    def reviews(self):
        return self.json_str['reviews']
    def server(self):
        return self.json_str['server']
    def dir(self):
        return self.json_str['dir']

    def exists(self):
        if self.json_str == None:
            return 0
        if self.json_str != None:
            return 1


class parse:

    def __init__(self, url, params=None):
        self.request = requests.get(url=url, params=params)

    def json(self):
        self.json_str = simplejson.loads(self.request.content)
        return self.json_str

    def html(self):
        self.html = lxml.html.fromstring(self.request.content)
        return self.html

    def html_links(self):
        links = [ x for x in self.html().iterlinks() ]
        return links


class make:

    def __init__(self, identifier, meta_dict=None):
        self.identifier = identifier
        if meta_dict:
            self.meta_dict = dict((k,v) for k,v in meta_dict.items() if v != '')

    def metadata(self):
        f = open("%s_files.xml" % self.identifier, "wb")
        f.write("<files />")
        f.close()
        root = etree.Element("metadata")
        for k,v in self.meta_dict.iteritems():
            subElement = etree.SubElement(root,k)
            subElement.text = v
        metaXml = etree.tostring(root, pretty_print=True,
                                 xml_declaration=True, encoding="utf-8")
        ff = open("%s_meta.xml" % self.identifier, "wb")
        ff.write(metaXml)
        ff.close()

    def dir(self):
        if not os.path.exists(self.identifier):
            os.mkdir(self.identifier)
        os.chdir(self.identifier)


class perpetual_loop:

    def __init__(self, log_home, data_home):
        self.home = log_home
        self.data_home = data_home
        self.ready_fname = os.path.join(self.home, 'ready_list.txt')
        self.lock_fname = os.path.join(self.home, 'ready_list.txt.lck')

    def start(self):
        ### Exit if last list still pending, wait for it to be renamed/removed.
        if os.access( self.ready_fname, os.F_OK ) is True:
            print ( 'ABORT: %s exists (Not picked up yet? Should be renamed'
                    ' when retrieved by auto_submit loop!)' % self.ready_fname )
            if os.access( self.lock_fname, os.F_OK ) is True:
                os.remove(self.lock_fname)
            exit(0)
        ### If lock file exists, another process is already generating the list
        if os.access( self.lock_fname, os.F_OK ) is True:
            print ( 'ABORT: %s lockfile exists (Another process generating list'
                    'already? Should be deleted when complete!)' % self.lock_fname )
            exit(0)
        ### Touch a lock and list file.
        touchLi = open(self.ready_fname,'wb')
        touchLi.write('')
        touchLi.close()
        touchLo = open(self.lock_fname, 'wb')
        touchLo.write('')
        touchLo.close()

    def end(self):
        os.chdir(self.home)
        data_list = os.listdir(self.data_home)
        f = open(self.ready_fname,'wb')
        f.write('\n'.join(data_list))
        f.close()
        os.remove(self.lock_fname)


class facets:

    def __init__(self, facet_file):
        self.facet_file = facet_file
        self.dictionary = {}
        self.max_words_in_key = 0

    def build_dict(self):
        facet_list = open(self.facet_file,'rb').read().split('\n')
        for facet in facet_list:
            k,v = facet.split(',')[0], facet.split(',')[-1]
            k = k.strip().lower()
            if not k:
                continue
            words_in_key = len(k.split(' '))
            if words_in_key > self.max_words_in_key:
                self.max_words_in_key = words_in_key
            self.dictionary[k] = v.strip()
        return self.dictionary, self.max_words_in_key

    def get_phrase(self, words, phrase_length, start_pos):
        s = ''
        exclude =set(['!', '#', '"', '%', '$', "'", '&', ')', '(', '+', '*', ',',
                      '/', '.', ';', ':', '=', '<', '?', '>', '@', '[', ']', '\\',
                      '^', '`', '{', '}', '|', '~'])
        for i in range(phrase_length):
            s += words[start_pos+i] + ' '
            s = ''.join(ch for ch in s if ch not in exclude)
        return s[:-1]

    def get_facets(self, string, dictionary, longest_key):
        faceted = {}
        words = string.split()
        num_words = len(words)
        pos = 0

        while pos < num_words:
            phrase_length = min(longest_key, num_words-pos)
            found_phrase = False
            while phrase_length > 0:

                phrase = self.get_phrase(words, phrase_length, pos)
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
