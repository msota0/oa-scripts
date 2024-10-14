import json
import pandas as pd
import glob

# Function to parse RIS data from a file
def parse_ris_file(file_path):
    entries = []
    entry = {}
    
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line.startswith('ER  -'):
                if entry:  # If we have an entry, save it
                    entries.append(entry)
                    entry = {}
            elif line.startswith('TY  -'):
                entry['type'] = line[5:].strip()
            elif line.startswith('AU  -'):
                entry.setdefault('authors', []).append(line[5:].strip())
            elif line.startswith('TI  -'):
                entry['title'] = line[5:].strip()
            elif line.startswith('T2  -'):
                entry['journal'] = line[5:].strip()
            elif line.startswith('PY  -'):
                entry['year'] = line[5:].strip()
            elif line.startswith('VL  -'):
                entry['volume'] = line[5:].strip()
            elif line.startswith('IS  -'):
                entry['issue'] = line[5:].strip()
            elif line.startswith('SN  -'):
                entry['issn'] = line[5:].strip()
            elif line.startswith('AB  -'):
                entry['abstract'] = line[5:].strip()
            elif line.startswith('KW  -'):
                entry.setdefault('keywords', []).append(line[5:].strip())
            elif line.startswith('DO  -'):
                entry['doi'] = line[5:].strip()

    return entries

# Paths to the RIS files
ris_file_paths = glob.glob('./ris/*.ris')  

# Parse the RIS data from both files and combine
combined_entries = []
for file_path in ris_file_paths:
    combined_entries.extend(parse_ris_file(file_path))

# Save to JSON
with open('articles_combined.json', 'w', encoding='utf-8') as json_file:
    json.dump(combined_entries, json_file, indent=4)

# Convert to DataFrame and save to CSV
df = pd.DataFrame(combined_entries)
df.to_csv('articles_combined.csv', index=False, encoding='utf-8')

print("Data extraction completed! Combined JSON and CSV files created.")
