#Import necessary libraries

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime, timedelta
import re
from pathlib import Path




# Function to create and configure the Chrome driver
def create_driver(headless=True):
    options = Options()
    options.headless = headless
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(10)
    
    return driver

# Function to navigate to Booking.com and handle cookies
def navigate_to_booking(driver):
    driver.get("https://www.booking.com/")
    time.sleep(3)
    
    # Handle cookies if present
    try:
        cookie_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#onetrust-accept-btn-handler"))
        )
        cookie_button.click()
        time.sleep(2)
    except:
        pass  

# Function to set the destination in the search box
def set_destination(driver, destination="London"):
    try:
        destination_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='ss']"))
        )
        destination_input.clear()
        destination_input.send_keys(destination)
        time.sleep(2)
        
        # Try to click first suggestion
        try:
            suggestion = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "li[data-i='0']"))
            )
            suggestion.click()
            time.sleep(2)
        except:
            pass  # Use typed destination
    except Exception as e:
        print(f"Could not set destination: {e}")


# Function to select check-in and check-out dates with improved logic
def select_dates(driver, checkin_date, checkout_date):
    """Select check-in and check-out dates with improved logic"""
    try:
        print(f"Attempting to select dates: {checkin_date} to {checkout_date}")
        
        # Multiple selectors for date field
        date_selectors = [
            "button[data-testid='date-display-field-start']",
            "[data-testid='searchbox-dates-container']",
            "button[data-testid='searchbox-dates-container']", 
            ".xp__dates-inner",
            "[data-testid='date-display-field']",
            "div[data-testid='searchbox-dates-container']"
        ]
        
        date_field = None
        for selector in date_selectors:
            try:
                date_field = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                print(f"Found date field with selector: {selector}")
                break
            except:
                continue
        
        if not date_field:
            print("Could not find date field")
            return False
            
        date_field.click()
        time.sleep(3)
        print("Date picker opened")
        
        # Try multiple strategies for date selection
        success = False
        
        # Strategy 1: Direct date selection
        try:
            checkin_element = driver.find_element(By.CSS_SELECTOR, f'td[data-date="{checkin_date}"]')
            driver.execute_script("arguments[0].click();", checkin_element)
            print(f"Check-in date selected: {checkin_date}")
            time.sleep(2)
            
            checkout_element = driver.find_element(By.CSS_SELECTOR, f'td[data-date="{checkout_date}"]')
            driver.execute_script("arguments[0].click();", checkout_element)
            print(f"Check-out date selected: {checkout_date}")
            time.sleep(2)
            success = True
        except Exception as e:
            print(f"Direct date selection failed: {e}")
        
        # Strategy 2: Alternative date selectors
        if not success:
            try:
                date_selectors_alt = [
                    f'[data-date="{checkin_date}"]',
                    f'span[data-date="{checkin_date}"]',
                    f'button[data-date="{checkin_date}"]'
                ]
                
                for selector in date_selectors_alt:
                    try:
                        checkin_element = driver.find_element(By.CSS_SELECTOR, selector)
                        driver.execute_script("arguments[0].click();", checkin_element)
                        print(f"Check-in selected with alt selector: {selector}")
                        time.sleep(2)
                        break
                    except:
                        continue
                
                for selector in date_selectors_alt:
                    alt_selector = selector.replace(checkin_date, checkout_date)
                    try:
                        checkout_element = driver.find_element(By.CSS_SELECTOR, alt_selector)
                        driver.execute_script("arguments[0].click();", checkout_element)
                        print(f"Check-out selected with alt selector: {alt_selector}")
                        time.sleep(2)
                        success = True
                        break
                    except:
                        continue
            except Exception as e:
                print(f"Alternative date selection failed: {e}")
        
        # Strategy 3: JavaScript input method
        if not success:
            try:
                print("Trying JavaScript date input method...")
                js_script = f"""
                var checkinInput = document.querySelector('input[name="checkin"]') || 
                                 document.querySelector('input[data-testid="searchbox-checkin-date"]') ||
                                 document.querySelector('input[placeholder*="Check-in"]');
                if (checkinInput) {{
                    checkinInput.value = '{checkin_date}';
                    checkinInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    checkinInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                }}
                
                var checkoutInput = document.querySelector('input[name="checkout"]') ||
                                  document.querySelector('input[data-testid="searchbox-checkout-date"]') ||
                                  document.querySelector('input[placeholder*="Check-out"]');
                if (checkoutInput) {{
                    checkoutInput.value = '{checkout_date}';
                    checkoutInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    checkoutInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                }}
                
                return checkinInput && checkoutInput;
                """
                result = driver.execute_script(js_script)
                if result:
                    print("Dates set via JavaScript")
                    success = True
                    time.sleep(2)
            except Exception as e:
                print(f"JavaScript date setting failed: {e}")
        
        if success:
            print("✅ Date selection successful")
            return True
        else:
            print("❌ All date selection strategies failed")
            return False
            
    except Exception as e:
        print(f"Date selection error: {e}")
        return False


# Function to search for hotels with improved logic
def search_hotels(driver):
    try:
        print("Looking for search button...")
        
        # Multiple selectors for search button
        search_selectors = [
            "button[type='submit']",
            "button[data-testid='submit']",
            ".sb-searchbox__button",
            "button.fc63351294",
            "button[aria-label*='Search']",
            "form button[type='submit']"
        ]
        
        search_button = None
        for selector in search_selectors:
            try:
                search_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                print(f"Found search button with selector: {selector}")
                break
            except:
                continue
        
        if not search_button:
            print("Could not find search button")
            return False
        
        print("Clicking search button...")
        search_button.click()
        time.sleep(5)  # Give more time for navigation
        
        print("Waiting for search results...")
        result_selectors = [
            "div[data-testid='property-card']",
            "[data-testid='property-card']",
            ".sr_item",
            ".hotel-card",
            "[data-testid='property-list-item']"
        ]
        
        results_found = False
        for selector in result_selectors:
            try:
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                print(f"Search results found with selector: {selector}")
                results_found = True
                break
            except:
                continue
        
        if not results_found:
            print("No search results found - checking current page...")
            current_url = driver.current_url
            print(f"Current URL: {current_url}")
            
            # Check if we're still on the main page
            if "booking.com" in current_url and "/searchresults" not in current_url:
                print("Still on main page - search may not have worked")
                return False
        
        time.sleep(3)
        print("✅ Search completed successfully")
        return True
        
    except Exception as e:
        print(f"Search failed: {e}")
        return False


# Function to click the "Load more results" button with multiple detection strategies
def click_load_more(driver, max_clicks=4):
    print(f"Starting enhanced load more process (target: {max_clicks} clicks)")
    clicks = 0

    # Initial hotel count
    initial_hotels = len(driver.find_elements(By.CSS_SELECTOR, "div[data-testid='property-card'], .sr_item"))
    print(f"Initial hotel count: {initial_hotels}")
    
    if initial_hotels == 0:
        print("No hotels found on page - load more not applicable")
        return 0

    for attempt in range(max_clicks):
        print(f"\nLoad More Attempt {attempt + 1}/{max_clicks}")
        
        # Scroll to bottom with multiple scrolls to ensure everything is loaded
        print("Scrolling to bottom...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollBy(0, 500);")  # Additional scroll
        time.sleep(1)
        
        # Take screenshot for debugging 
        try:
            screenshot_path = f"load_more_attempt_{attempt+1}.png"
            driver.save_screenshot(screenshot_path)
            print(f"Screenshot saved: {screenshot_path}")
        except:
            pass
            
        # Try multiple detection strategies
        button_found = False

        # STRATEGY 1: By text content
        print("Strategy 1: Looking for button by text content...")
        try:
            buttons = driver.find_elements(By.XPATH, "//button[contains(., 'Load more') or contains(., 'load more') or contains(., 'Show more')]")
            if buttons:
                button_found = True
                print(f"✅ Found {len(buttons)} button(s) by text content")
                for btn in buttons:
                    if btn.is_displayed() and btn.is_enabled():
                        btn_text = btn.text.strip()
                        print(f"🎯 Found visible button with text: '{btn_text}'")
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                        time.sleep(1)
                        try:
                            btn.click()
                        except:
                            driver.execute_script("arguments[0].click();", btn)
                        clicks += 1
                        print(f"✅ Clicked button ({clicks}/{max_clicks})")
                        time.sleep(3)
                        break
        except Exception as e:
            print(f"⚠️ Strategy 1 error: {e}")
        
        # STRATEGY 2: By class or specific structure
        if not button_found:
            print("🔍 Strategy 2: Looking for button by class/structure...")
            try:
                # Try the span first (more specific)
                spans = driver.find_elements(By.CSS_SELECTOR, "span.ca2ca5203b")
                if spans:
                    for span in spans:
                        parent_button = span.find_element(By.XPATH, "./..")  # Get parent button
                        if parent_button.is_displayed() and parent_button.is_enabled():
                            print(f"🎯 Found button via span.ca2ca5203b")
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", parent_button)
                            time.sleep(1)
                            driver.execute_script("arguments[0].click();", parent_button)
                            button_found = True
                            clicks += 1
                            print(f"✅ Clicked button ({clicks}/{max_clicks})")
                            time.sleep(3)
                            break
            except Exception as e:
                print(f"⚠️ Strategy 2 error: {e}")
        
        # STRATEGY 3: By using JavaScript to find and click the button
        if not button_found:
            print("🔍 Strategy 3: Using JavaScript to find and click the button...")
            try:
                js_script = """
                // Look for load more button by text
                var buttons = Array.from(document.querySelectorAll('button'));
                var loadMoreBtn = buttons.find(btn => {
                    var text = btn.textContent.toLowerCase();
                    return text.includes('load more') || text.includes('show more');
                });
                
                if (loadMoreBtn) {
                    loadMoreBtn.scrollIntoView({block: 'center'});
                    loadMoreBtn.click();
                    return 'clicked';
                }
                
                // Look for the specific span
                var span = document.querySelector('span.ca2ca5203b');
                if (span && span.parentElement.tagName === 'BUTTON') {
                    span.parentElement.scrollIntoView({block: 'center'});
                    span.parentElement.click();
                    return 'clicked via span';
                }
                
                return false;
                """
                result = driver.execute_script(js_script)
                if result:
                    button_found = True
                    clicks += 1
                    print(f"✅ JavaScript click successful: {result} ({clicks}/{max_clicks})")
                    time.sleep(3)
            except Exception as e:
                print(f"⚠️ Strategy 3 error: {e}")
        
        # Check if we have more hotels after the click
        current_hotels = len(driver.find_elements(By.CSS_SELECTOR, "div[data-testid='property-card'], .sr_item"))
        print(f"Current hotel count: {current_hotels} (was {initial_hotels})")
        
        if current_hotels <= initial_hotels and button_found:
            print("⚠️ Button clicked but no new hotels loaded")
        
        if current_hotels > initial_hotels:
            print(f"✅ Success! Added {current_hotels - initial_hotels} new hotels")
            initial_hotels = current_hotels
        
        if not button_found:
            print("No load more button found - stopping")
            break
    
    final_hotels = len(driver.find_elements(By.CSS_SELECTOR, "div[data-testid='property-card'], .sr_item"))
    print(f"\nLOAD MORE COMPLETE:")
    print(f"  • Successful clicks: {clicks}/{max_clicks}")
    print(f"  • Final hotels: {final_hotels}")
    print(f"  • Total increase: +{final_hotels - initial_hotels} hotels")
    return clicks

# Function to extract hotel data from HTML with improved rating extraction
def extract_hotels(html_content):
    """Extract hotel data from HTML with improved rating extraction"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find hotel cards
    cards = soup.find_all('div', {'data-testid': 'property-card'})
    if not cards:
        cards = soup.find_all('div', class_=lambda x: x and 'sr_item' in x)
    
    print(f"Found {len(cards)} hotel cards to process")

    # Initialize list to hold hotel data
    hotels = []
    for i, card in enumerate(cards):
        try:
            # Name
            name_elem = card.find('div', {'data-testid': 'title'})
            name = name_elem.get_text(strip=True) if name_elem else None
            if not name:
                continue
            
            # Address
            address_elem = card.find('span', {'data-testid': 'address'})
            address = address_elem.get_text(strip=True) if address_elem else ""
            
            # Price
            price_elem = card.select_one('span[data-testid="price-and-discounted-price"]')
            if not price_elem:
                price_elem = card.select_one('span[data-testid="price"]')
            price_text = price_elem.get_text(strip=True) if price_elem else ""
            price = None
            if price_text:
                numbers = re.findall(r'\d+', price_text)
                if numbers:
                    price = int(numbers[0])
            
            # IMPROVED RATING EXTRACTION
            rating = None
            
            # Try multiple rating selectors
            rating_selectors = [
                'div[aria-label*="Scored"]',
                'div[data-testid="review-score"]',
                'span[data-testid="review-score"]',
                'div[class*="review-score"]',
                'span[class*="review-score"]',
                'div[aria-label*="rating"]',
                'div[aria-label*="Rating"]',
                'span[aria-label*="Scored"]'
            ]
            
            for selector in rating_selectors:
                try:
                    rating_elem = card.select_one(selector)
                    if rating_elem:
                        # Method 1: Extract from aria-label
                        aria_label = rating_elem.get('aria-label', '')
                        if aria_label:
                            # Look for patterns like "Scored 8.5", "Rating 9.1", etc.
                            patterns = [
                                r'Scored\s+(\d+\.?\d*)',
                                r'Rating\s+(\d+\.?\d*)', 
                                r'rating\s+(\d+\.?\d*)',
                                r'(\d+\.?\d*)\s+out\s+of',
                                r'(\d+\.?\d*)/10'
                            ]
                            
                            for pattern in patterns:
                                match = re.search(pattern, aria_label, re.IGNORECASE)
                                if match:
                                    rating = float(match.group(1))
                                    print(f"Rating found via aria-label: {rating} (pattern: {pattern})")
                                    break
                            
                            if rating:
                                break
                        
                        # Method 2: Extract from text content
                        rating_text = rating_elem.get_text(strip=True)
                        if rating_text and not rating:
                            # Look for number patterns in text
                            number_matches = re.findall(r'\d+\.?\d*', rating_text)
                            for num_text in number_matches:
                                try:
                                    potential_rating = float(num_text)
                                    # Validate rating range (typically 0-10 or 0-5)
                                    if 0 <= potential_rating <= 10:
                                        rating = potential_rating
                                        print(f"Rating found via text: {rating}")
                                        break
                                except:
                                    continue
                            
                            if rating:
                                break
                                
                except Exception as e:
                    continue
            
            # Additional rating search - look for any element with rating-like text
            if not rating:
                try:
                    # Search all elements for rating patterns
                    all_text_elements = card.find_all(text=re.compile(r'\d+\.?\d*'))
                    for text in all_text_elements:
                        # Look for rating-like patterns in surrounding context
                        parent = text.parent if text.parent else None
                        if parent:
                            parent_text = parent.get_text(strip=True)
                            parent_class = ' '.join(parent.get('class', []))
                            
                            # Check if parent has rating-related classes or attributes
                            if any(keyword in parent_class.lower() for keyword in ['rating', 'score', 'review']):
                                numbers = re.findall(r'\d+\.?\d*', parent_text)
                                for num_text in numbers:
                                    try:
                                        potential_rating = float(num_text)
                                        if 0 <= potential_rating <= 10:
                                            rating = potential_rating
                                            print(f"Rating found via class search: {rating}")
                                            break
                                    except:
                                        continue
                                if rating:
                                    break
                except:
                    pass
            
            # Distance
            distance_elem = card.find('span', {'data-testid': 'distance'})
            distance = distance_elem.get_text(strip=True) if distance_elem else ""
            
            # Debug output for first few hotels
            if i < 3:
                print(f"Hotel {i+1}: {name}")
                print(f"  Price: {price}")
                print(f"  Rating: {rating}")
                print(f"  Address: {address[:50]}..." if len(address) > 50 else f"  Address: {address}")
            
            hotels.append({
                'name': name,
                'address': address,
                'price': price,
                'rating': rating,
                'distance': distance,
                'scraped_at': datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"⚠️ Error extracting hotel {i}: {e}")
            continue
    
    print(f"Successfully extracted {len(hotels)} hotels")
    return hotels


# Function to process hotel data into a DataFrame with categorizations
def process_data(hotels_data):
    """Convert to DataFrame and add simple categorizations with better rating handling"""
    if not hotels_data:
        return None
    
    df = pd.DataFrame(hotels_data)
    
    # Debug: Check rating distribution
    if 'rating' in df.columns:
        rating_count = df['rating'].notna().sum()
        total_count = len(df)
        print(f"Rating stats: {rating_count}/{total_count} hotels have ratings")
        
        if rating_count > 0:
            print(f"Rating range: {df['rating'].min():.1f} - {df['rating'].max():.1f}")
            print(f"Average rating: {df['rating'].mean():.1f}")
    
    # Price categories
    def price_category(price):
        if pd.isna(price) or price is None:
            return 'No Price'
        elif price < 100:
            return 'Budget'
        elif price < 300:
            return 'Mid-range'
        else:
            return 'Luxury'
    
    # Rating categories with better handling
    def rating_category(rating):
        if pd.isna(rating) or rating is None:
            return 'No Rating'
        elif rating >= 9:
            return 'Excellent'
        elif rating >= 8:
            return 'Very Good'
        elif rating >= 7:
            return 'Good'
        elif rating >= 6:
            return 'Fair'
        else:
            return 'Average'
    
    df['price_category'] = df['price'].apply(price_category)
    df['rating_category'] = df['rating'].apply(rating_category)
    
    # Show category distribution
    print("\nPrice category distribution:")
    print(df['price_category'].value_counts())
    print("\nRating category distribution:")
    print(df['rating_category'].value_counts())
    
    return df

# Function to save DataFrame to CSV 
def process_data(hotels_data):
    if not hotels_data:
        return None
    
    df = pd.DataFrame(hotels_data)
    
    # Price categories
    def price_category(price):
        if pd.isna(price) or price is None:
            return 'No Price'
        elif price < 100:
            return 'Budget'
        elif price < 300:
            return 'Mid-range'
        else:
            return 'Luxury'
    
    # Rating categories  
    def rating_category(rating):
        if pd.isna(rating) or rating is None:
            return 'No Rating'
        elif rating >= 9:
            return 'Excellent'
        elif rating >= 8:
            return 'Very Good'
        elif rating >= 7:
            return 'Good'
        else:
            return 'Average'
    
    df['price_category'] = df['price'].apply(price_category)
    df['rating_category'] = df['rating'].apply(rating_category)
    
    return df

def save_data(df, filename=None):
    """Save DataFrame to CSV"""
    if df is None or df.empty:
        print("No data to save")
        return
    
    # Create output directory
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    
    # Generate filename
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"hotels_{timestamp}.csv"
    
    filepath = output_dir / filename
    df.to_csv(filepath, index=False)
    print(f"✅ Data saved: {filepath}")
    
    # # Also save as latest
    # latest_path = output_dir / "hotels_latest.csv"
    # df.to_csv(latest_path, index=False)
    # print(f"✅ Latest saved: {latest_path}")
    
    return filepath


# Function to load DataFrame to PostgreSQL database
def load_to_database(df, table_name="lodgify_hotels", if_exists="append"):
    try:
        from dotenv import load_dotenv
        import os
        from urllib.parse import quote_plus
        from sqlalchemy import create_engine
        
        print("🔄 Loading data to PostgreSQL...")
        
        # Load environment variables
        load_dotenv()
        DB_HOST = os.getenv('DB_HOST')
        DB_PORT = os.getenv('DB_PORT')
        DB_NAME = os.getenv('DB_NAME')
        DB_USER = os.getenv('DB_USER')
        DB_PASSWORD = os.getenv('DB_PASSWORD')
        
        if not all([DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD]):
            print("❌ Database credentials not found in .env file")
            return False
        
        # URL-encode the password to handle special characters like '@'
        DB_PASSWORD_ENC = quote_plus(DB_PASSWORD)
        
        # Create connection string
        db_url = f'postgresql://{DB_USER}:{DB_PASSWORD_ENC}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
        
        # Create engine
        engine = create_engine(db_url)
        
        # Load DataFrame to database
        df.to_sql(table_name, engine, if_exists=if_exists, index=False)
        
        print(f"✅ Successfully loaded {len(df)} records to '{table_name}' table")
        return True
    
    except Exception as e:
        print(f"❌ Database loading failed: {e}")
        return False


# Test function for date selection
def test_date_selection():
    """Test just the date selection functionality"""
    print("🧪 Testing Date Selection")
    print("=" * 40)
    
    from datetime import datetime, timedelta
    
    # Generate dates
    checkin = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    checkout = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')
    print(f"Test dates: {checkin} to {checkout}")
    
    driver = None
    try:
        # Setup browser in visible mode
        driver = create_driver(headless=False)
        
        # Navigate to booking
        navigate_to_booking(driver)
        time.sleep(2)
        
        # Set destination
        set_destination(driver, "London")
        time.sleep(2)
        
        # Test date selection
        date_success = select_dates(driver, checkin, checkout)
        
        if date_success:
            print("✅ Date selection test passed!")
            
            # Try to search
            search_success = search_hotels(driver)
            if search_success:
                print("✅ Search test passed!")
                
                # Test load more
                clicks = click_load_more(driver, max_clicks=4)  # Increased to 4 clicks
                print(f"✅ Load more test: {clicks} clicks")
            else:
                print("❌ Search test failed")
        else:
            print("❌ Date selection test failed")
        
        print("\nBrowser will stay open for 10 seconds for inspection...")
        time.sleep(10)
        
    except Exception as e:
        print(f"Test error: {e}")
    finally:
        if driver:
            driver.quit()

# Main function to scrape hotels with all steps coordinated
def scrape_hotels(checkin_date=None, checkout_date=None, destination="London", headless=True, load_db=True):
    """
    Main scraper function - coordinates all steps
    
    Args:
        checkin_date: Check-in date (YYYY-MM-DD) or None for 7 days from now
        checkout_date: Check-out date (YYYY-MM-DD) or None for 10 days from now  
        destination: Destination city (default: London)
        headless: Run browser in headless mode
        load_db: Load data to database (default: True)
        
    Returns:
        DataFrame with hotel data
    """
    
    # Set default dates
    if not checkin_date:
        checkin_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    if not checkout_date:
        checkout_date = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')
    
    print(f"🔍 Scraping hotels for {destination}: {checkin_date} to {checkout_date}")
    
    driver = None
    try:
        # Step 1: Setup browser
        print("🚀 Setting up browser...")
        driver = create_driver(headless)
        
        # Step 2: Navigate and setup search
        print("🌐 Navigating to Booking.com...")
        navigate_to_booking(driver)
        
        print(f"📍 Setting destination: {destination}")
        set_destination(driver, destination)
        
        print(f"📅 Selecting dates: {checkin_date} to {checkout_date}")
        select_dates(driver, checkin_date, checkout_date)
        
        # Step 3: Search
        print("🔍 Searching hotels...")
        if not search_hotels(driver):
            return None
        
        # Step 4: Load more content
        print("📄 Loading more content...")
        clicks = click_load_more(driver, max_clicks=4)
        print(f"✅ Completed {clicks} load more clicks")
        
        # Step 5: Extract data
        print("🏨 Extracting hotel data...")
        hotels_data = extract_hotels(driver.page_source)
        print(f"✅ Extracted {len(hotels_data)} hotels")
        
        # Step 6: Process data
        print("📊 Processing data...")
        df = process_data(hotels_data)
        
        if df is not None:
            print(f"✅ Successfully processed {len(df)} hotels")
            
            # Save to CSV
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            csv_filename = f"hotels_{destination}_{timestamp}.csv"
            filepath = save_data(df, filename=csv_filename)
            
            # Step 7: Load to database (if enabled)
            if load_db:
                table_name = "lodgify_hotels"
                load_success = load_to_database(df, table_name=table_name)
                if load_success:
                    print(f"✅ Data loaded to database table: {table_name}")
                else:
                    print("⚠️ Database loading skipped or failed")
        
        return df
        
    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        return None
    finally:
        if driver:
            driver.quit()
            print("🔒 Browser closed")



# Test function for the scraper
def test_scraper(load_db=False):
    """Test the scraper with default settings"""
    print("🧪 Testing Hotel Scraper")
    print("=" * 50)
    
    # Test with visible browser and option to load to database
    df = scrape_hotels(headless=False, load_db=load_db)
    
    if df is not None and not df.empty:
        print(f"\n📊 Test Results:")
        print(f"  • Total hotels: {len(df)}")
        print(f"  • Hotels with prices: {df['price'].notna().sum()}")
        print(f"  • Hotels with ratings: {df['rating'].notna().sum()}")
        
        # Show sample
        print(f"\n🏨 Sample Hotels:")
        cols = ['name', 'price', 'rating', 'price_category', 'rating_category']
        available_cols = [col for col in cols if col in df.columns]
        print(df[available_cols].head())
        
        if not load_db:
            print("\n⚠️ Database loading was disabled for this test")
            print("To load data to database, run: test_scraper(load_db=True)")
        
        print(f"\n✅ Test completed successfully!")
        return True
    else:
        print(f"\n❌ Test failed - no data extracted")
        return False

# Function to select dates with multiple strategies
def test_date_selection():
    print("🧪 Testing Date Selection")
    print("=" * 40)
    
    from datetime import datetime, timedelta
    
    # Generate dates
    checkin = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    checkout = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')
    print(f"Test dates: {checkin} to {checkout}")
    
    driver = None
    try:
        # Setup browser in visible mode
        driver = create_driver(headless=False)
        
        # Navigate to booking
        navigate_to_booking(driver)
        time.sleep(2)
        
        # Set destination
        set_destination(driver, "London")
        time.sleep(2)
        
        # Test date selection
        date_success = select_dates(driver, checkin, checkout)
        
        if date_success:
            print("✅ Date selection test passed!")
            
            # Try to search
            search_success = search_hotels(driver)
            if search_success:
                print("✅ Search test passed!")
                
                # Test load more
                clicks = click_load_more(driver, max_clicks=4)  # Increased to 4 clicks
                print(f"✅ Load more test: {clicks} clicks")
            else:
                print("❌ Search test failed")
        else:
            print("❌ Date selection test failed")
        
        print("\nBrowser will stay open for 10 seconds for inspection...")
        time.sleep(10)
        
    except Exception as e:
        print(f"Test error: {e}")
    finally:
        if driver:
            driver.quit()


# Main entry point for running tests or full scraper
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test-dates":
        # Run date selection test
        test_date_selection()
    else:
        # Run the full test
        # Run the scraper with database loading enabled
        test_scraper(load_db=True)