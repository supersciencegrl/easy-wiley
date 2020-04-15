# coding: utf-8

import xml.etree.ElementTree as ET
import requests
import subprocess
import csv

ET.register_namespace('', 'http://purl.org/rss/1.0/')
ET.register_namespace('dc', 'http://purl.org/dc/elements/1.1/')
ET.register_namespace('prism', 'http://prismstandard.org/namespaces/basic/2.0/')
ET.register_namespace('content', 'http://purl.org/rss/1.0/modules/content/')
ET.register_namespace('rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')

journallist = [{'journal': 'Advanced Synthesis & Catalysis', 'shortname': 'AdvSynthCatal', 'url': 'https://onlinelibrary.wiley.com/feed/16154169/most-recent'},
                {'journal': 'Angewandte Chemie International Edition', 'shortname': 'acie', 'url': 'https://onlinelibrary.wiley.com/action/showFeed?jc=15213773&type=etoc&feed=rss'},
                {'journal': 'Chemistry — A European Journal', 'shortname': 'ChemEurJ', 'url': 'https://onlinelibrary.wiley.com/feed/15213765/most-recent'}
                ]

def getxml(url):    
	headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
           'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
           'Accept-Encoding': 'none',
           'Accept-Language': 'en-US,en;q=0.8',
           'Connection': 'keep-alive'}

	response = requests.get(url, headers = headers)
	if response.status_code == 200:
		root = ET.fromstring(requests.get(url, headers = headers).content)
		return root
	else:
		response.raise_for_status()

def getxmlfromfile():
	filename = 'acie.xml'
	tree = ET.parse(filename)
	root = tree.getroot()

	return root

def updaterss(journal, shortname, url, cdate):
    root = getxml(url)

    # Read in old articles
    with open('acie_old.csv', 'rt') as fin:
        reader = csv.reader(fin)
        old_articles = list(reader)

    # Read in RSS articles and remove newer duplicates
    rss_articles = old_articles[:]
    for paper in root[2:][::-1]:
        for doi in paper.findall('{http://prismstandard.org/namespaces/basic/2.0/}doi'):
            doi = doi.text
        if paper.findall('{http://purl.org/dc/elements/1.1/}date'):
            for date in paper.findall('{http://purl.org/dc/elements/1.1/}date'):
                date = date.text
        else:
            date = 'none'

        if [doi, date] not in rss_articles:
            if doi in [i[0] for i in rss_articles]:
                root.remove(paper)
                # Add date to journal_old.csv
                if date == 'none':
                    date = cdate
                    listposition = [i[0] for i in rss_articles].index(doi)
                    if cdate not in rss_articles[listposition]:
                        rss_articles[listposition].append(date)
            else:
                rss_articles.append([doi, date])

    # Change feed title
    if root[0][0].tag.endswith('title'):
        root[0][0].text = f'{journal} (no repeats)'
    if root[0][3].tag.endswith('title'):
        root[0][3].text = f'{journal} (no repeats)'
    if root[0][6].text == f'{journal}':
        root[0][6].text = f'{journal} (no repeats)'

    # Create new RSS feed
    with open(f'{shortname}.xml', 'wb') as fout:
        fout.write(ET.tostring(root))

    # Update old article list
    with open(f'{shortname}_old.csv'.lower(), 'wt', newline = '') as fout:
        writer = csv.writer(fout, quoting = csv.QUOTE_ALL)
        for a in rss_articles:
            b = fout.write((',').join(a) + '\n')

def updatejournals(cdate):
    for j in journallist:
        journal = j['journal']
        shortname = j['shortname']
        url = j['url']
        updaterss(journal, shortname, url, cdate)

def ghpush(commitmsg):
    print(subprocess.check_output('git init'))
    print(subprocess.check_output('git add .'))
    subprocess.run('git commit -m "%s"' % commitmsg)
    subprocess.run('git push origin master')

##{http://purl.org/rss/1.0/}title {}
##{http://purl.org/dc/elements/1.1/}description {}
##{http://purl.org/dc/elements/1.1/}creator {}
##{http://purl.org/rss/1.0/}link {}
##{http://purl.org/rss/1.0/modules/content/}encoded {}
##{http://purl.org/rss/1.0/}description {}
##{http://purl.org/dc/elements/1.1/}title {}
##{http://purl.org/dc/elements/1.1/}identifier {}
##{http://purl.org/dc/elements/1.1/}source {}
##{http://purl.org/dc/elements/1.1/}date {}
##{http://prismstandard.org/namespaces/basic/2.0/}publicationName {}
##{http://prismstandard.org/namespaces/basic/2.0/}doi {}
##{http://prismstandard.org/namespaces/basic/2.0/}url {}
##{http://prismstandard.org/namespaces/basic/2.0/}copyright {}
##{http://prismstandard.org/namespaces/basic/2.0/}section {}
