# Card Price Tracker

A simple Python script to track the prices of your Magic: The Gathering card collection using the Scryfall API.

## Setup

1.  **Install Python**: Ensure you have Python installed on your system.
2.  **Dependencies**: This script uses standard libraries, so no extra `pip install` is usually required. However, if you run into issues, check `requirements.txt` (if provided) or ensure you have a standard Python environment.

## Usage

1.  **Add your cards**: Open `my_cards.txt` and list your cards, one per line.
    *   Example: `Black Lotus`
    *   You can also include collector numbers if you want a specific printing: `Black Lotus #001` (format may vary depending on how you want to track it, but the script tries to handle basic names best).
2.  **Run the script**:
    ```bash
    python price_tracker.py
    ```
3.  **Check results**: The script will generate `card_prices.csv` with the current prices.

## Output

The `card_prices.csv` file will contain:
*   Date of the scan
*   Card Name
*   Set Name
*   Price (USD)

## API Usage

This script uses the **[Scryfall API](https://scryfall.com/docs/api)** to fetch card prices. Scryfall is a powerful and free API for Magic: The Gathering cards.

*   **Rate Limiting**: The script includes a small delay (0.1s) between requests to comply with Scryfall's rate limits and be a good citizen.
*   **Data Source**: Prices are fetched from Scryfall's real-time data.

## Using Other APIs

If you wish to use a different pricing source (e.g., TCGPlayer directly, Cardmarket, etc.), you will need to modify the `get_card_data` function in `price_tracker.py`.

1.  **Locate the function**: Find `def get_card_data(card_line):` in `price_tracker.py`.
2.  **Replace the logic**:
    *   Remove the Scryfall API calls (`urllib.request.urlopen(...)`).
    *   Implement the API call for your desired service.
    *   Ensure the function returns a dictionary with `name`, `set`, and `price` keys, or `None` if not found.
3.  **Update parsing**: You might need to adjust how the card name and number are parsed if your new API expects a different format.

## Notes

*   The script uses the Scryfall API. Please be respectful of their rate limits (the script includes a small delay between requests).
*   If a card is not found, it will be skipped and noted in the console output.

## How it was Built
This tool was developed using a "Human-in-the-Loop" workflow leveraging **Google Antigravity** and **Gemini 3 Pro**.

* **AI Role:** Accelerated the development lifecycle by handling `pandas` CSV implementation, API connectivity logic, and boilerplate generation.
* **Developer Role:** Directed system architecture, refined API search parameters (implementing "Fuzzy Search" for better user experience), and engineered the file handling logic to ensure historical price data is preserved.
