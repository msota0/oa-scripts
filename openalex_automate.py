import requests
import json
import os
import re
import pandas as pd

def fetch_institution_id(ror_id):
    base_url = f"https://api.crossref.org/organizations?filter=ror:{ror_id}"
    response = requests.get(base_url)

    if response.status_code == 200:
        institution_data = response.json()
        return institution_data['message']['items'][0]['id']  # Assuming you want the first item
    else:
        print(f"Failed to fetch institution: {response.status_code}")
        return None

def fetch_all_works(institution_id):
    all_works = []
    page = 0
    per_page = 100

    while True:
        print(f"Fetching page: {page + 1}")
        works_url = f"https://api.crossref.org/works?filter=member:{institution_id}&rows={per_page}&offset={page * per_page}"
        response = requests.get(works_url)

        if response.status_code == 200:
            data = response.json()
            current_results = data['message']['items']

            # Filter works by publication_year
            for work in current_results:
                if 'published-print' in work and 'date-parts' in work['published-print']:
                    publication_year = work['published-print']['date-parts'][0][0]
                    if 2018 <= publication_year <= 2024:
                        all_works.append(work)

            # Check if we've reached the last page
            if len(current_results) < per_page:
                break
            
            page += 1
        else:
            print(f"Failed to fetch works for institution {institution_id}: {response.status_code}")
            break

    return all_works

ror_id = "https://ror.org/02teq1165"  # Example ROR ID
institution_id = fetch_institution_id(ror_id)

if institution_id:
    json_file_name = 'crossref_data.json'

    # Check if the JSON file exists
    if os.path.exists(json_file_name):
        # Load data from the JSON file
        with open(json_file_name, 'r') as json_file:
            all_works = json.load(json_file)
        print("Loaded data from JSON file.")
    else:
        # Fetch works from the API
        all_works = fetch_all_works(institution_id)
        print(f"Total number of works found (2018-2024): {len(all_works)}")

        # Save the fetched works to a JSON file
        with open(json_file_name, 'w') as json_file:
            json.dump(all_works, json_file, indent=2)
        print(f"Data saved to {json_file_name}.")

    # Prepare a list to hold DataFrame rows
    rows = []
    doi_pattern = r'10\.\d{4,9}/[-._;()/:A-Z0-9]+'

    # Iterate through each work in the loaded data
    for work in all_works:
        doi = work.get("DOI")  # Get the DOI safely
        doi_temp = None  # Initialize doi_temp to None

        # Only search for the DOI if it's not None
        if doi:
            match = re.search(doi_pattern, doi, re.IGNORECASE)
            if match:
                doi_temp = match.group(0)

        row = {
            "id": work.get("id"),
            "doi": doi_temp,  # Use the matched DOI or None
            "title": work.get("title", ['No Title'])[0],
            "publication_year": work.get("published-print", {}).get("date-parts", [[None]])[0][0],
            "language": work.get("language"),
            "is_open_access": work.get("is_open_access", {}).get("is_oa", False),
        }

        # Collect authors
        authors = work.get("author", [])

        # Limit to 20 authors
        for i, author in enumerate(authors[:20]):
            author_name = author.get("given", "") + " " + author.get("family", "")
            row[f"author_{i + 1}_name"] = author_name

            # If there are affiliations, add the first one
            affiliations = author.get("affiliation", [])
            if affiliations:
                row[f"author_{i + 1}_affiliation"] = affiliations[0].get("name")

        # Append the row to the list
        rows.append(row)

    # Create a DataFrame from the list of rows
    df = pd.DataFrame(rows)

    # Filter out rows with "Jackson" in any author's affiliation
    df_filtered = df[~df.apply(lambda x: any("jackson" in str(x[f"author_{i + 1}_affiliation"]).lower() for i in range(20) if f"author_{i + 1}_affiliation" in x), axis=1)]

    # Save the filtered DataFrame to a CSV file
    df_filtered.to_csv('crossref_data.csv', index=False)

    # Display the first few rows of the filtered DataFrame
    print(df_filtered.head())
