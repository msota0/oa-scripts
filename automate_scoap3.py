import requests
import pandas as pd
import json
import os

def fetch_articles_batch(fetch_url):
    response = requests.get(fetch_url)
    if response.status_code == 200:
        return response.content
    else:
        print(f"Failed to fetch data with status code: {response.status_code}")
        return None

def call_scoap3_api_call():
    columns = [
        'id', 'doi', 'title', 'publication_year', 'publication_date', 
        'language', 'is_open_access', 'source_display_name', 
        'author1_name', 'author2_name', 'author3_name', 
        'author4_name', 'author5_name', 'author6_name', 
        'author7_name', 'author8_name', 'author9_name', 
        'author10_name', 'author11_name', 'author12_name', 
        'author13_name', 'author14_name', 'author15_name', 
        'author16_name', 'author17_name', 'author18_name', 
        'author19_name', 'author20_name'
    ]
    
    total_rows = []
    article_json_data = []
    
    # Fetch data from multiple pages
    for i in range(1, 54):  # Adjust the range as needed
        print(f"Fetching page {i}")
        fetch_url = f'http://repo.scoap3.org/api/records/?sort=-date&q=university+of+mississippi&page={i}&size=10'
        article_data = fetch_articles_batch(fetch_url)
        
        if article_data is None:
            break  # Exit if there's an error
        
        article_data_json = json.loads(article_data)
        data_bucket_hits = article_data_json["hits"]["hits"]
        
        for data in data_bucket_hits:
            # Extracting the desired fields
            metadata = data.get('metadata', {})
            article_json_data.append(metadata)
            article_info = {
                'id': data.get('id', ''),
                'doi': metadata.get('dois', '')[0].get('value', ''),
                'title': metadata.get('titles', '')[0].get('title', ''),
                'publication_year': metadata.get('published_year', ''),
                'publication_date': metadata.get('publication_date', ''),
                'language': metadata.get('language', ''),
                'is_open_access': metadata.get('open_access', ''),
                'source_display_name': metadata.get('source', ''),
            }
            
            # Extract authors
            authors = [author.get('full_name', '') for author in metadata.get('authors', [])]
            for idx in range(20):  # Fill up to 20 author fields
                article_info[f'author{idx + 1}_name'] = authors[idx] if idx < len(authors) else ''
            
            total_rows.append(article_info)
        
        print(f"Total rows collected so far: {len(total_rows)}")
    
    # Save the full JSON response for all pages
    if article_json_data:
        with open('scoap3_response.json', 'w') as json_file:
            json.dump(total_rows, json_file, indent=4)
        
        # Save the article data JSON
        with open('article_data_json.json', 'w') as json_file:
            json.dump(article_json_data, json_file, indent=4)

    # Create DataFrame
    scoap3_df = pd.DataFrame(total_rows, columns=columns)
    
    # Save to CSV
    scoap3_df.to_csv('scoap3_articles.csv', index=False)

    # Print DataFrame for verification (optional)
    print(scoap3_df.head())
    
    return not scoap3_df.empty

# Call the function to execute
call_scoap3_api_call()
