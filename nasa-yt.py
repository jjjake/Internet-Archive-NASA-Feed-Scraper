#!/usr/bin/env python


""" nasa-yt.py will Download download all of the videos for every channel/user
    listed in the nasa-youtubes text file. It will create a directory:
    'nasa_youtube', and within that directory it will create a directory for 
    each video. It will generate two metadata files: '{identifier}_files.xml'
    and '{identifier}_meta.xml'. The _files.xml file is just a stub file,
    created for the purposes of uploading to archive.org using auto_submit.php.
    The _meta.xml contains a selection of metadata created from the video's 
    Youtube metadata. It is catered to the way archive.org likes things, but
    it is a basic xml file and generally useful.

    TODO:
    * Generalize the script for to work for any Youtube channel/user.

"""


import os
from subprocess import call

import ia



# Create a list of dictionaries, each dictionary containing the metadata for
# the given video item, provided a list of JSON objects for each channel.
#------------------------------------------------------------------------------

def get_meta_list(entry_list):

    # Create a list of metadata dictionaries for each item.
    meta_list = [ {'title': entry['title']['$t'], 
                   'date': entry['published']['$t'][:10],
                   'subject': entry['media$group']['media$keywords']['$t'],
                   'description': entry['media$group']['media$description']['$t'],
                   'videoid': entry['media$group']['yt$videoid']['$t']
                   } for entry in entry_list ]

    return meta_list


#
#------------------------------------------------------------------------------

def main():

    # Load and create the necessary files and directories.
    root_dir = os.getcwd()
    ia.make('nasa_youtube').dir()
    home_dir = os.getcwd()
    collections_file = os.path.join(root_dir, 'nasa-youtubes')
    facet_file = os.path.join(root_dir, 'facets.txt')
    facet = ia.facets(facet_file)
    facet_dict, longest_key = facet.build_dict()

    # Parse the Youtube data into JSON objects.
    for channel in open(collections_file):
        channel_id = channel.split(',')[0]
        collection = channel.split(',')[-1].strip()
        base_url = ('https://gdata.youtube.com/feeds/api/users/%s/uploads' % 
                    channel_id.strip())
        params = { 'v': 2, 'alt': 'json', 'max-results': 50 }
        json_str = ia.parse(base_url, params).json()
        total_results = json_str['feed']['openSearch$totalResults']['$t'] + 50
        feed_updated = json_str['feed']['updated']

        # Create a list of metadata dictionaries. 
        for index in range(0, total_results, 50):
            if index != 0:
                params = { 'v': 2, 'alt': 'json', 'max-results': 50, 
                           'start-index': index }
                json_str = ia.parse(base_url, params).json()
            meta_list = get_meta_list(json_str['feed']['entry'])

            # Create the item.
            for meta_dict in meta_list:
                # Make a pretty identifier, and create the item's directory.
                title_words = meta_dict['title'].lower().split(' ')
                clean_words = '-'.join([ ''.join(x for x in y if x.isalnum()) 
                                         for y in title_words ])
                identifier = '%s-%s' % (clean_words[:68], meta_dict['videoid'])
                ia.make(identifier).dir()
                # Create facets for each item.
                facet_str = "%s %s" % (meta_dict['description'], 
                                       meta_dict['subject'])
                returned_facets = facet.get_facets(facet_str, facet_dict, 
                                                   longest_key)
                meta_dict['subject'] = ';'.join(v for v in returned_facets.values())
                ## Create the meatadata files.
                #ia.make(identifier, meta_dict)
                # Download the video.
                download = ('youtube-dl %s -o %s.%%(ext)s' % 
                            (meta_dict['videoid'], identifier)
                call(download, shell=True)

                os.chdir(home_dir)

if __name__ == "__main__":
    main()
