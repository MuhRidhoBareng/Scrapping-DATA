"""
Custom Universal Scraper
Scraper universal yang bisa dikonfigurasi untuk berbagai website

Usage:
    python custom_scraper.py                    # Menggunakan config default (Yelp)
    python custom_scraper.py --site tripadvisor # Menggunakan config TripAdvisor
    python custom_scraper.py --site google      # Menggunakan config Google
    python custom_scraper.py --site custom      # Menggunakan config custom
"""

import os
import re
import csv
import glob
import argparse
from bs4 import BeautifulSoup

# Import configurations
from scraper_config import (
    YELP_CONFIG, 
    TRIPADVISOR_CONFIG, 
    GOOGLE_CONFIG, 
    TEMPLATE_CONFIG,
    ACTIVE_CONFIG
)


class UniversalScraper:
    """Universal scraper yang bisa dikonfigurasi untuk berbagai website"""
    
    def __init__(self, config: dict):
        self.config = config
        self.reviews = []
        
    def find_html_files(self, directory: str) -> list:
        """Find HTML files matching pattern"""
        pattern = os.path.join(directory, self.config['file_pattern'])
        files = glob.glob(pattern)
        
        # Sort by number in filename
        def extract_number(f):
            match = re.search(r'(\d+)\.html$', f)
            return int(match.group(1)) if match else 0
        
        files.sort(key=extract_number)
        return files
    
    def parse_file(self, filepath: str) -> list:
        """Parse single HTML file"""
        print(f"[PARSE] {os.path.basename(filepath)}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(filepath, 'r', encoding='latin-1') as f:
                content = f.read()
        
        soup = BeautifulSoup(content, 'lxml')
        reviews = []
        
        # Find review text elements
        sel = self.config['selectors']['review_text']
        
        # Build search kwargs
        search_kwargs = {'name': sel['tag']}
        if 'attrs' in sel:
            for attr_name, attr_val in sel['attrs'].items():
                if attr_name == 'class':
                    # Class contains pattern
                    search_kwargs['class_'] = re.compile(attr_val)
                elif attr_name == 'lang':
                    search_kwargs['lang'] = attr_val
                else:
                    search_kwargs['attrs'] = {attr_name: re.compile(attr_val)}
        
        review_elements = soup.find_all(**search_kwargs)
        
        for elem in review_elements:
            review = self.extract_review(elem, soup)
            if review and review.get('username'):
                reviews.append(review)
        
        print(f"   Found {len(reviews)} reviews")
        return reviews
    
    def extract_review(self, elem, soup) -> dict:
        """Extract review data from element"""
        # Initialize with all columns
        review = {col: '' for col in self.config['columns']}
        
        # Get review text
        review_text = elem.get_text(strip=True)
        if len(review_text) < 50:
            return None
        review['review_text'] = review_text
        
        # Find container
        container = self.find_container(elem)
        if not container:
            return None
        
        container_text = container.get_text(' ', strip=True)
        
        # Extract username
        review['username'] = self.extract_username(container)
        if not review['username']:
            return None
        
        # Extract other fields using patterns
        patterns = self.config.get('patterns', {})
        
        # Location
        if 'location' in patterns and 'from' in review:
            match = re.search(patterns['location'], container_text)
            if match:
                review['from'] = match.group(1) if match.lastindex else match.group()
        
        # Date
        if 'date' in patterns and 'written_date' in review:
            match = re.search(patterns['date'], container_text)
            if match:
                review['written_date'] = match.group()
        
        # Rating
        review['rating'] = self.extract_rating(container)
        
        # Helpful count
        if 'helpful' in patterns and 'daya_tarik_wisata' in review:
            match = re.search(patterns['helpful'], container_text)
            if match:
                review['daya_tarik_wisata'] = match.group(1)
        
        # Contribution
        if 'contribution' in patterns and 'contribution' in review:
            match = re.search(patterns['contribution'], container_text)
            if match:
                review['contribution'] = f"{match.group(1)} reviews, {match.group(2)} photos"
        
        # Elite/Status
        if 'status' in review or 'tema_pengalaman' in review:
            status = self.extract_elite(container)
            if 'status' in review:
                review['status'] = status
            if 'tema_pengalaman' in review:
                review['tema_pengalaman'] = status
        
        return review
    
    def find_container(self, elem):
        """Find parent container for review"""
        sel = self.config['selectors']
        container_tag = sel.get('container_tag', 'div')
        levels = sel.get('container_levels_up', 10)
        
        current = elem
        for _ in range(levels):
            parent = current.parent
            if parent is None:
                break
            if parent.name == container_tag:
                # Check if this container has a user link
                username_sel = sel.get('username', {})
                user_tag = username_sel.get('tag', 'a')
                user_attrs = username_sel.get('attrs', {})
                
                # Build search
                for attr_name, attr_val in user_attrs.items():
                    user_elem = parent.find(user_tag, attrs={attr_name: re.compile(attr_val)})
                    if user_elem:
                        return parent
            current = parent
        
        return current  # Return last parent found
    
    def extract_username(self, container) -> str:
        """Extract username from container"""
        sel = self.config['selectors'].get('username', {})
        tag = sel.get('tag', 'a')
        attrs = sel.get('attrs', {})
        
        # Build search kwargs
        search_kwargs = {}
        for attr_name, attr_val in attrs.items():
            search_kwargs[attr_name] = re.compile(attr_val)
        
        links = container.find_all(tag, attrs=search_kwargs) if search_kwargs else container.find_all(tag)
        
        for link in links:
            text = link.get_text(strip=True)
            if text and len(text) >= 2 and re.match(r'^[A-Za-z]', text):
                return text
        
        return ''
    
    def extract_rating(self, container) -> str:
        """Extract rating from container"""
        sel = self.config['selectors'].get('rating', {})
        
        # Try aria-label pattern
        if 'aria_label_pattern' in sel:
            pattern = sel['aria_label_pattern']
            elem = container.find(attrs={'aria-label': re.compile(pattern, re.I)})
            if elem:
                match = re.search(r'(\d+)', elem.get('aria-label', ''))
                if match:
                    return match.group(1)
        
        # Try class pattern (for TripAdvisor style)
        if 'class_pattern' in sel:
            pattern = sel['class_pattern']
            for elem in container.find_all(class_=True):
                for cls in elem.get('class', []):
                    match = re.search(pattern, cls)
                    if match:
                        return str(int(match.group(1)) // 10)  # bubble_50 -> 5
        
        return ''
    
    def extract_elite(self, container) -> str:
        """Extract elite/status from container"""
        sel = self.config['selectors'].get('elite', {})
        if not sel:
            return ''
        
        tag = sel.get('tag', 'a')
        attrs = sel.get('attrs', {})
        
        search_kwargs = {}
        for attr_name, attr_val in attrs.items():
            search_kwargs[attr_name] = attr_val
        
        elem = container.find(tag, attrs=search_kwargs)
        if elem:
            return elem.get_text(strip=True)
        
        return ''
    
    def filter_by_year(self, reviews: list) -> list:
        """Filter reviews by year"""
        year_filter = self.config.get('year_filter', {})
        if not year_filter.get('enabled', False):
            return reviews
        
        start = year_filter.get('start', 2019)
        end = year_filter.get('end', 2025)
        
        filtered = []
        for r in reviews:
            date_str = r.get('written_date', '')
            match = re.search(r'(\d{4})', date_str)
            if match:
                year = int(match.group(1))
                if start <= year <= end:
                    filtered.append(r)
        
        return filtered
    
    def save_csv(self, reviews: list, output_path: str):
        """Save reviews to CSV"""
        columns = self.config['columns']
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(reviews)
        
        print(f"\n[SAVED] {len(reviews)} reviews -> {output_path}")
    
    def run(self, directory: str = None):
        """Run the scraper"""
        if directory is None:
            directory = os.path.dirname(os.path.abspath(__file__))
        
        print("=" * 60)
        print(f"UNIVERSAL SCRAPER - {self.config['name'].upper()}")
        print("=" * 60)
        print(f"Directory: {directory}")
        print(f"Pattern: {self.config['file_pattern']}")
        
        # Find files
        files = self.find_html_files(directory)
        print(f"Found {len(files)} files\n")
        
        if not files:
            print("[ERROR] No HTML files found!")
            return []
        
        # Parse all files
        all_reviews = []
        for f in files:
            reviews = self.parse_file(f)
            all_reviews.extend(reviews)
        
        # Deduplicate
        seen = set()
        unique = []
        for r in all_reviews:
            key = (r.get('username', ''), r.get('review_text', '')[:100])
            if key not in seen and r.get('username'):
                seen.add(key)
                unique.append(r)
        
        print(f"\nTotal unique: {len(unique)}")
        
        # Filter by year
        if self.config.get('year_filter', {}).get('enabled'):
            unique = self.filter_by_year(unique)
            start = self.config['year_filter']['start']
            end = self.config['year_filter']['end']
            print(f"After year filter ({start}-{end}): {len(unique)}")
        
        # Save
        if unique:
            output = os.path.join(directory, self.config['output_file'])
            self.save_csv(unique, output)
            
            # Show samples
            print("\n--- Samples ---")
            for i, r in enumerate(unique[:2]):
                print(f"\n[{i+1}] {r.get('username', 'N/A')}")
                for k, v in r.items():
                    if v and k != 'review_text':
                        print(f"    {k}: {v}")
                text = r.get('review_text', '')[:60]
                print(f"    review: {text}...")
        
        return unique


def get_config(site_name: str) -> dict:
    """Get configuration by site name"""
    configs = {
        'yelp': YELP_CONFIG,
        'tripadvisor': TRIPADVISOR_CONFIG,
        'google': GOOGLE_CONFIG,
        'custom': TEMPLATE_CONFIG
    }
    return configs.get(site_name.lower(), ACTIVE_CONFIG)


def main():
    parser = argparse.ArgumentParser(description='Universal Web Scraper')
    parser.add_argument('--site', type=str, default=None,
                        choices=['yelp', 'tripadvisor', 'google', 'custom'],
                        help='Site configuration to use')
    parser.add_argument('--dir', type=str, default=None,
                        help='Directory containing HTML files')
    
    args = parser.parse_args()
    
    # Get config
    if args.site:
        config = get_config(args.site)
    else:
        config = ACTIVE_CONFIG
    
    # Run scraper
    scraper = UniversalScraper(config)
    scraper.run(args.dir)


if __name__ == "__main__":
    main()
