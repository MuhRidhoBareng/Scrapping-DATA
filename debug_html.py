"""Debug script to analyze Yelp HTML structure"""
import os
import re
from bs4 import BeautifulSoup

directory = os.path.dirname(os.path.abspath(__file__))
filepath = os.path.join(directory, "COACHELLA - Updated January 2026 - 3016 Photos & 557 Reviews - 81 800 Ave 51, Indio, California - Festivals - Yelp 1.html")

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

soup = BeautifulSoup(content, 'lxml')

print("=" * 60)
print("DEBUGGING HTML STRUCTURE")
print("=" * 60)

# Find review text spans
review_spans = soup.find_all('span', lang='en', class_=re.compile(r'raw'))
print(f"\n1. Found {len(review_spans)} review text spans with lang='en' and class containing 'raw'")

if review_spans:
    # Analyze first review span
    span = review_spans[0]
    text = span.get_text(strip=True)[:100]
    print(f"\n   First span text: {text}...")
    
    print("\n   Parent hierarchy:")
    current = span
    for i in range(20):
        parent = current.parent
        if parent is None:
            break
        
        # Get tag info
        tag_name = parent.name
        classes = parent.get('class', [])
        has_user_link = bool(parent.find('a', href=re.compile(r'/user_details\?userid=')))
        
        print(f"   [{i}] <{tag_name}> classes={classes[:2] if classes else []} has_user_link={has_user_link}")
        
        current = parent

# Find user links
print("\n" + "=" * 60)
user_links = soup.find_all('a', href=re.compile(r'/user_details\?userid='))
print(f"2. Found {len(user_links)} user profile links")

if user_links:
    # Show first few usernames
    for link in user_links[:5]:
        name = link.get_text(strip=True)
        if name:
            print(f"   - {name}")

# Check if user links and review spans share a common parent
print("\n" + "=" * 60)
print("3. Checking if reviews are in divs instead of li...")

# Try finding divs that contain both
for span in review_spans[:3]:
    text = span.get_text(strip=True)[:50]
    print(f"\n   Review: '{text}...'")
    
    # Go up levels looking for container with user link
    current = span
    for i in range(25):
        parent = current.parent
        if parent is None:
            print(f"   -> No parent found at level {i}")
            break
        
        user_link = parent.find('a', href=re.compile(r'/user_details\?userid='))
        if user_link:
            username = user_link.get_text(strip=True)
            print(f"   -> Found user '{username}' at level {i} in <{parent.name}>")
            break
        
        current = parent
    else:
        print("   -> No user link found in any parent")
