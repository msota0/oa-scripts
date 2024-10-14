import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import time
import csv

# Define the function to fetch articles in batches
def fetch_articles_batch(uids):
    fetch_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={uids}&retmode=xml"
    response = requests.get(fetch_url)
    if response.status_code == 200:
        print('hit')
        return response.content
    else:
        print(f"Failed to fetch articles with status code: {response.status_code}")
        return None

# Define a function to handle rate limiting
def rate_limit_wait():
    time.sleep(1)  # Adjust this sleep time based on API rate limits

# Define the search term and date range
search_term = "University of Mississippi[Affiliation]"
current_year = datetime.now().year
start_year = current_year - 5
end_year = current_year

# Initialize counters and results
all_uids = []
max_results = 2000  # Adjust as needed (PubMed often supports up to 2000 per request)

# Fetch results in batches
start = 0
while True:
    search_url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"
        f"db=pubmed&term={search_term}&retmode=xml&mindate={start_year}/01/01&maxdate={end_year}/12/31&retstart={start}&retmax={max_results}"
    )
    
    search_response = requests.get(search_url)
    if search_response.status_code != 200:
        print(f"Failed to search articles with status code: {search_response.status_code}")
        break
    
    search_result = ET.fromstring(search_response.content)
    ids = search_result.findall(".//Id")
    
    if not ids:
        break
    
    uids = [id_elem.text for id_elem in ids]
    all_uids.extend(uids)
    
    # Break if fewer results than requested (last page)
    if len(ids) < max_results:
        break
    
    # Update start for next batch
    start += max_results
    # rate_limit_wait()

# Initialize list for results
# Initialize list for results
results = []

# Define the maximum number of authors to track
max_authors = 20

# Process UIDs in smaller batches
batch_size = 200  # Adjust based on maximum allowed batch size
for i in range(0, len(all_uids), batch_size):
    print('i', i)
    uid_batch = all_uids[i:i + batch_size]
    uid_list = ",".join(uid_batch)
    article_data = fetch_articles_batch(uid_list)
    
    if article_data:
        root = ET.fromstring(article_data)

        # Parse article details
        for article in root.findall(".//PubmedArticle"):
            article_info = {
                "id": article.findtext(".//ArticleId[@IdType='pubmed']"), 
                "pmc": article.findtext(".//ArticleId[@IdType='pmc']"),
                "doi": article.findtext(".//ArticleId[@IdType='doi']"),
                "title": article.findtext(".//ArticleTitle"),
                "publication_year": article.findtext(".//PubDate/Year"),
                "publication_date": article.findtext(".//PubDate"),
                "language": article.findtext(".//Language"),
                "is_open_access": "Yes" if article.find(".//PubmedData/ArticleId[@IdType='pmc']") is not None else "No",
                "source_display_name": article.findtext(".//Journal/Title")
            }

            # Collect authors (up to max_authors)
            for j in range(max_authors):
                author = article.find(f".//Author[{j + 1}]")
                if author is not None:
                    full_name = f"{author.findtext('ForeName', '')} {author.findtext('LastName', '')}".strip()
                    article_info[f"author{j + 1}_name"] = full_name
                else:
                    article_info[f"author{j + 1}_name"] = ""  # Fill with empty string if no author

            results.append(article_info)

        # Implement rate limiting
        # rate_limit_wait()

# Write results to CSV
with open('pubmed_articles.csv', 'w', newline='', encoding='utf-8') as csv_file:
    # Use a set to gather all unique fieldnames across all results
    fieldnames = set()
    for result in results:
        fieldnames.update(result.keys())
    
    fieldnames = sorted(fieldnames)  # Sort fieldnames for consistency
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

# Print the total count of articles fetched
print(f"Total Articles from University of Mississippi: {len(results)}")
