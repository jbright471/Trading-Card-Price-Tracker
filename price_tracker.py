import urllib.request
import urllib.parse
import json
import time
import urllib.error
import csv
import os
import re
from datetime import datetime

def clean_txt(file_path):
    """
    Reads a text file and removes duplicate lines, keeping only unique non-empty lines.
    
    Args:
        file_path (str): The path to the text file to clean.
    """
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    seen = set()
    unique_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and stripped not in seen:
            seen.add(stripped)
            unique_lines.append(line)
        elif not stripped:
             # Skip empty lines
             pass

    # Write back the cleaned content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(unique_lines)
    print(f"Cleaned {file_path}: {len(lines)} -> {len(unique_lines)} lines")

def clean_csv(file_path):
    """
    Reads a CSV file and removes duplicate rows.
    
    Args:
        file_path (str): The path to the CSV file to clean.
    """
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    unique_rows = []
    seen = set()
    
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header:
            unique_rows.append(header)
        
        for row in reader:
            # Convert to tuple to make it hashable for set storage
            row_tuple = tuple(row)
            if row_tuple not in seen:
                seen.add(row_tuple)
                unique_rows.append(row)

    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(unique_rows)
    print(f"Cleaned {file_path}")

def get_card_data(card_line):
    """
    Fetches card data from the Scryfall API.
    
    Args:
        card_line (str): The line from the input file containing the card name 
                         and optionally a collector number (e.g., "Card Name #123").
                         
    Returns:
        dict: A dictionary containing 'name', 'set', and 'price', or None if not found.
    """
    # Try to parse name and collector number
    match = re.search(r'^(.*?)\s+#\s*(\S+)$', card_line)
    
    queries = []
    if match:
        name_part = match.group(1).strip()
        number_part = match.group(2).strip()
        clean_name = re.sub(r'\s*\(.*?\)', '', name_part).strip()
        number_stripped = number_part.lstrip('0')
        
        # Specific queries to try with collector number
        queries.append(f'name:"{clean_name}" cn:"{number_part}"')
        queries.append(f'name:"{clean_name}" cn:"{number_stripped}"')
    else:
        # Fallback to simple name if no number found
        clean_name = card_line
    
    # URL for fuzzy search as a last resort
    encoded_name = urllib.parse.quote(clean_name)
    fuzzy_url = f"https://api.scryfall.com/cards/named?fuzzy={encoded_name}"
    
    # Try specific queries first
    for q in queries:
        encoded_query = urllib.parse.quote(q)
        url = f"https://api.scryfall.com/cards/search?q={encoded_query}"
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())
                if data.get('total_cards', 0) > 0:
                    card_data = data['data'][0]
                    prices = card_data.get('prices', {})
                    price = prices.get('usd')
                    if not price:
                        price = prices.get('usd_foil')
                    
                    return {
                        'name': card_data.get('name', clean_name),
                        'set': card_data.get('set_name', 'Unknown'),
                        'price': price if price else 'N/A'
                    }
        except Exception:
            continue

    # Fallback to fuzzy search if specific queries fail
    try:
        with urllib.request.urlopen(fuzzy_url) as response:
            data = json.loads(response.read().decode())
            prices = data.get('prices', {})
            price = prices.get('usd')
            if not price:
                price = prices.get('usd_foil')
            
            set_name = data.get('set_name', 'Unknown')
            return {
                'name': data.get('name', clean_name),
                'set': set_name,
                'price': price if price else 'N/A'
            }
    except urllib.error.HTTPError as e:
        print(f"Error fetching data for {card_line}: HTTP {e.code}")
        return None
    except urllib.error.URLError as e:
        print(f"Error fetching data for {card_line}: {e.reason}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred for {card_line}: {e}")
        return None

def main():
    """
    Main function to run the price tracker.
    """
    # Clean input file first to remove duplicates
    clean_txt('my_cards.txt')

    try:
        with open('my_cards.txt', 'r') as f:
            cards = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("Error: my_cards.txt not found. Please create it and add card names.")
        return

    csv_file = 'card_prices.csv'
    
    collected_data = []
    print(f"Fetching prices for {len(cards)} cards...")
    
    for card in cards:
        data = get_card_data(card)
        if data:
            collected_data.append(data)
            print(f"Saved: {data['name']} - ${data['price']}")
        else:
            print(f"Skipped: {card}")
        
        # Be nice to the API to avoid rate limiting
        time.sleep(0.1)
    
    # Sort data by price (highest first)
    def get_price_value(item):
        p = item.get('price', 'N/A')
        if p == 'N/A':
            return -1.0
        try:
            return float(p)
        except ValueError:
            return -1.0

    collected_data.sort(key=get_price_value, reverse=True)

    try:
        # Write results to CSV
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Date', 'Card Name', 'Set', 'Prices'])
            
            current_time = datetime.now().strftime('%Y-%m-%d')
            for data in collected_data:
                writer.writerow([current_time, data['name'], data['set'], data['price']])
        
        print(f"Done. Prices saved to {csv_file}")
        
    except PermissionError:
        print(f"Error: Could not write to {csv_file}. Is it open in another program?")

if __name__ == "__main__":
    main()
