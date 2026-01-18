"""
Scraper Configuration File
Ubah konfigurasi ini untuk scraping website yang berbeda
"""

# ============================================================
# KONFIGURASI UNTUK YELP
# ============================================================
YELP_CONFIG = {
    'name': 'yelp',
    'file_pattern': 'COACHELLA*.html',  # Pattern file HTML
    
    # CSS Selectors
    'selectors': {
        # Selector untuk menemukan review text
        'review_text': {
            'tag': 'span',
            'attrs': {'lang': 'en', 'class': 'raw'}  # class mengandung 'raw'
        },
        # Selector untuk container review (parent dari review_text)
        'container_tag': 'li',
        'container_levels_up': 10,  # Berapa level naik ke parent untuk menemukan container
        
        # Selector untuk username
        'username': {
            'tag': 'a',
            'attrs': {'href': '/user_details'}  # href mengandung ini
        },
        
        # Selector untuk rating (menggunakan aria-label)
        'rating': {
            'aria_label_pattern': r'\d+\s*star'
        },
        
        # Selector untuk Elite status
        'elite': {
            'tag': 'a',
            'attrs': {'href': '/elite'}
        }
    },
    
    # Regex patterns untuk ekstraksi data
    'patterns': {
        'location': r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?,\s*[A-Z]{2})\b',
        'date': r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}',
        'contribution': r'(\d+)\s*(\d+)\s*(\d+)',  # reviews, photos, friends
        'helpful': r'Helpful\s*(\d+)'
    },
    
    # Output columns
    'columns': [
        'username', 'from', 'written_date', 'rating', 'title',
        'review_text', 'tema_pengalaman', 'daya_tarik_wisata',
        'status', 'contribution'
    ],
    
    # Filter
    'year_filter': {
        'enabled': True,
        'start': 2019,
        'end': 2025
    },
    
    # Output
    'output_file': 'yelp_reviews.csv'
}

# ============================================================
# KONFIGURASI UNTUK TRIPADVISOR
# ============================================================
TRIPADVISOR_CONFIG = {
    'name': 'tripadvisor',
    'file_pattern': 'tripadvisor*.html',
    
    'selectors': {
        'review_text': {
            'tag': 'div',
            'attrs': {'class': 'review-text'}
        },
        'container_tag': 'div',
        'container_levels_up': 5,
        
        'username': {
            'tag': 'a',
            'attrs': {'class': 'member'}
        },
        
        'rating': {
            'class_pattern': r'bubble_(\d+)'  # bubble_50 = 5 stars
        }
    },
    
    'patterns': {
        'location': r'\b([A-Za-z\s]+,\s*[A-Za-z\s]+)\b',
        'date': r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}',
        'helpful': r'(\d+)\s*helpful'
    },
    
    'columns': [
        'username', 'from', 'written_date', 'rating', 'title',
        'review_text', 'tema_pengalaman', 'daya_tarik_wisata'
    ],
    
    'year_filter': {
        'enabled': True,
        'start': 2019,
        'end': 2025
    },
    
    'output_file': 'tripadvisor_reviews.csv'
}

# ============================================================
# KONFIGURASI UNTUK GOOGLE REVIEWS
# ============================================================
GOOGLE_CONFIG = {
    'name': 'google',
    'file_pattern': 'google*.html',
    
    'selectors': {
        'review_text': {
            'tag': 'span',
            'attrs': {'class': 'review-content'}
        },
        'container_tag': 'div',
        'container_levels_up': 8,
        
        'username': {
            'tag': 'div',
            'attrs': {'class': 'reviewer-name'}
        },
        
        'rating': {
            'aria_label_pattern': r'(\d+)\s*stars?'
        }
    },
    
    'patterns': {
        'location': r'Local Guide',
        'date': r'(\d+)\s*(day|week|month|year)s?\s*ago',
        'helpful': r'(\d+)\s*found\s*helpful'
    },
    
    'columns': [
        'username', 'from', 'written_date', 'rating', 'review_text'
    ],
    
    'year_filter': {
        'enabled': False
    },
    
    'output_file': 'google_reviews.csv'
}

# ============================================================
# TEMPLATE UNTUK WEBSITE BARU
# ============================================================
TEMPLATE_CONFIG = {
    'name': 'custom_site',           # Nama website
    'file_pattern': '*.html',         # Pattern file HTML
    
    'selectors': {
        'review_text': {
            'tag': 'div',             # Tag HTML yang berisi review
            'attrs': {'class': 'review'}  # Atribut untuk mencari
        },
        'container_tag': 'div',       # Tag container review
        'container_levels_up': 5,     # Level parent untuk mencari
        
        'username': {
            'tag': 'span',
            'attrs': {'class': 'username'}
        },
        
        'rating': {
            'aria_label_pattern': r'\d+\s*star'  # Regex untuk rating
        }
    },
    
    'patterns': {
        'location': r'([A-Za-z\s]+)',           # Regex lokasi
        'date': r'(\w+\s+\d+,\s+\d{4})',        # Regex tanggal
        'helpful': r'(\d+)'                      # Regex helpful count
    },
    
    'columns': [                                # Kolom output
        'username', 'from', 'written_date', 'rating', 'review_text'
    ],
    
    'year_filter': {
        'enabled': False,
        'start': 2020,
        'end': 2025
    },
    
    'output_file': 'custom_reviews.csv'
}

# ============================================================
# PILIH KONFIGURASI AKTIF
# Ubah ini untuk menggunakan konfigurasi yang berbeda
# ============================================================
ACTIVE_CONFIG = YELP_CONFIG
