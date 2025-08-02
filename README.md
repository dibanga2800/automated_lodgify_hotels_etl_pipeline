# Automated Lodgify Hotels ETL Pipeline

This repository includes a Jupyter Notebook that automates the extraction, transformation, and loading (ETL) of hotel data from Booking website for Lodgify or similar hospitality analytics use cases.

## Overview

The main notebook, [`notebook/automated_lodgify_etl_pipeline.ipynb`](notebook/automated_lodgify_etl_pipeline.ipynb), provides a complete workflow to:

- Scrape hotel listings from Booking.com using Selenium and BeautifulSoup.
- Extract hotel details: name, address, price, rating, distance, etc.
- Categorize hotels by price and rating.
- Save results to CSV for further analysis.
- Optionally, load the data into a PostgreSQL database.

## Features

- **Robust Selenium Automation**: Multiple strategies for interacting with dynamic Booking.com components (dates, search, load more).
- **Flexible Data Extraction**: Handles variations in hotel card layouts and rating/price formats.
- **Data Categorization**: Adds `price_category` and `rating_category` columns for segmentation.
- **Database Integration**: Uses SQLAlchemy to load data into a PostgreSQL table.
- **Testing Utilities**: Includes test functions to verify date selection and scraping logic.

## Setup Instructions

### Prerequisites

- Python 3.7+
- Google Chrome
- [ChromeDriver](https://chromedriver.chromium.org/downloads) (automatically managed via `webdriver_manager`)
- PostgreSQL (optional, for database loading)
- Jupyter Notebook

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/dibanga2800/automated_lodgify_hotels_etl_pipeline.git
   cd automated_lodgify_hotels_etl_pipeline
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   Major dependencies:
   - selenium
   - webdriver_manager
   - beautifulsoup4
   - pandas
   - sqlalchemy
   - python-dotenv

3. **Configure Database (Optional)**
   - Create a `.env` file in the repo root with your PostgreSQL credentials:
     ```
     DB_HOST=your_host
     DB_PORT=your_port
     DB_NAME=your_db_name
     DB_USER=your_db_user
     DB_PASSWORD=your_db_password
     ```

### Usage

1. **Run the Notebook**
   - Open `notebook/automated_lodgify_etl_pipeline.ipynb` in Jupyter.
   - Follow the cell sequence to execute the ETL pipeline.
   - Use the provided test and main functions:
     - `test_scraper(load_db=False)` — runs a test scrape with visible browser, without loading to DB.
     - `scrape_hotels(destination="London", headless=True, load_db=True)` — main pipeline.

2. **Output**
   - Scraped hotel data is saved to the `../data/` directory as CSV.
   - If configured, data is loaded to PostgreSQL table `lodgify_hotels`.

## Customization

- **Destination & Dates**: Change `destination`, `checkin_date`, and `checkout_date` args in `scrape_hotels`.
- **Headless Mode**: Set `headless=False` for browser interaction, debugging, or visual feedback.
- **Load More Results**: Adjust `max_clicks` in `click_load_more` for deeper scraping.

## Troubleshooting

- If elements are not found (e.g., dates, search button), try running in non-headless mode for debugging.
- Ensure Chrome and ChromeDriver versions are compatible.
- If database loading fails, check `.env` configuration and PostgreSQL server status.

## File Structure

```
notebook/
  automated_lodgify_etl_pipeline.ipynb   # Main ETL notebook
data/
  hotels_*.csv                           # Output CSV files
.env                                     # Database credentials (not tracked)
requirements.txt                         # Python dependencies
```

## License

This project is licensed under the MIT License.

## Author

[@dibanga2800](https://github.com/dibanga2800)

---

*Automate your hotel data extraction and analytics pipeline with this ready-to-use ETL notebook!*
