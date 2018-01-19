import requests
import json
import os
from lxml import html
from glob import glob

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Do not change the order of the list, only append to it
resources = [
    {
        'url': 'https://raw.githubusercontent.com/unicode-cldr/cldr-localenames-full/master/main/en/territories.json',
        'dst': 'cldr-localenames-territories.json'
    },
    {
        'url': 'https://en.wikipedia.org/wiki/ISO_3166-1',
        'dst': 'wikipedia-iso-3166.html'
    },
    {
        'url': 'http://download.geonames.org/export/dump/countryInfo.txt',
        'dst': 'geonames-country-info.txt'
    }
]

def download_resource(resource, force=False):
    print('+ Downloading {}'.format(resource['dst']))

    dst_path = os.path.join(ROOT, 'data', resource['dst'] + '.tmp')
    if os.path.exists(dst_path) and not force:
        return dst_path
    with open(dst_path, 'wb') as out_file:
        resp = requests.get(resource['url'])
        out_file.write(resp.content)
    return dst_path


ISO3166_COUNT = 249
def process_iso3166():
    """
    The output format of items is:
     ['Afghanistan', 'AF', 'AFG', '004']
     or
    Country name, alpha2, alpha3, numeric
    """
    src_path = os.path.join(ROOT, 'data', resources[1]['dst'] + '.tmp')

    with open(src_path) as in_file:
        tree = html.fromstring(in_file.read())

    items = []
    for el in tree.xpath('//table'):
        if el.xpath('./tr/th/text()')[0] == 'English short name (upper/lower case)':
            for tr in el.xpath('./tr'):
                items.append([td.text_content() for td in tr.xpath('./td')])

    def filter_empty(x):
        return len(x) != 0
    def map_fields(x):
        return x[:4]

    items = list(map(map_fields, filter(filter_empty, items)))
    if len(items) != ISO3166_COUNT:
        print('{} != {}'.format(len(items), ISO3166_COUNT))
        raise Exception('Inconsistency in country count')

    return items

def process_territories():
    src_path = os.path.join(ROOT, 'data', resources[0]['dst'] + '.tmp')
    with open(src_path) as in_file:
        obj = json.load(in_file)
    return obj['main']['en']['localeDisplayNames']['territories']

def process_geonames_country_info():
    src_path = os.path.join(ROOT, 'data', resources[2]['dst'] + '.tmp')
    obj = {}
    with open(src_path) as in_file:
        for line in in_file.readlines():
            if line[0] == '#' or line[0] == '\n':
                continue
            p = line.split('\t')
            # Keyed on alpha2
            # capital, continent code, tld, languages
            if p[0] in obj:
                raise Exception('Detected a dupe')
            obj[p[0]] = [
                p[5], p[8], p[9], p[15]
            ]
    return obj

def join_all(iso3166_list, territories, geonames_country_info):
    items = []
    for iso_name, alpha2, alpha3, num in iso3166_list:
        name = territories[alpha2]
        capital, continent, tld, languages = geonames_country_info[alpha2]
        entry = {
            'iso3166_alpha2': alpha2,
            'iso3166_alpha3': alpha2,
            'iso3166_num': num,
            'iso3166_name': iso_name,
            'name': name,
            'languages': languages.split(','),
            'tld': tld,
            'capital': capital,
            'continent': continent
        }
        items.append(entry)
    sorted(items, key=lambda x: x['name'])
    return items

def process_all():
    territories = process_territories()
    country_list = join_all(process_iso3166(),
                            territories,
                            process_geonames_country_info())
    print('+ Writing territory-names.json')
    with open(os.path.join(ROOT, 'data', 'territory-names.json'), 'w') as out_file:
        json.dump(territories, out_file)
    print('+ Writing country-list.json')
    with open(os.path.join(ROOT, 'data', 'country-list.json'), 'w') as out_file:
        json.dump(country_list, out_file)

def clean():
    for path in glob(os.path.join(ROOT, 'data', '*.tmp')):
        os.remove(path)

def main():
    #clean()
    for resource in resources:
        download_resource(resource)
    process_all()

if __name__ == '__main__':
    main()