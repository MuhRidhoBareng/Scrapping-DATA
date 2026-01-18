"""
Yelp HTML Parser v5
Mengekstrak review dari file HTML Yelp yang disimpan secara lokal

Output columns: username, from, written_date, rating, title, review_text, 
                tema_pengalaman, daya_tarik_wisata, status, contribution
                
Filter: Tahun 2019-2025
"""

import os
import re
import csv
import glob
from bs4 import BeautifulSoup


def find_html_files(directory):
    """Find all Yelp HTML files in directory"""
    patterns = [
        os.path.join(directory, "COACHELLA*.html"),
        os.path.join(directory, "yelp*.html"),
    ]
    
    files = []
    for pattern in patterns:
        files.extend(glob.glob(pattern))
    
    # Sort by number in filename
    def extract_number(f):
        match = re.search(r'(\d+)\.html$', f)
        return int(match.group(1)) if match else 0
    
    files.sort(key=extract_number)
    return files


def extract_year(date_str):
    """Extract year from date string like 'Apr 23, 2025'"""
    if not date_str:
        return None
    match = re.search(r'(\d{4})', date_str)
    if match:
        return int(match.group(1))
    return None


def parse_html_file(filepath):
    """Parse a single HTML file and extract reviews"""
    print(f"[PARSE] Processing: {os.path.basename(filepath)}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(filepath, 'r', encoding='latin-1') as f:
            content = f.read()
    
    soup = BeautifulSoup(content, 'lxml')
    reviews = []
    
    # Find review text spans
    review_spans = soup.find_all('span', lang='en', class_=re.compile(r'raw'))
    
    for span in review_spans:
        review_text = span.get_text(strip=True)
        
        # Skip short texts
        if len(review_text) < 50:
            continue
        
        review = {
            'username': '',
            'from': '',
            'written_date': '',
            'rating': '',
            'title': '',
            'review_text': review_text,
            'tema_pengalaman': '',
            'daya_tarik_wisata': '',
            'status': '',           # Elite status
            'contribution': ''      # Review/photo count
        }
        
        # Go up to find the li container
        container = span
        for _ in range(10):
            parent = container.parent
            if parent is None:
                break
            if parent.name == 'li':
                container = parent
                break
            container = parent
        
        if container is None:
            continue
        
        # Find ALL user links in container
        user_links = container.find_all('a', href=re.compile(r'/user_details\?userid='))
        
        # Find the one with actual text (username)
        for link in user_links:
            text = link.get_text(strip=True)
            if text and len(text) >= 2 and re.match(r'^[A-Za-z]', text):
                review['username'] = text
                break
        
        if not review['username']:
            continue
        
        # Get all text from container
        container_text = container.get_text(' ', strip=True)
        
        # Extract location - format "City, ST" 
        loc_match = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?,\s*[A-Z]{2})\b', container_text)
        if loc_match:
            review['from'] = loc_match.group(1)
        
        # Extract date
        date_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}', container_text)
        if date_match:
            review['written_date'] = date_match.group()
        
        # Extract rating from aria-label
        rating_elem = container.find(attrs={'aria-label': re.compile(r'\d+\s*star', re.I)})
        if rating_elem:
            rating_match = re.search(r'(\d+)', rating_elem.get('aria-label', ''))
            if rating_match:
                review['rating'] = rating_match.group(1)
        
        # Extract Elite status (for both 'status' and 'tema_pengalaman')
        elite_link = container.find('a', href='/elite')
        if elite_link:
            elite_text = elite_link.get_text(strip=True)
            review['status'] = elite_text  # e.g., "Elite 26"
            review['tema_pengalaman'] = elite_text
        
        # Extract contribution (review count, photo count)
        # Look for patterns like "123 456 78" which are reviews/photos/friends counts
        contribution_match = re.search(r'(\d+)\s*(\d+)\s*(\d+)', container_text)
        if contribution_match:
            reviews_count = contribution_match.group(1)
            photos_count = contribution_match.group(2)
            review['contribution'] = f"{reviews_count} reviews, {photos_count} photos"
        
        # Extract helpful count for daya_tarik_wisata
        helpful_match = re.search(r'Helpful\s*(\d+)', container_text)
        if helpful_match:
            review['daya_tarik_wisata'] = helpful_match.group(1)
        
        reviews.append(review)
    
    print(f"   Extracted {len(reviews)} reviews")
    return reviews


def filter_by_year(reviews, start_year=2019, end_year=2025):
    """Filter reviews by year range"""
    filtered = []
    for r in reviews:
        year = extract_year(r.get('written_date', ''))
        if year and start_year <= year <= end_year:
            filtered.append(r)
    return filtered


def save_to_csv(reviews, output_file):
    """Save reviews to CSV file"""
    columns = ['username', 'from', 'written_date', 'rating', 'title', 
               'review_text', 'tema_pengalaman', 'daya_tarik_wisata', 
               'status', 'contribution']
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(reviews)
    
    print(f"\n[SAVED] {len(reviews)} reviews -> {output_file}")


def main():
    directory = os.path.dirname(os.path.abspath(__file__))
    
    print("=" * 60)
    print("YELP HTML PARSER v5")
    print("=" * 60)
    print(f"Directory: {directory}")
    print(f"Year filter: 2019-2025")
    
    html_files = find_html_files(directory)
    print(f"Found {len(html_files)} HTML files\n")
    
    if not html_files:
        print("[ERROR] No HTML files found!")
        return
    
    all_reviews = []
    for filepath in html_files:
        reviews = parse_html_file(filepath)
        all_reviews.extend(reviews)
    
    # Deduplicate
    seen = set()
    unique_reviews = []
    for r in all_reviews:
        key = (r.get('username', ''), r.get('review_text', '')[:100])
        if key not in seen and r.get('username'):
            seen.add(key)
            unique_reviews.append(r)
    
    print(f"\nTotal unique reviews before filter: {len(unique_reviews)}")
    
    # Filter by year 2019-2025
    filtered_reviews = filter_by_year(unique_reviews, 2019, 2025)
    
    print(f"Total reviews after year filter (2019-2025): {len(filtered_reviews)}")
    
    # Count by year
    year_counts = {}
    for r in filtered_reviews:
        year = extract_year(r.get('written_date', ''))
        if year:
            year_counts[year] = year_counts.get(year, 0) + 1
    
    print("\nReviews by year:")
    for year in sorted(year_counts.keys()):
        print(f"   {year}: {year_counts[year]} reviews")
    
    # Check for missing years
    for year in range(2019, 2026):
        if year not in year_counts:
            print(f"   {year}: 0 reviews (no data)")
    
    if filtered_reviews:
        output_file = os.path.join(directory, 'yelp_coachella_reviews.csv')
        save_to_csv(filtered_reviews, output_file)
        
        print("\n--- Sample Reviews ---")
        for i, r in enumerate(filtered_reviews[:3]):
            print(f"\n[{i+1}] {r['username']} from {r['from']}")
            print(f"    Date: {r['written_date']} | Rating: {r['rating']} stars")
            print(f"    Status: {r['status']} | Contribution: {r['contribution']}")
            print(f"    Helpful: {r['daya_tarik_wisata']}")
            print(f"    Review: {r['review_text'][:80]}...")
    else:
        print("[ERROR] No reviews extracted after filtering.")


if __name__ == "__main__":
    main()
