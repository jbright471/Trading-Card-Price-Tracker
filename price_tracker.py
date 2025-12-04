import urllib.request
import urllib.parse
import json
import time
import urllib.error
import csv
import os
import re
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, Border, Side
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# --- Configuration ---
DISCORD_WEBHOOK_URL = "" # Add your Discord Webhook URL here to enable alerts
ALERT_THRESHOLD_PERCENT = 10.0 # Alert if total value increases by this %

def clean_txt(file_path):
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
             pass

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(unique_lines)
    print(f"Cleaned {file_path}: {len(lines)} -> {len(unique_lines)} lines")

def get_card_data(card_line):
    # Try to parse name and collector number
    match = re.search(r'^(.*?)\s+#\s*(\S+)$', card_line)
    
    queries = []
    if match:
        name_part = match.group(1).strip()
        number_part = match.group(2).strip()
        clean_name = re.sub(r'\s*\(.*?\)', '', name_part).strip()
        number_stripped = number_part.lstrip('0')
        
        # Specific queries to try
        queries.append(f'name:"{clean_name}" cn:"{number_part}"')
        queries.append(f'name:"{clean_name}" cn:"{number_stripped}"')
    else:
        # Fallback to simple name if no number found
        clean_name = card_line
    
    # Add fuzzy search as last resort
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
                    return parse_scryfall_data(card_data, clean_name)
        except Exception:
            continue

    # Fallback to fuzzy search
    try:
        with urllib.request.urlopen(fuzzy_url) as response:
            data = json.loads(response.read().decode())
            return parse_scryfall_data(data, clean_name)
    except Exception as e:
        print(f"Error fetching {card_line}: {e}")
        return None

def parse_scryfall_data(data, default_name):
    prices = data.get('prices', {})
    price = prices.get('usd')
    if not price:
        price = prices.get('usd_foil')
    
    name = data.get('name', default_name)
    if 'flavor_name' in data:
        name = data['flavor_name']

    # Get Image URL
    image_url = ""
    if 'image_uris' in data:
        image_url = data['image_uris'].get('normal', '')
    elif 'card_faces' in data and 'image_uris' in data['card_faces'][0]:
         image_url = data['card_faces'][0]['image_uris'].get('normal', '')

    return {
        'name': name,
        'set': data.get('set_name', 'Unknown'),
        'price': price if price else 'N/A',
        'image': image_url,
        'scryfall_uri': data.get('scryfall_uri', '#')
    }

def update_history_and_graph(total_value):
    history_file = 'price_history.csv'
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Read existing
    history = []
    previous_value = 0.0
    
    if os.path.exists(history_file):
        with open(history_file, 'r', newline='') as f:
            reader = csv.reader(f)
            history = list(reader)
            # Find previous entry (not today)
            for row in reversed(history):
                if row[0] != today:
                    try:
                        previous_value = float(row[1])
                        break
                    except: pass
    
    # Update or Append today's value
    updated = False
    for row in history:
        if row and row[0] == today:
            row[1] = f"{total_value:.2f}"
            updated = True
            break
    
    if not updated:
        history.append([today, f"{total_value:.2f}"])
        
    # Sort by date
    history.sort(key=lambda x: x[0])
    
    # Write back
    with open(history_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(history)
        
    # Generate Graph
    if len(history) > 0:
        dates = [datetime.strptime(row[0], '%Y-%m-%d') for row in history]
        values = [float(row[1]) for row in history]
        
        plt.figure(figsize=(10, 5))
        plt.plot(dates, values, marker='o', linestyle='-', color='#2c3e50', linewidth=2)
        plt.title('Collection Value History', fontsize=14)
        plt.xlabel('Date')
        plt.ylabel('Value (USD)')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.gcf().autofmt_xdate()
        
        # Save
        plt.savefig('history_graph.png', bbox_inches='tight')
        plt.close()

    # Check for Alerts
    if previous_value > 0 and DISCORD_WEBHOOK_URL:
        percent_change = ((total_value - previous_value) / previous_value) * 100
        if percent_change >= ALERT_THRESHOLD_PERCENT:
            send_discord_alert(total_value, percent_change)

def send_discord_alert(current_value, percent_change):
    try:
        data = {
            "content": f"🚀 **Collection Value Alert!**\nYour collection is now worth **${current_value:.2f}**.\nThat's a **{percent_change:.1f}%** increase since the last check!"
        }
        req = urllib.request.Request(
            DISCORD_WEBHOOK_URL, 
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        urllib.request.urlopen(req)
        print("Discord alert sent!")
    except Exception as e:
        print(f"Failed to send Discord alert: {e}")

def generate_html_report(collected_data, total_value, total_profit_loss):
    today = datetime.now().strftime('%Y-%m-%d')
    
    pl_color = "#27ae60" if total_profit_loss >= 0 else "#c0392b"
    pl_sign = "+" if total_profit_loss >= 0 else ""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Card Collection Tracker</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f9; color: #333; margin: 0; padding: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
            .header h1 {{ margin: 0; font-size: 24px; }}
            .stats {{ text-align: right; }}
            .total-value {{ font-size: 32px; font-weight: bold; color: #2c3e50; }}
            .profit-loss {{ font-size: 18px; font-weight: bold; color: {pl_color}; }}
            .graph-container {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 20px; text-align: center; }}
            .graph-container img {{ max-width: 100%; height: auto; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 20px; }}
            .card {{ background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.1); transition: transform 0.2s; }}
            .card:hover {{ transform: translateY(-5px); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }}
            .card-img {{ width: 100%; height: 280px; object-fit: cover; }}
            .card-info {{ padding: 15px; }}
            .card-name {{ font-weight: bold; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
            .card-set {{ color: #7f8c8d; font-size: 12px; margin-bottom: 10px; }}
            .card-price {{ font-size: 18px; color: #2980b9; font-weight: bold; }}
            .card-pl {{ font-size: 14px; font-weight: bold; margin-top: 5px; }}
            .pl-green {{ color: #27ae60; }}
            .pl-red {{ color: #c0392b; }}
            .card-qty {{ font-size: 12px; color: #95a5a6; float: right; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div>
                    <h1>My Collection</h1>
                    <p>Last Updated: {today}</p>
                </div>
                <div class="stats">
                    <div class="total-value">${total_value:.2f}</div>
                    <div class="profit-loss">P/L: {pl_sign}${total_profit_loss:.2f}</div>
                </div>
            </div>
            
            <div class="graph-container">
                <h2>Value History</h2>
                <img src="history_graph.png" alt="Value History Graph">
            </div>
            
            <div class="grid">
    """
    
    for item in collected_data:
        data = item['data']
        price_str = item['price_str']
        qty = item['quantity']
        profit_loss = item['profit_loss']
        
        pl_html = ""
        if profit_loss is not None:
            color_class = "pl-green" if profit_loss >= 0 else "pl-red"
            sign = "+" if profit_loss >= 0 else ""
            pl_html = f'<div class="card-pl {color_class}">{sign}${profit_loss:.2f}</div>'

        # Use placeholder if no image
        img_src = data['image'] if data['image'] else "https://cards.scryfall.io/large/front/4/4/44012bb8-17b7-4b50-a796-662ef09bfc29.jpg"
        
        html += f"""
                <div class="card" onclick="window.open('{data['scryfall_uri']}', '_blank')" style="cursor: pointer;">
                    <img src="{img_src}" class="card-img" alt="{data['name']}">
                    <div class="card-info">
                        <div class="card-name" title="{data['name']}">{data['name']}</div>
                        <div class="card-set">{data['set']}</div>
                        <div class="card-price">
                            ${price_str}
                            <span class="card-qty">x{qty}</span>
                        </div>
                        {pl_html}
                    </div>
                </div>
        """
        
    html += """
            </div>
        </div>
    </body>
    </html>
    """
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Report generated: index.html")

def main():
    clean_txt('my_cards.txt')

    try:
        with open('my_cards.txt', 'r') as f:
            cards = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("Error: my_cards.txt not found.")
        return

    collected_data = []
    print(f"Fetching prices for {len(cards)} cards...")
    
    total_collection_value = 0.0
    total_profit_loss = 0.0
    
    for card in cards:
        quantity = 1
        bought_price = None
        
        # Parse "Card Name | 50.00" (Bought Price)
        if '|' in card:
            parts = card.split('|')
            card = parts[0].strip()
            try:
                bought_price = float(parts[1].strip())
            except ValueError:
                pass
        
        clean_card_line = card
        qty_match = re.search(r'^(\d+)x\s+(.*)', card)
        if qty_match:
            quantity = int(qty_match.group(1))
            clean_card_line = qty_match.group(2).strip()

        data = get_card_data(clean_card_line)
        if data:
            unit_price_str = data['price']
            
            total_price_str = unit_price_str
            profit_loss = None
            
            if unit_price_str != 'N/A':
                try:
                    unit_price = float(unit_price_str)
                    total_price = unit_price * quantity
                    total_price_str = f"{total_price:.2f}"
                    total_collection_value += total_price
                    
                    if bought_price is not None:
                        # Total bought price (assuming bought_price is per unit? Or total? Usually per unit)
                        # Let's assume user enters UNIT bought price
                        total_bought = bought_price * quantity
                        profit_loss = total_price - total_bought
                        total_profit_loss += profit_loss
                        
                except ValueError:
                    pass

            collected_data.append({
                'data': data,
                'quantity': quantity,
                'price_str': total_price_str,
                'profit_loss': profit_loss,
                'sort_val': float(total_price_str) if total_price_str != 'N/A' else -1.0
            })
            
            print(f"Fetched: {data['name']} - ${total_price_str}")
        else:
            print(f"Skipped: {card}")
        time.sleep(0.1)
    
    # Sort by price
    collected_data.sort(key=lambda x: x['sort_val'], reverse=True)

    # 1. Update Excel (Legacy support)
    try:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Card Prices"
        ws.append(['Date', 'Card Name', 'Set', 'Prices', 'Notes'])
        
        today = datetime.now().strftime('%Y-%m-%d')
        for item in collected_data:
            d = item['data']
            note = f"x{item['quantity']}" if item['quantity'] > 1 else ""
            if item['profit_loss'] is not None:
                sign = "+" if item['profit_loss'] >= 0 else ""
                note += f" (P/L: {sign}${item['profit_loss']:.2f})"
                
            ws.append([today, d['name'], d['set'], item['price_str'], note])
            
        ws.append(['Total', '', '', f"{total_collection_value:.2f}", f"Total P/L: ${total_profit_loss:.2f}"])
        wb.save('card_prices.xlsx')
        print("Saved to card_prices.xlsx")
    except Exception as e:
        print(f"Error saving Excel: {e}")

    # 2. Update History & Graph
    update_history_and_graph(total_collection_value)
    
    # 3. Generate HTML Report
    generate_html_report(collected_data, total_collection_value, total_profit_loss)

if __name__ == "__main__":
    main()
