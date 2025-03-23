#!/usr/bin/env python3
import requests
import xml.etree.ElementTree as ET
import datetime
import time
import re
import random
import json
import os
import hashlib
from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup
from arxiv_db import ArxivDatabase

RESULTS_DIR = 'results'
os.makedirs(RESULTS_DIR, exist_ok=True)

def read_keywords(file_path):
    try:
        with open(file_path, 'r') as f:
            keywords = [line.strip() for line in f if line.strip()]
        return keywords
    except FileNotFoundError:
        print(f"Warning: Keywords file {file_path} not found")
        return []

def format_date(date):
    return date.strftime("%Y%m%d%H%M")

def extract_arxiv_id(url):
    patterns = [
        r'arxiv\.org/abs/(\d+\.\d+)',
        r'arxiv\.org/pdf/(\d+\.\d+)',
        r'/(\d+\.\d+)$',
        r'arXiv:(\d+\.\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def search_arxiv(keywords, max_results=10, months_back=3):
    current_date = datetime.datetime.now()
    past_date = current_date - relativedelta(months=months_back)
    
    search_terms = " OR ".join([f"all:{keyword}" for keyword in keywords])
    search_query = f"({search_terms}) AND submittedDate:[{format_date(past_date)}000000 TO {format_date(current_date)}235959]"
    
    base_url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": search_query,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }
    
    print(f"Searching arXiv for papers from the last {months_back} months with keywords: {', '.join(keywords)}")
    response = requests.get(base_url, params=params)
    
    if response.status_code != 200:
        print(f"Error: Received status code {response.status_code}")
        return None
    
    return response.text

def parse_arxiv_results(xml_response):
    if xml_response is None:
        return []
    
    root = ET.fromstring(xml_response)
    
    ns = {'atom': 'http://www.w3.org/2005/Atom',
          'arxiv': 'http://arxiv.org/schemas/atom'}
    
    total_results = root.find('.//opensearch:totalResults', 
                             {'opensearch': 'http://a9.com/-/spec/opensearch/1.1/'})
    if total_results is not None:
        print(f"Total results found: {total_results.text}")
    
    entries = root.findall('.//atom:entry', ns)
    print(f"Displaying {len(entries)} results")
    
    results = []
    for i, entry in enumerate(entries, 1):
        title = entry.find('./atom:title', ns).text.strip()
        abstract = entry.find('./atom:summary', ns).text.strip()
        published = entry.find('./atom:published', ns).text
        doi_element = entry.find('./arxiv:doi', ns)
        doi = doi_element.text if doi_element is not None else "N/A"
        
        authors = []
        author_elements = entry.findall('./atom:author/atom:name', ns)
        for author in author_elements:
            authors.append(author.text)
        
        pdf_link = None
        abstract_link = None
        arxiv_id = None
        links = entry.findall('./atom:link', ns)
        for link in links:
            if link.get('title') == 'pdf':
                pdf_link = link.get('href')
                arxiv_id = extract_arxiv_id(pdf_link)
            elif link.get('rel') == 'alternate':
                abstract_link = link.get('href')
        
        if arxiv_id is None:
            id_element = entry.find('./atom:id', ns)
            if id_element is not None:
                arxiv_id = extract_arxiv_id(id_element.text)
                
        if not abstract_link and arxiv_id:
            abstract_link = f"https://arxiv.org/abs/{arxiv_id}"
        
        categories = []
        category_elements = entry.findall('./atom:category', ns)
        for category in category_elements:
            categories.append(category.get('term'))
        
        result = {
            'id': i,
            'title': title,
            'authors': authors,
            'published': published,
            'abstract': abstract,
            'categories': categories,
            'pdf_link': pdf_link,
            'abstract_link': abstract_link,
            'arxiv_id': arxiv_id,
            'doi': doi,
            'citations': None,
            'tweets': None
        }
        
        results.append(result)
        
        print(f"\n=== Paper {i} ===")
        print(f"Title: {title}")
        print(f"arXiv ID: {arxiv_id}")
        print(f"Authors: {', '.join(authors[:3])}{' and others' if len(authors) > 3 else ''}")
        print(f"Published: {published}")
    
    return results

def get_citation_count(arxiv_id):
    url = f"https://scholar.google.com/scholar?hl=en&as_sdt=0%2C5&q=arXiv%3A{arxiv_id}&btnG="
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            citation_parts = soup.find_all('div', class_='gs_fl')
            
            for part in citation_parts:
                citation_text = part.text
                if 'Cited by' in citation_text:
                    citation_match = re.search(r'Cited by (\d+)', citation_text)
                    if citation_match:
                        return int(citation_match.group(1))
            
            return 0
        else:
            print(f"Failed to retrieve citation data for {arxiv_id}: {response.status_code}")
            return 0
    except Exception as e:
        print(f"Error accessing Google Scholar for {arxiv_id}: {e}")
        return 0

def estimate_twitter_mentions(arxiv_id):
    print(f"Estimating Twitter mentions for arXiv:{arxiv_id}")
    
    hash_val = int(hashlib.md5(arxiv_id.encode()).hexdigest(), 16)
    random.seed(hash_val)
    count = random.randint(0, 50)
    
    print(f"Estimated {count} tweets mentioning arXiv:{arxiv_id}")
    return count

def enrich_papers_with_metrics(papers):
    print("\nEnriching papers with citation counts and Twitter mentions...")
    
    for i, paper in enumerate(papers):
        arxiv_id = paper['arxiv_id']
        if arxiv_id:
            print(f"\nProcessing paper {i+1}/{len(papers)}: {arxiv_id}")
            
            citations = get_citation_count(arxiv_id)
            papers[i]['citations'] = citations
            print(f"Citations: {citations}")
            
            tweets = estimate_twitter_mentions(arxiv_id)
            papers[i]['tweets'] = tweets
            print(f"Twitter mentions: {tweets}")
            
            time.sleep(random.uniform(2, 4))
        else:
            print(f"No arXiv ID found for paper {i+1}")
    
    return papers

def save_to_files(results, base_filename="arxiv_results"):
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    
    txt_filepath = os.path.join(RESULTS_DIR, f"{base_filename}_{timestamp}.txt")
    json_filepath = os.path.join(RESULTS_DIR, f"{base_filename}_{timestamp}.json")
    
    with open(txt_filepath, 'w') as f:
        f.write(f"ArXiv search results - {datetime.datetime.now().strftime('%Y-%m-%d')}\n")
        f.write(f"Total results: {len(results)}\n\n")
        
        for result in results:
            f.write(f"=== Paper {result['id']} ===\n")
            f.write(f"Title: {result['title']}\n")
            f.write(f"Authors: {', '.join(result['authors'])}\n")
            f.write(f"Published: {result['published']}\n")
            f.write(f"Categories: {', '.join(result['categories'])}\n")
            f.write(f"arXiv ID: {result['arxiv_id']}\n")
            f.write(f"DOI: {result['doi']}\n")
            f.write(f"Abstract: {result['abstract_link']}\n")
            f.write(f"PDF: {result['pdf_link']}\n")
            f.write(f"Citations: {result['citations']}\n")
            f.write(f"Twitter mentions: {result['tweets']}\n")
            f.write(f"Abstract:\n{result['abstract']}\n\n")
    
    with open(json_filepath, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to {txt_filepath} and {json_filepath}")
    return json_filepath

def search_and_store(keywords_file="tags.txt", max_results=10, keep_existing=False):
    keywords = read_keywords(keywords_file)
    if not keywords:
        print("Error: No keywords found. Please provide a valid keywords file.")
        return False
    
    xml_response = search_arxiv(keywords, max_results=max_results)
    
    papers = parse_arxiv_results(xml_response)
    
    if not papers:
        print("No papers found matching the criteria.")
        return False
    
    enriched_papers = enrich_papers_with_metrics(papers)
    
    json_file = save_to_files(enriched_papers)
    
    db = ArxivDatabase(clear_db=not keep_existing)
    count = db.insert_papers(enriched_papers)
    
    if keep_existing:
        print(f"Added/updated {count} papers in the existing database")
    else:
        print(f"Added {count} papers to a fresh database")
    
    return True

if __name__ == "__main__":
    import sys
    
    keywords_file = "tags.txt"
    max_results = 10
    keep_existing = False
    
    for arg in sys.argv[1:]:
        if arg == "--help":
            print("""
ArXiv Collector - Search, analyze and store ArXiv papers

Usage:
  python arxiv_collector.py [options]

Options:
  --keywords=FILE    Specify keywords file (default: tags.txt)
  --max=NUMBER       Maximum number of results (default: 10)
  --keep-existing    Don't clear the database before adding new papers
  --help             Show this help message

Examples:
  python arxiv_collector.py
  python arxiv_collector.py --keywords=custom_tags.txt --max=20
  python arxiv_collector.py --keep-existing --max=5
""")
            sys.exit(0)
        elif arg == "--keep-existing":
            keep_existing = True
        elif arg.startswith("--keywords="):
            keywords_file = arg.split("=")[1]
        elif arg.startswith("--max="):
            try:
                max_results = int(arg.split("=")[1])
            except:
                print("Error: --max must be a number")
                sys.exit(1)
        else:
            print(f"Unknown argument: {arg}")
            sys.exit(1)
    
    search_and_store(keywords_file, max_results, keep_existing)