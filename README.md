# Card Price Tracker (Ultimate Edition)

A powerful Python script to track the value of your Magic: The Gathering card collection. It fetches real-time prices from Scryfall, tracks your portfolio history, calculates profit/loss, and generates a beautiful visual report.

## Features

*   **📈 Price History**: Tracks your total collection value over time and generates a line graph.
*   **🖼️ Visual Report**: Creates an interactive HTML dashboard (`index.html`) with card images, prices, and stats.
*   **💰 Profit/Loss Calculator**: See exactly how much money you've made (or lost) on each card.
*   **🚨 Discord Alerts**: Get notified automatically when your collection value spikes.
*   **📊 Excel Export**: Saves a detailed spreadsheet (`card_prices.xlsx`) with all your data.

## Setup

1.  **Install Python**: Ensure you have Python installed.
2.  **Install Dependencies**:
    ```bash
    pip install matplotlib openpyxl
    ```

## Usage

### 1. Add Your Cards
Open `my_cards.txt` and list your cards. You can add them in two ways:

*   **Simple**: Just the name (and optional quantity).
    ```text
    Black Lotus
    2x Sol Ring
    ```
*   **With Bought Price** (for Profit/Loss tracking): Add `| Price` after the name.
    ```text
    Black Lotus | 5000
    Mox Pearl | 800.50
    ```

### 2. Configure Alerts (Optional)
To get Discord notifications:
1.  Open `price_tracker.py` in a text editor.
2.  Find the line: `DISCORD_WEBHOOK_URL = ""`
3.  Paste your Discord Webhook URL inside the quotes.
4.  (Optional) Adjust `ALERT_THRESHOLD_PERCENT` to change when you get notified (default is 10%).

### 3. Run the Tracker
Double-click `price_tracker.py` or run it from the terminal:
```bash
python price_tracker.py
```

## Output

*   **index.html**: Open this in your browser to see your **Visual Report**.
*   **card_prices.xlsx**: The detailed spreadsheet of your collection.
*   **price_history.csv**: The raw data log of your collection's value over time.
*   **history_graph.png**: The image file of your value graph.

## API Usage

This script uses the **[Scryfall API](https://scryfall.com/docs/api)**.
*   **Rate Limiting**: Includes a built-in delay (0.1s) to respect Scryfall's guidelines.
*   **Data**: Prices are fetched in real-time (USD).

## How it was Built
This tool was developed using a "Human-in-the-Loop" workflow leveraging **Google Antigravity** and **Gemini 3 Pro**.

* **AI Role:** Accelerated development by implementing data visualization (`matplotlib`), HTML report generation, and Discord webhook integration.
* **Developer Role:** Directed feature roadmap, designed the Profit/Loss logic, and ensured the tool remains user-friendly and robust.
