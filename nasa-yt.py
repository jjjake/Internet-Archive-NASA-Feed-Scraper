#!/home/jake/.virtualenvs/nasa-ingest/bin/python
import os
from subprocess import call

import logging,logging.config
import ia


ROOT_DIR = os.getcwd()
DOWNLOAD_DIR = '/1/incoming/tmp/nasa_youtube'
COLLECTIONS_FILE = os.path.join(ROOT_DIR, 'nasa-youtubes')
FACET_FILE = os.path.join(ROOT_DIR, 'facets.txt')
mkdir = lambda x: os.mkdir(x) if not os.path.exists(x) else None

logging.config.fileConfig('logging.conf')
console_logger = logging.getLogger('console')


#______________________________________________________________________________
def get_meta_list(entry_list):
    return [{'title': entry['title']['$t'],
             'date': entry['published']['$t'][:10],
             'subject': entry['media$group']['media$keywords']['$t'],
             'description': entry['media$group']['media$description']['$t'],
             'videoid': entry['media$group']['yt$videoid']['$t']
            } for entry in entry_list ]

#______________________________________________________________________________
def get_channel_list():
    channel_list = []
    for channel in open(COLLECTIONS_FILE):
        url = ('https://gdata.youtube.com/feeds/api/users/%s/uploads' %
               channel.split(',')[0])
        collection = channel.split(',')[-1].strip()
        channel_list.append((url,collection))
    return channel_list

#______________________________________________________________________________
def main():
    mkdir(DOWNLOAD_DIR)
    facet = ia.facets(FACET_FILE)
    facet_dict, longest_key = facet.build_dict()

    # CHANNEL FEED ____________________________________________________________
    for base_url, collection in get_channel_list():
        os.chdir(DOWNLOAD_DIR)
        params = { 'v': 2, 'alt': 'json', 'max-results': 50 }
        json_str = ia.parse(base_url, params).json()
        total_results = json_str['feed']['openSearch$totalResults']['$t'] + 50
        feed_updated = json_str['feed']['updated']

        # CHANNEL PAGE ________________________________________________________
        for index in range(0, total_results, 50):
            if index != 0:
                params = { 'v': 2, 'alt': 'json', 'max-results': 50,
                           'start-index': index }
                json_str = ia.parse(base_url, params).json()
            meta_list = get_meta_list(json_str['feed']['entry'])

            # CREATE ITEM _____________________________________________________
            for meta_dict in meta_list:
                title_words = meta_dict['title'].lower().split(' ')
                clean_words = '-'.join([ ''.join(x for x in y if x.isalnum())
                                         for y in title_words ])
                identifier = '%s-%s' % (clean_words[:68], meta_dict['videoid'])

                if ia.details(identifier).exists():
                    console_logger.info('SKIPPING :: %s already exists!' % identifier)
                    continue

                logging.info('CREATING :: %s' % identifier)
                mkdir(identifier)
                os.chdir(identifier)

                # FACETS ______________________________________________________
                facet_str = "%s %s" % (meta_dict['description'],
                                       meta_dict['subject'])
                returned_facets = facet.get_facets(facet_str, facet_dict,
                                                   longest_key)
                meta_dict['subject'] = ';'.join(v for v in
                                                returned_facets.values())
                meta_dict['collection'] = collection
                meta_dict['mediatype'] = 'movies'

                # WRITE // DOWNLOAD ___________________________________________
                ia.make(identifier, meta_dict).metadata()
                download = ('youtube-dl -c "%s" -o "%s.%%(ext)s"' %
                            (meta_dict['videoid'], identifier))
                call(download, shell=True)

if __name__ == "__main__":
    main()
