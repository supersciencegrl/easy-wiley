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

def read_old_articles(filename: Path) -> list[list[str, str]]:
    """
    Read in old articles as doi's and datetimes from a CSV file and return them 
    as a list of lists. 

    Args:
        filename (Path): The path to the CSV file.

    Returns:
        list[list[str, str]]: A list of lists, where each inner list represents a 
                              doi-datetime pair read from the csv file.
    """
    with open(filename, 'rt') as fin:
        reader = csv.reader(fin)
        old_articles = list(reader)
    return old_articles

def extract_doi_and_date(paper: ET.Element, cdate: str) -> tuple[str, str]:
    """
    Extracts the DOI and publication date from an XML element representing a paper.
    
    Args:
        paper (ET.Element): The XML element representing a paper.
        cdate (str): The current date in 'YYYY-MM-DD' format to use if no date is found.

    Returns:
        tuple[str, str]: A tuple containing the DOI and the date.
    """
    # Extract DOI
    for doi in paper.findall('{http://prismstandard.org/namespaces/basic/2.0/}doi'):
        doi = doi.text
        # Extract article date, or default to 'none' if not found
        if paper.findall('{http://purl.org/dc/elements/1.1/}date'):
            for date in paper.findall('{http://purl.org/dc/elements/1.1/}date'):
                # Trim time portion of datetime if present
                date = date.text[:10] if 'T' in date.text else date.text
        else:
            date = 'none'
    
    return doi, date

def update_with_new_date(rss_articles: list[list[str, str]], doi: str, date: str):
    """
    Updates an RSS article's date if the specified DOI is found and the date needs to be changed.

    This function searches for the specified DOI in the list of RSS articles. If the DOI is found
    and the new date is not already present, it updates the existing date if it's not in the 'YYYY-MM-DD'
    format. If no date exists for the DOI, it appends the new date.

    Args:
        rss_articles (list[list[str, str]]): A list of articles, where each article is represented by 
                                             a list containing a DOI and a date.
        doi (str): The DOI of the article to update.
        date (str): The new date to be set for the article.
    """
    idx = [i[0] for i in rss_articles].index(doi) # Indices where doi appears
    if date not in rss_articles[idx]:
        try:
            existing_date = rss_articles[idx][1]
            # If existing date not in standard format, update it
            if existing_date.count('-') != 2: 
                rss_articles[idx][1] = date
        except IndexError:
            rss_articles[idx].append(date)

def update_rss_articles(root: ET.Element, old_articles: list[list[str, str]], cdate: str) -> list[list[str, str]]:
    """
    Updates the list of RSS articles by adding new articles from the XML root element and 
    removing duplicates.

    Args:
        root (xml.etree.ElementTree.Element): The root element of the XML document 
                                              containing RSS articles.
        old_articles (list[list[str, str]]): A list of lists, where each inner list 
                                             represents a doi-datetime pair 
                                             corresponding to an old article. 
        cdate (str): The current date in 'YYYY-MM-DD' format. 

    Returns:
        list[list[str, str]]: Updated list of RSS articles.
    """
    # Create copy of old articles list to return later
    rss_articles = old_articles[:]

    # Iterate over the XML articles in reverse order
    for paper in root[0][2:][::-1]: 
        doi, date = extract_doi_and_date(paper, cdate)

        # Check the doi-date pair isn't already in the list
        if [doi, date] not in rss_articles:
            # If the doi is in the list but with a different date, update the entry
            if doi in [i[0] for i in rss_articles]:
                try:
                    root.remove(paper) # Remove duplicate paper from xml
                except ValueError:
                    pass
                # Use today's date if none available
                if date == 'none':
                    update_with_new_date(rss_articles, doi, cdate)
            else:
                # Add new [doi, date] pair to the article list
                rss_articles.append([doi, date])

    return rss_articles

def update_feed_title(root: ET.Element, journal: str):
    """
    Updates the feed title in an XML document to reflect the journal's name with a suffix.

    This function iterates over the elements of the XML document's root and changes the text
    of the first title element or any element with text matching the journal name to 
    f"{journal} (no repeats)" until it encounters an 'item' element.

    Args:
        root (ET.Element): The root element of the XML document.
        journal (str): The name of the journal to be reflected in the updated feed title.
    """
    for i, elem in enumerate(root[0]):
        if elem.tag == 'item': # We've gone beyond the title section: stop looking
            break
        elif elem.tag.endswith('title') or elem.text == journal: # Update the title
            root[0][i].text = f'{journal} (no repeats)'

def create_new_rss_feed(root: ET.Element, shortname: str):
    """
    Generates a new RSS feed XML file with modified URLs.

    This function serializes the provided XML root element to a string, modifies specific URL patterns,
    and writes the resulting XML content to a file named after the provided shortname.

    Args:
        root (xml.etree.ElementTree.Element): The root element of the XML document to be processed 
                                              and saved.
        shortname (str): The shortname used for naming the output file (e.g., 'example' results in 
                         'example.xml').
    """
    with open(f'{shortname}.xml', 'wb') as fout:
        newstring = ET.tostring(root).replace(b'pericles.pericles-prod.literatumonline.com', b'onlinelibrary.wiley.com')
        newstring = newstring.replace(b'onlinelibrary.wiley.com/doi/abs', b'doi.org')
        newstring = newstring.replace(b'www.', b'').replace(b'?af=R', b'')
        fout.write(newstring)

def update_old_article_list(filename: Path, rss_articles: list[list[str, str]]):
    """
    Writes the list of RSS articles to a CSV file, updating the old article list.

    This function takes a list of RSS articles, each represented as a list or tuple, and writes them
    to a specified CSV file, with each article occupying a separate row in the CSV.

    Args:
        filename (Path): The path to the CSV file where the article list will be written.
        rss_articles (list[list[str, str]]): A list of RSS articles, where each article is a list of 
                                             data to be written.
    """
    with open(filename, 'wt', newline='') as fout:
        writer = csv.writer(fout, quoting=csv.QUOTE_ALL)
        for a in rss_articles:
            writer.writerow(a)

def updaterss(journal: str, shortname: str, url: str, cdate: str):
    """
    Updates the RSS feed for a specified journal by integrating new articles and managing existing 
    ones.

    This function fetches XML data from a given URL, processes the articles to remove duplicates,
    updates the feed title, and saves the updated feed and article list to files.

    Args:
        journal (str): The name of the journal for which the RSS feed is being updated.
        shortname (str): A short identifier used for generating filenames.
        url (str): The URL from which the XML data is retrieved.
        cdate (str): The current date used for date handling in the articles.
    """
    root = getxml(url)

    old_articles = read_old_articles(f'{shortname.lower()}_old.csv')
    rss_articles = update_rss_articles(root, old_articles, cdate)

    update_feed_title(root, journal)
    create_new_rss_feed(root, shortname)
    update_old_article_list(Path(f'{shortname.lower()}_old.csv'), rss_articles)

def update_journals(cdate: str):
    """
    Updates the RSS feeds for a list of journals.

    This function iterates over a predefined list of journals, calling the `updaterss` function
    for each journal to fetch, process, and save updated RSS feed information.

    Args:
        cdate (str): The current date, used for processing article data within each journal's 
                     RSS feed.
    """
    for j in journal_list:
        journal = j['journal']
        shortname = j['shortname']
        url = j['url']
        updaterss(journal, shortname, url, cdate)

''' Debugging functions '''
def get_xml_from_file(filepath: Path=Path('acie.xml')):
    """
    Retrieve XML data from the given file and parse it into an ElementTree.

    Args:
        filename (Path): The path to the XML file. Default is Path('acie.xml'). 

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

journal_list = [{'journal': 'Advanced Materials', 'shortname': 'AdvMater', 'url': 'https://onlinelibrary.wiley.com/feed/15214095/most-recent'},
                {'journal': 'Advanced Synthesis & Catalysis', 'shortname': 'AdvSynthCatal', 'url': 'https://onlinelibrary.wiley.com/feed/16154169/most-recent'},
                {'journal': 'Angewandte Chemie International Edition', 'shortname': 'acie', 'url': 'https://onlinelibrary.wiley.com/feed/15213773/most-recent'},
                {'journal': 'Chemistry — A European Journal', 'shortname': 'ChemEurJ', 'url': 'https://onlinelibrary.wiley.com/feed/15213765/most-recent'},
                {'journal': 'ChemBioChem', 'shortname': 'ChemBioChem', 'url': 'https://onlinelibrary.wiley.com/feed/14397633/most-recent'},
		        {'journal': 'European Journal of Chemistry', 'shortname': 'ejoc', 'url': 'https://onlinelibrary.wiley.com/feed/10990690/most-recent'}
                ]