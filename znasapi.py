#!/1/data/ENV/bin/python

import sys
import urllib2
import simplejson as json

def dataSet(apiQuery):
    url = "http://data.nasa.gov/api/%s" % apiQuery
    p = json.load(urllib2.urlopen(url))
    print json.dumps(p, indent=4)

def main():
    print dataSet(sys.argv[1])

if __name__ == "__main__":
    main()
