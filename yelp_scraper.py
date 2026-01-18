"""
Yelp Coachella Reviews Scraper
Menggunakan Selenium + BeautifulSoup untuk scraping review dari Yelp

Output columns: username, from, written_date, rating, title, review_text, tema_pengalaman, daya_tarik_wisata
"""

import time
import csv
import re
import argparse
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


class YelpScraper:
    """Scraper untuk mengambil review dari halaman Yelp"""
    
    BASE_URL = "https://www.yelp.com/biz/coachella-indio-2"
    
    def __init__(self, headless: bool = True):
        """
        Initialize scraper dengan Chrome WebDriver
        
        Args:
            headless: Run browser tanpa GUI jika True
        """
        self.options = Options()
        if headless:
            self.options.add_argument("--headless=new")
        
        # Options untuk menghindari deteksi bot
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_argument("--disable-extensions")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--window-size=1920,1080")
        self.options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = None
        self.reviews = []
        
    def start_driver(self):
        """Start Chrome WebDriver"""
        print("[*] Starting Chrome WebDriver...")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=self.options)
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
        })
        print("[OK] WebDriver started successfully")
        
    def close_driver(self):
        """Close WebDriver"""
        if self.driver:
            self.driver.quit()
            print("[STOP] WebDriver closed")
            
    def get_page(self, start: int = 0) -> str:
        """
        Navigate ke halaman review dengan pagination
        
        Args:
            start: Offset untuk pagination (0, 10, 20, ...)
            
        Returns:
            HTML page source
        """
        url = f"{self.BASE_URL}?start={start}" if start > 0 else self.BASE_URL
        print(f"[PAGE] Loading: {url}")
        
        self.driver.get(url)
        
        # Wait for reviews to load
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='review']"))
            )
            # Extra wait for dynamic content
            time.sleep(2)
        except TimeoutException:
            print(f"[WARN] Timeout waiting for reviews on page start={start}")
            
        return self.driver.page_source
    
    def parse_reviews(self, html: str) -> list:
        """
        Parse review dari HTML page
        
        Args:
            html: HTML source dari halaman Yelp
            
        Returns:
            List of review dictionaries
        """
        soup = BeautifulSoup(html, 'lxml')
        reviews = []
        
        # Find all review containers - Yelp uses various class patterns
        review_containers = soup.find_all('li', class_=re.compile(r'.*margin-b.*|.*review.*', re.I))
        
        # Alternative selectors if the above doesn't work
        if not review_containers:
            review_containers = soup.find_all('div', {'data-review-id': True})
            
        if not review_containers:
            # Try finding by user profile links pattern
            user_links = soup.find_all('a', href=re.compile(r'/user_details\?userid='))
            review_containers = [link.find_parent('li') or link.find_parent('div') for link in user_links]
            review_containers = [r for r in review_containers if r]
        
        print(f"   Found {len(review_containers)} potential review containers")
        
        for container in review_containers:
            try:
                review = self._extract_review_data(container)
                if review and review.get('username'):
                    reviews.append(review)
            except Exception as e:
                print(f"   [WARN] Error parsing review: {e}")
                continue
                
        return reviews
    
    def _extract_review_data(self, container) -> dict:
        """
        Extract data dari single review container
        
        Args:
            container: BeautifulSoup element untuk satu review
            
        Returns:
            Dictionary dengan review data
        """
        review = {
            'username': '',
            'from': '',
            'written_date': '',
            'rating': '',
            'title': '',
            'review_text': '',
            'tema_pengalaman': '',
            'daya_tarik_wisata': ''
        }
        
        # Username - look for user profile link
        user_link = container.find('a', href=re.compile(r'/user_details\?userid='))
        if user_link:
            # Get text or aria-label
            review['username'] = user_link.get_text(strip=True) or user_link.get('aria-label', '')
        
        # Location (from) - usually near username
        # Look for location patterns like "City, ST" or just location text
        location_patterns = [
            container.find('span', class_=re.compile(r'.*location.*|.*css-qgunke.*', re.I)),
            container.find('span', string=re.compile(r'^[A-Za-z\s]+,\s*[A-Z]{2}$')),
        ]
        for loc in location_patterns:
            if loc:
                review['from'] = loc.get_text(strip=True)
                break
        
        # If location not found, try to find by pattern in text
        if not review['from']:
            all_text = container.get_text()
            loc_match = re.search(r'([A-Za-z\s]+,\s*[A-Z]{2})\d', all_text)
            if loc_match:
                review['from'] = loc_match.group(1).strip()
        
        # Date - look for date patterns
        date_patterns = [
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}',
            r'\d{1,2}/\d{1,2}/\d{4}'
        ]
        all_text = container.get_text()
        for pattern in date_patterns:
            date_match = re.search(pattern, all_text)
            if date_match:
                review['written_date'] = date_match.group()
                break
        
        # Rating - look for star rating
        # Yelp uses aria-label like "5 star rating"
        rating_elem = container.find(attrs={'aria-label': re.compile(r'\d+\s*star', re.I)})
        if rating_elem:
            rating_match = re.search(r'(\d+)', rating_elem.get('aria-label', ''))
            if rating_match:
                review['rating'] = rating_match.group(1)
        
        # Alternative: look for role="img" with star rating
        if not review['rating']:
            star_elem = container.find(attrs={'role': 'img', 'aria-label': re.compile(r'star', re.I)})
            if star_elem:
                rating_match = re.search(r'(\d+)', star_elem.get('aria-label', ''))
                if rating_match:
                    review['rating'] = rating_match.group(1)
        
        # Review text - look for the main review content
        # Usually in a span or p with longer text
        review_text_candidates = container.find_all(['span', 'p'])
        for elem in review_text_candidates:
            text = elem.get_text(strip=True)
            # Review text is usually longer than 100 chars
            if len(text) > 100 and not re.match(r'^(Helpful|Thanks|Love|Oh no)', text):
                review['review_text'] = text
                break
        
        # If still no review text, get all text and clean it
        if not review['review_text']:
            # Find the comment/review section
            comment_section = container.find('span', {'lang': 'en'}) or container.find('p', {'lang': 'en'})
            if comment_section:
                review['review_text'] = comment_section.get_text(strip=True)
        
        # Title - Yelp reviews usually don't have titles, leave empty
        review['title'] = ''
        
        # tema_pengalaman - not available on Yelp, check for Elite status
        elite_badge = container.find('a', href='/elite')
        if elite_badge:
            elite_text = elite_badge.get_text(strip=True)
            review['tema_pengalaman'] = elite_text  # e.g., "Elite 26"
        
        # daya_tarik_wisata - use "Helpful" count
        helpful_pattern = re.search(r'Helpful\s*(\d+)', all_text)
        if helpful_pattern:
            review['daya_tarik_wisata'] = helpful_pattern.group(1)
        
        return review
    
    def scrape_all_reviews(self, limit: int = None) -> list:
        """
        Scrape semua review dengan pagination
        
        Args:
            limit: Maximum number of reviews to scrape (None = all)
            
        Returns:
            List of all reviews
        """
        self.start_driver()
        all_reviews = []
        start = 0
        page_num = 1
        consecutive_empty = 0
        max_consecutive_empty = 3
        
        try:
            while True:
                print(f"\n[PAGE] Page {page_num} (offset: {start})")
                
                html = self.get_page(start)
                page_reviews = self.parse_reviews(html)
                
                if not page_reviews:
                    consecutive_empty += 1
                    print(f"   [WARN] No reviews found on this page ({consecutive_empty}/{max_consecutive_empty})")
                    if consecutive_empty >= max_consecutive_empty:
                        print("   [STOP] Too many empty pages, stopping...")
                        break
                else:
                    consecutive_empty = 0
                    
                # Add reviews, avoiding duplicates
                for review in page_reviews:
                    if not any(r['username'] == review['username'] and 
                              r['written_date'] == review['written_date'] 
                              for r in all_reviews):
                        all_reviews.append(review)
                
                print(f"   [OK] Total reviews collected: {len(all_reviews)}")
                
                # Check limit
                if limit and len(all_reviews) >= limit:
                    print(f"\n[TARGET] Reached limit of {limit} reviews")
                    all_reviews = all_reviews[:limit]
                    break
                
                # Check if there's a next page
                # Yelp shows 10 reviews per page
                if len(page_reviews) < 10:
                    print("\n[END] Last page reached (fewer than 10 reviews)")
                    break
                
                # Move to next page
                start += 10
                page_num += 1
                
                # Be nice to the server
                time.sleep(3)
                
                # Safety limit to prevent infinite loops
                if page_num > 60:  # 60 pages * 10 = 600 reviews max
                    print("\n[STOP] Safety limit reached (60 pages)")
                    break
                    
        except KeyboardInterrupt:
            print("\n[WARN] Scraping interrupted by user")
        except Exception as e:
            print(f"\n[ERROR] Error during scraping: {e}")
        finally:
            self.close_driver()
            
        self.reviews = all_reviews
        return all_reviews
    
    def save_to_csv(self, filename: str = "yelp_coachella_reviews.csv"):
        """
        Simpan reviews ke CSV file
        
        Args:
            filename: Nama file output
        """
        if not self.reviews:
            print("[ERROR] No reviews to save")
            return
            
        columns = ['username', 'from', 'written_date', 'rating', 'title', 
                   'review_text', 'tema_pengalaman', 'daya_tarik_wisata']
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(self.reviews)
            
        print(f"\n[SAVE] Saved {len(self.reviews)} reviews to {filename}")


def main():
    parser = argparse.ArgumentParser(description='Yelp Coachella Reviews Scraper')
    parser.add_argument('--limit', type=int, default=None,
                        help='Maximum number of reviews to scrape (default: all)')
    parser.add_argument('--output', type=str, default='yelp_coachella_reviews.csv',
                        help='Output CSV filename')
    parser.add_argument('--show-browser', action='store_true',
                        help='Show browser window during scraping')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("YELP COACHELLA REVIEWS SCRAPER")
    print("=" * 60)
    print(f"Target: {YelpScraper.BASE_URL}")
    print(f"Limit: {args.limit or 'All reviews'}")
    print(f"Output: {args.output}")
    print("=" * 60)
    
    scraper = YelpScraper(headless=not args.show_browser)
    
    start_time = datetime.now()
    reviews = scraper.scrape_all_reviews(limit=args.limit)
    end_time = datetime.now()
    
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "=" * 60)
    print("SCRAPING SUMMARY")
    print("=" * 60)
    print(f"Total reviews: {len(reviews)}")
    print(f"Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    print(f"Rate: {len(reviews)/max(duration,1)*60:.1f} reviews/minute")
    
    if reviews:
        scraper.save_to_csv(args.output)
        
        # Show sample
        print("\nSample review:")
        sample = reviews[0]
        for key, value in sample.items():
            display_value = value[:50] + "..." if len(str(value)) > 50 else value
            print(f"   {key}: {display_value}")


if __name__ == "__main__":
    main()
