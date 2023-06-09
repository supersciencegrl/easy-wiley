import csv
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

import requests

def getxml(url: str):   
    """
    Retrieve XML data from the given URL and parse it into an ElementTree.

    Args:
        url (str): The URL of the XML data.

    Returns:
        xml.etree.ElementTree.Element: The root element of the parsed XML.

    Raises:
        requests.HTTPError: If the request to the URL fails.

    """ 
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
           'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
           'Accept-Encoding': 'none',
           'Accept-Language': 'en-US,en;q=0.8',
           'Connection': 'keep-alive'}

    response = requests.get(url, headers = headers)
    if response.status_code == 200:
        root = ET.fromstring(response.content)
        return root
    else:
        response.raise_for_status()

def read_old_articles(filename: Path):
    """
    Read in old articles as doi's and datetimes from a CSV file.

    Args:
        filename (Path): The path to the CSV file.

    Returns:
        list: List of old article doi-datetime pairs read from the CSV file.

    """
    with open(filename, 'rt') as fin:
        reader = csv.reader(fin)
        old_articles = list(reader)
    return old_articles

def update_rss_articles(root, old_articles, cdate):
    """
    Update the RSS articles and remove duplicates.

    Args:
        root (xml.etree.ElementTree.Element): The root element of the XML.
        old_articles (list): List of old articles as doi-datetime pairs.
        cdate (str): Current date.

    Returns:
        list: Updated list of RSS articles.

    """
    rss_articles = old_articles[:]
    for n, paper in enumerate(root[0][2:][::-1]):
        for doi in paper.findall('{http://prismstandard.org/namespaces/basic/2.0/}doi'):
            doi = doi.text
        if paper.findall('{http://purl.org/dc/elements/1.1/}date'):
            for date in paper.findall('{http://purl.org/dc/elements/1.1/}date'):
                if 'T' in date.text:
                    date = date.text[:10]
                else:
                    date = date.text
        else:
            date = 'none'

        if [doi, date] not in rss_articles:
            if doi in [i[0] for i in rss_articles]:
                try:
                    root.remove(paper)
                except ValueError:
                    pass
                if date == 'none':
                    date = cdate
                    listposition = [i[0] for i in rss_articles].index(doi)
                    if cdate not in rss_articles[listposition]:
                        try:
                            existingdate = rss_articles[listposition][1]
                            if existingdate.count('-') != 2:
                                rss_articles[listposition][1] = date
                        except IndexError:
                            rss_articles[listposition].append(date)
            else:
                rss_articles.append([doi, date])

    return rss_articles

def update_feed_title(root, journal):
    """
    Change the feed title in the XML.

    Args:
        root (xml.etree.ElementTree.Element): The root element of the XML.
        journal (str): Journal name.

    """
    for i, elem in enumerate(root[0]):
        if elem.tag == 'item':
            break
        elif elem.tag.endswith('title') or elem.text == journal:
            root[0][i].text = f'{journal} (no repeats)'

def create_new_rss_feed(root, shortname):
    """
    Create a new RSS feed by writing the XML to a file.

    Args:
        root (xml.etree.ElementTree.Element): The root element of the XML.
        shortname (str): The shortname used for the filename.

    """
    with open(f'{shortname}.xml', 'wb') as fout:
        newstring = ET.tostring(root).replace(b'pericles.pericles-prod.literatumonline.com', b'onlinelibrary.wiley.com')
        newstring = newstring.replace(b'onlinelibrary.wiley.com/doi/abs', b'doi.org')
        newstring = newstring.replace(b'www.', b'').replace(b'?af=R', b'')
        fout.write(newstring)

def update_old_article_list(filename: Path, rss_articles: list):
    """
    Update the old article list by writing it to a CSV file.

    Args:
        filename (Path): The path to the CSV file.
        rss_articles (list): List of RSS articles.

    """
    with open(filename, 'wt', newline='') as fout:
        writer = csv.writer(fout, quoting=csv.QUOTE_ALL)
        for a in rss_articles:
            writer.writerow(a)

def updaterss(journal: str, shortname: str, url: str, cdate: str):
    """
    Update the RSS feed for a journal with new articles.

    Args:
        journal (str): The name of the journal.
        shortname (str): The shortname used for filenames.
        url (str): The URL to fetch the XML data from.
        cdate (str): The current date.

    """
    root = getxml(url)

    old_articles = read_old_articles(f'{shortname.lower()}_old.csv')
    rss_articles = update_rss_articles(root, old_articles, cdate)

    update_feed_title(root, journal)
    create_new_rss_feed(root, shortname)
    update_old_article_list(Path(f'{shortname.lower()}_old.csv'), rss_articles)

def update_journals(cdate: str):
    """
    Update the RSS feeds for multiple journals.

    Args:
        cdate (str): The current date.

    """
    for j in journal_list:
        journal = j['journal']
        shortname = j['shortname']
        url = j['url']
        updaterss(journal, shortname, url, cdate)

## Debugging functions
def get_xml_from_file(filepath: Path=Path('acie.xml')):
    """
    Retrieve XML data from the given file and parse it into an ElementTree.

    Args:
        filename (Path): The path to the XML file. Default is Path('acie.xml')

    Returns:
        xml.etree.ElementTree.Element: The root element of the parsed XML.

    Raises:
        FileNotFoundError: If the file is not found.

    """
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
    except FileNotFoundError:
        raise FileNotFoundError(f"File '{filepath}' not found.")

    return root

def github_push(commitmsg: str):
    """
    Push local changes to a GitHub repository.

    Args:
        commitmsg (str): The commit message for the changes.

    Raises:
        subprocess.CalledProcessError: If any of the Git commands fail.

    """
    print(subprocess.check_output('git init'))
    print(subprocess.check_output('git add .'))
    subprocess.run('git commit -m "%s"' % commitmsg)
    subprocess.run('git push origin master')

# encoding: utf-8

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

ET.register_namespace('', 'http://purl.org/rss/1.0/')
ET.register_namespace('atom', 'http://www.w3.org/2005/Atom')
ET.register_namespace('content', 'http://purl.org/rss/1.0/modules/content/')
ET.register_namespace('dc', 'http://purl.org/dc/elements/1.1/')
ET.register_namespace('prism', 'http://prismstandard.org/namespaces/basic/2.0/')
ET.register_namespace('rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')

journal_list = [ {'journal': 'Advanced Materials', 'shortname': 'AdvMater', 'url': 'https://onlinelibrary.wiley.com/feed/15214095/most-recent'},
                {'journal': 'Advanced Synthesis & Catalysis', 'shortname': 'AdvSynthCatal', 'url': 'https://onlinelibrary.wiley.com/feed/16154169/most-recent'},
                {'journal': 'Angewandte Chemie International Edition', 'shortname': 'acie', 'url': 'https://onlinelibrary.wiley.com/feed/15213773/most-recent'},
                {'journal': 'Chemistry — A European Journal', 'shortname': 'ChemEurJ', 'url': 'https://onlinelibrary.wiley.com/feed/15213765/most-recent'},
                {'journal': 'ChemBioChem', 'shortname': 'ChemBioChem', 'url': 'https://onlinelibrary.wiley.com/feed/14397633/most-recent'},
		{'journal': 'European Journal of Chemistry', 'shortname': 'ejoc', 'url': 'https://onlinelibrary.wiley.com/feed/10990690/most-recent'}
                ]