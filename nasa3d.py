#!/usr/bin/env python

import os
from sets import Set
from lxml import etree
from subprocess import call

import ia


# Parse the HTML for each item, and put it into set.
#_____________________________________________________________________________

def get_item_set():
    base_url = 'http://www.nasa.gov'
    index_url = base_url + '/multimedia/3d_resources/models.html'
    html = ia.parse(index_url).html()
    html_links = ia.parse(index_url).html_links()
    
    # Create a set consisting of parsed HTML objects for each item.
    link_set = Set((base_url + link[-2]) for link in html_links 
                   if link[-2].startswith('/multimedia/3d_resources/'))
    item_set = Set(ia.parse(link).html() for link in link_set)

    return item_set


# Parse the HTML for each item, and put it into set.
#_____________________________________________________________________________

def main():

    root_dir = os.getcwd()
    ia.make('nasa_3d').dir()
    home = os.getcwd()

    # Build facet and collection dictionaries.
    facet_file = os.path.join(root_dir,'facets.txt')
    facet = ia.facets(facet_file)
    facet_dict, longest_key = facet.build_dict()

    for item in get_item_set():

        meta_list = [ item[0].findall('meta') ]
        meta_dict = {}
        for tags in meta_list:
            nasa_dict = {(x.get('name')): (x.get('content')) for x in tags}

        try:
            title = nasa_dict['bn_title']
        except KeyError:
            continue

        nasa_id = nasa_dict['CMS Document Id']
        identifier = '%s-%s' % ((''.join(ch for ch in title if 
                                 ch.isalnum())).lower(), nasa_id)

        # Filter subjects through faceting machine.
        facet_string = nasa_dict['dc.subject']
        returned_facets = facet.get_facets(facet_string, facet_dict, 
                                           longest_key)
        meta_dict['subject'] = ';'.join(returned_facets[k] for k in
                                        returned_facets.keys())

        meta_dict['title'] = title
        meta_dict['collection'] = 'nasa-3d-resources'
        meta_dict['licenseurl'] = 'http://www.nasa.gov/audience/formedia/features/MP_Photo_Guidelines.html'
        meta_dict['description'] = nasa_dict['dc.description']
        meta_dict['source'] = nasa_dict['dc.identifier']
        meta_dict['contributor'] = nasa_dict['dc.publisher']
        meta_dict['date'] = nasa_dict['dc.date.modified']
        meta_dict = {i:j for i,j in meta_dict.items() if j != ''}

        print 'creating: ' + identifier

        # Create the item.
        ia.make(identifier).dir()
        ia.make(identifier, meta_dict).metadata()

        # Download files.
        thumbnail = item.xpath('//img')[-1].attrib['src']
        thumbnail_url = 'http://www.nasa.gov%s' % thumbnail
        zip_file = item.xpath('//button')[0].attrib['onclick'].split("'")[-2]
        zip_url = 'http://www.nasa.gov%s' % zip_file

        wget_source = 'wget -q -nc %s' % (zip_url)
        wget_thumb = 'wget -q -c %s -O %s' % (thumbnail_url, 
                                               identifier + '_thumb.jpg')
        call(wget_source, shell=True)
        call(wget_thumb, shell=True)
        os.chdir(home)

if __name__ == "__main__":
    main()
