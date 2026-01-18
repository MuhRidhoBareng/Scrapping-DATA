"""
Web Scraper Desktop Application
GUI untuk scraping review dari berbagai website (Yelp, TripAdvisor, Google, dll)

Requirements:
    pip install beautifulsoup4 lxml
"""

import os
import re
import csv
import glob
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime
from bs4 import BeautifulSoup


class ScraperConfig:
    """Konfigurasi untuk berbagai website"""
    
    PRESETS = {
        'Yelp': {
            'file_pattern': '*.html',
            'review_tag': 'span',
            'review_class': 'raw',
            'review_lang': 'en',
            'container_tag': 'li',
            'container_levels': 10,
            'username_tag': 'a',
            'username_attr': 'href',
            'username_pattern': '/user_details',
            'location_pattern': r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?,\s*[A-Z]{2})\b',
            'date_pattern': r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}',
            'rating_pattern': r'(\d+)\s*star',
            'helpful_pattern': r'Helpful\s*(\d+)',
            'contribution_pattern': r'(\d+)\s*(\d+)\s*(\d+)',
            'elite_tag': 'a',
            'elite_attr': 'href',
            'elite_pattern': '/elite'
        },
        'TripAdvisor': {
            'file_pattern': '*.html',
            'review_tag': 'div',
            'review_class': 'review',
            'review_lang': '',
            'container_tag': 'div',
            'container_levels': 5,
            'username_tag': 'a',
            'username_attr': 'class',
            'username_pattern': 'member',
            'location_pattern': r'([A-Za-z\s]+,\s*[A-Za-z\s]+)',
            'date_pattern': r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}',
            'rating_pattern': r'bubble_(\d+)',
            'helpful_pattern': r'(\d+)\s*helpful',
            'contribution_pattern': r'(\d+)\s*contributions',
            'elite_tag': '',
            'elite_attr': '',
            'elite_pattern': ''
        },
        'Google Reviews': {
            'file_pattern': '*.html',
            'review_tag': 'span',
            'review_class': 'review',
            'review_lang': '',
            'container_tag': 'div',
            'container_levels': 8,
            'username_tag': 'div',
            'username_attr': 'class',
            'username_pattern': 'name',
            'location_pattern': r'Local Guide',
            'date_pattern': r'(\d+)\s*(day|week|month|year)s?\s*ago',
            'rating_pattern': r'(\d+)\s*star',
            'helpful_pattern': r'(\d+)\s*found',
            'contribution_pattern': r'(\d+)\s*review',
            'elite_tag': '',
            'elite_attr': '',
            'elite_pattern': ''
        },
        'Custom': {
            'file_pattern': '*.html',
            'review_tag': 'div',
            'review_class': 'review',
            'review_lang': '',
            'container_tag': 'div',
            'container_levels': 5,
            'username_tag': 'span',
            'username_attr': 'class',
            'username_pattern': 'username',
            'location_pattern': r'([A-Za-z\s,]+)',
            'date_pattern': r'(\w+\s+\d+,\s+\d{4})',
            'rating_pattern': r'(\d+)',
            'helpful_pattern': r'(\d+)',
            'contribution_pattern': r'(\d+)',
            'elite_tag': '',
            'elite_attr': '',
            'elite_pattern': ''
        }
    }


class ScraperApp:
    """Main Desktop Application"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Web Scraper - Review Extractor")
        self.root.geometry("900x800")
        self.root.minsize(800, 700)
        
        # Variables
        self.folder_path = tk.StringVar()
        self.preset_var = tk.StringVar(value='Yelp')
        self.year_start = tk.StringVar(value='2019')
        self.year_end = tk.StringVar(value='2025')
        self.year_filter_enabled = tk.BooleanVar(value=True)
        self.output_file = tk.StringVar(value='scraped_reviews.csv')
        
        self.reviews = []
        self.is_running = False
        self.selected_files = []  # For direct file selection
        
        self.create_gui()
        self.apply_theme()
        
    def create_gui(self):
        """Create the GUI layout"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ========== HEADER ==========
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(header_frame, text="🌐 Web Scraper", 
                                font=('Segoe UI', 18, 'bold'))
        title_label.pack(side=tk.LEFT)
        
        subtitle = ttk.Label(header_frame, text="Review Extractor Tool",
                            font=('Segoe UI', 10))
        subtitle.pack(side=tk.LEFT, padx=10, pady=5)
        
        # ========== FOLDER SELECTION ==========
        folder_frame = ttk.LabelFrame(main_frame, text="📁 Select HTML Files", padding="10")
        folder_frame.pack(fill=tk.X, pady=5)
        
        # Row 1: Path entry and folder browse
        path_row = ttk.Frame(folder_frame)
        path_row.pack(fill=tk.X, pady=2)
        
        folder_entry = ttk.Entry(path_row, textvariable=self.folder_path, width=50)
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        browse_folder_btn = ttk.Button(path_row, text="📁 Folder", command=self.browse_folder)
        browse_folder_btn.pack(side=tk.LEFT, padx=2)
        
        browse_files_btn = ttk.Button(path_row, text="📄 Files", command=self.browse_files)
        browse_files_btn.pack(side=tk.LEFT, padx=2)
        
        # Row 2: Options
        options_row = ttk.Frame(folder_frame)
        options_row.pack(fill=tk.X, pady=2)
        
        self.recursive_var = tk.BooleanVar(value=True)
        recursive_check = ttk.Checkbutton(options_row, text="Search subfolders", 
                                          variable=self.recursive_var)
        recursive_check.pack(side=tk.LEFT)
        
        self.file_count_label = ttk.Label(options_row, text="", foreground='blue')
        self.file_count_label.pack(side=tk.RIGHT)
        
        # ========== CONFIGURATION ==========
        config_frame = ttk.LabelFrame(main_frame, text="⚙️ Configuration", padding="10")
        config_frame.pack(fill=tk.X, pady=5)
        
        # Row 1: Preset and Output
        row1 = ttk.Frame(config_frame)
        row1.pack(fill=tk.X, pady=5)
        
        ttk.Label(row1, text="Website Preset:").pack(side=tk.LEFT)
        preset_combo = ttk.Combobox(row1, textvariable=self.preset_var, 
                                    values=list(ScraperConfig.PRESETS.keys()),
                                    state='readonly', width=15)
        preset_combo.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(row1, text="Output File:").pack(side=tk.LEFT, padx=(20, 0))
        output_entry = ttk.Entry(row1, textvariable=self.output_file, width=30)
        output_entry.pack(side=tk.LEFT, padx=10)
        
        # Row 2: Year Filter
        row2 = ttk.Frame(config_frame)
        row2.pack(fill=tk.X, pady=5)
        
        year_check = ttk.Checkbutton(row2, text="Filter by Year:", 
                                     variable=self.year_filter_enabled)
        year_check.pack(side=tk.LEFT)
        
        ttk.Label(row2, text="From").pack(side=tk.LEFT, padx=(10, 5))
        year_start_entry = ttk.Entry(row2, textvariable=self.year_start, width=6)
        year_start_entry.pack(side=tk.LEFT)
        
        ttk.Label(row2, text="To").pack(side=tk.LEFT, padx=5)
        year_end_entry = ttk.Entry(row2, textvariable=self.year_end, width=6)
        year_end_entry.pack(side=tk.LEFT)
        
        # ========== BUTTONS ==========
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.start_btn = ttk.Button(button_frame, text="▶ Start Scraping", 
                                    command=self.start_scraping, style='Accent.TButton')
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(button_frame, text="⏹ Stop", 
                                   command=self.stop_scraping, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = ttk.Button(button_frame, text="🗑 Clear Log", command=self.clear_log)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        validate_btn = ttk.Button(button_frame, text="✓ Validate Data", command=self.validate_data)
        validate_btn.pack(side=tk.LEFT, padx=5)
        
        export_btn = ttk.Button(button_frame, text="💾 Export CSV", command=self.export_csv)
        export_btn.pack(side=tk.RIGHT, padx=5)
        
        # ========== PROGRESS ==========
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                            maximum=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=(0, 10))
        
        self.status_label = ttk.Label(progress_frame, text="Ready", width=20)
        self.status_label.pack(side=tk.RIGHT)
        
        # ========== LOG OUTPUT ==========
        log_frame = ttk.LabelFrame(main_frame, text="📋 Log Output", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, 
                                                   font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # ========== RESULTS PREVIEW ==========
        results_frame = ttk.LabelFrame(main_frame, text="📊 Results Preview", padding="5")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Treeview for results
        columns = ('username', 'from', 'date', 'rating', 'review')
        self.tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=8)
        
        self.tree.heading('username', text='Username')
        self.tree.heading('from', text='Location')
        self.tree.heading('date', text='Date')
        self.tree.heading('rating', text='Rating')
        self.tree.heading('review', text='Review')
        
        self.tree.column('username', width=100)
        self.tree.column('from', width=100)
        self.tree.column('date', width=100)
        self.tree.column('rating', width=50)
        self.tree.column('review', width=400)
        
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ========== FOOTER ==========
        footer_frame = ttk.Frame(main_frame)
        footer_frame.pack(pady=5)
        
        footer = ttk.Label(footer_frame, 
                          text="© 2026 Web Scraper Tool | Created by Muhammad Ridho Bareng",
                          font=('Segoe UI', 8))
        footer.pack()
        
        github_link = ttk.Label(footer_frame, 
                                text="GitHub: github.com/MuhRidhoBareng",
                                font=('Segoe UI', 8), foreground='blue', cursor='hand2')
        github_link.pack()
        github_link.bind('<Button-1>', lambda e: self.open_github())
        
    def apply_theme(self):
        """Apply custom styling"""
        style = ttk.Style()
        
        # Use 'winnative' or 'vista' theme on Windows for proper checkmarks
        # These themes show ✓ instead of x
        available_themes = style.theme_names()
        if 'vista' in available_themes:
            style.theme_use('vista')
        elif 'winnative' in available_themes:
            style.theme_use('winnative')
        else:
            style.theme_use('default')
        
        # Custom button style
        style.configure('Accent.TButton', font=('Segoe UI', 10, 'bold'))
    
    def open_github(self):
        """Open GitHub profile in browser"""
        import webbrowser
        webbrowser.open('https://github.com/MuhRidhoBareng')
        
    def browse_folder(self):
        """Open folder browser dialog"""
        folder = filedialog.askdirectory(title="Select folder containing HTML files")
        if folder:
            self.folder_path.set(folder)
            self.log(f"Selected folder: {folder}")
            self.count_html_files(folder)
    
    def browse_files(self):
        """Open file browser dialog for selecting HTML files directly"""
        files = filedialog.askopenfilenames(
            title="Select HTML files",
            filetypes=[("HTML files", "*.html *.htm"), ("All files", "*.*")]
        )
        if files:
            # Store files as comma-separated list
            self.selected_files = list(files)
            if len(files) == 1:
                folder = os.path.dirname(files[0])
                self.folder_path.set(folder)
            else:
                self.folder_path.set(f"{len(files)} files selected")
            
            self.file_count_label.config(text=f"✓ {len(files)} HTML files selected")
            self.log(f"Selected {len(files)} HTML files directly")
            for f in files[:3]:
                self.log(f"  - {os.path.basename(f)}")
            if len(files) > 3:
                self.log(f"  ... and {len(files) - 3} more")
    
    def count_html_files(self, folder):
        """Count HTML files in folder and update label"""
        if self.recursive_var.get():
            # Search recursively
            pattern = os.path.join(folder, "**", "*.html")
            files = glob.glob(pattern, recursive=True)
        else:
            pattern = os.path.join(folder, "*.html")
            files = glob.glob(pattern)
        
        self.file_count_label.config(text=f"Found {len(files)} HTML files")
        self.log(f"Found {len(files)} HTML files")
    
    def log(self, message: str):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        """Clear log text"""
        self.log_text.delete(1.0, tk.END)
        
    def update_status(self, text: str):
        """Update status label"""
        self.status_label.config(text=text)
        self.root.update_idletasks()
    
    def update_progress(self, value: float):
        """Update progress bar"""
        self.progress_var.set(value)
        self.root.update_idletasks()
    
    def start_scraping(self):
        """Start the scraping process in a thread"""
        folder = self.folder_path.get()
        
        # Check if we have direct file selection or folder
        has_direct_files = hasattr(self, 'selected_files') and self.selected_files
        has_valid_folder = folder and os.path.isdir(folder)
        
        if not has_direct_files and not has_valid_folder:
            messagebox.showerror("Error", "Please select a folder or HTML files")
            return
        
        self.is_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.reviews = []
        
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Start in thread
        thread = threading.Thread(target=self.scrape_worker, daemon=True)
        thread.start()
    
    def stop_scraping(self):
        """Stop the scraping process"""
        self.is_running = False
        self.log("Stopping...")
        self.update_status("Stopped")
    
    def scrape_worker(self):
        """Worker thread for scraping"""
        try:
            folder = self.folder_path.get()
            preset = self.preset_var.get()
            config = ScraperConfig.PRESETS.get(preset, ScraperConfig.PRESETS['Yelp'])
            
            self.log(f"Starting scrape with {preset} preset...")
            self.update_status("Scanning...")
            
            # Check for direct file selection first
            if hasattr(self, 'selected_files') and self.selected_files:
                files = sorted(self.selected_files)
                self.log(f"Using {len(files)} directly selected files")
            else:
                # Search in folder (recursively if option enabled)
                if self.recursive_var.get():
                    pattern = os.path.join(folder, "**", "*.html")
                    files = sorted(glob.glob(pattern, recursive=True))
                else:
                    pattern = os.path.join(folder, "*.html")
                    files = sorted(glob.glob(pattern))
            
            if not files:
                self.log("No HTML files found!")
                self.log("Tip: Try selecting files directly with the 'Files' button")
                self.update_status("No files")
                return
            
            self.log(f"Processing {len(files)} files...")
            
            total_files = len(files)
            for i, filepath in enumerate(files):
                if not self.is_running:
                    break
                    
                progress = ((i + 1) / total_files) * 100
                self.update_progress(progress)
                self.update_status(f"File {i+1}/{total_files}")
                
                filename = os.path.basename(filepath)
                self.log(f"Parsing: {filename[:50]}...")
                
                reviews = self.parse_file(filepath, config)
                
                for r in reviews:
                    if not self.is_running:
                        break
                    self.reviews.append(r)
                    self.add_to_tree(r)
                
                self.log(f"  Found {len(reviews)} reviews")
            
            # Apply year filter
            if self.year_filter_enabled.get():
                try:
                    start = int(self.year_start.get())
                    end = int(self.year_end.get())
                    self.reviews = self.filter_by_year(self.reviews, start, end)
                    self.log(f"After year filter ({start}-{end}): {len(self.reviews)} reviews")
                except ValueError:
                    pass
            
            # Deduplicate
            self.reviews = self.deduplicate(self.reviews)
            
            self.log(f"\n{'='*40}")
            self.log(f"COMPLETE! Total: {len(self.reviews)} unique reviews")
            self.update_status(f"Done: {len(self.reviews)}")
            
        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            self.update_status("Error")
        finally:
            self.is_running = False
            self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))
    
    def parse_file(self, filepath: str, config: dict) -> list:
        """Parse single HTML file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(filepath, 'r', encoding='latin-1') as f:
                content = f.read()
        
        soup = BeautifulSoup(content, 'lxml')
        reviews = []
        
        # Find review elements
        search_kwargs = {'name': config['review_tag']}
        if config['review_class']:
            search_kwargs['class_'] = re.compile(config['review_class'])
        if config['review_lang']:
            search_kwargs['lang'] = config['review_lang']
        
        elements = soup.find_all(**search_kwargs)
        
        for elem in elements:
            review = self.extract_review(elem, config)
            if review and review.get('username'):
                reviews.append(review)
        
        return reviews
    
    def extract_review(self, elem, config: dict) -> dict:
        """Extract review data from element"""
        review = {
            'username': '',
            'from': '',
            'written_date': '',
            'rating': '',
            'title': '',
            'review_text': '',
            'tema_pengalaman': '',
            'daya_tarik_wisata': '',
            'status': '',
            'contribution': ''
        }
        
        # Get review text
        text = elem.get_text(strip=True)
        if len(text) < 50:
            return None
        review['review_text'] = text
        
        # Find container
        container = elem
        for _ in range(config['container_levels']):
            parent = container.parent
            if parent is None:
                break
            if parent.name == config['container_tag']:
                container = parent
                break
            container = parent
        
        container_text = container.get_text(' ', strip=True)
        
        # Extract username
        if config['username_pattern']:
            links = container.find_all(config['username_tag'], 
                                       attrs={config['username_attr']: re.compile(config['username_pattern'])})
            for link in links:
                name = link.get_text(strip=True)
                if name and len(name) >= 2 and re.match(r'^[A-Za-z]', name):
                    review['username'] = name
                    break
        
        if not review['username']:
            return None
        
        # Extract location
        if config['location_pattern']:
            match = re.search(config['location_pattern'], container_text)
            if match:
                review['from'] = match.group(1) if match.lastindex else match.group()
        
        # Extract date
        if config['date_pattern']:
            match = re.search(config['date_pattern'], container_text)
            if match:
                review['written_date'] = match.group()
        
        # Extract rating
        if config['rating_pattern']:
            rating_elem = container.find(attrs={'aria-label': re.compile(config['rating_pattern'], re.I)})
            if rating_elem:
                match = re.search(r'(\d+)', rating_elem.get('aria-label', ''))
                if match:
                    review['rating'] = match.group(1)
        
        # Extract helpful
        if config['helpful_pattern']:
            match = re.search(config['helpful_pattern'], container_text)
            if match:
                review['daya_tarik_wisata'] = match.group(1)
        
        # Extract contribution
        if config['contribution_pattern']:
            match = re.search(config['contribution_pattern'], container_text)
            if match:
                if match.lastindex and match.lastindex >= 2:
                    review['contribution'] = f"{match.group(1)} reviews, {match.group(2)} photos"
                else:
                    review['contribution'] = match.group(1)
        
        # Extract elite/status
        if config['elite_pattern'] and config['elite_tag']:
            elite_elem = container.find(config['elite_tag'], 
                                        attrs={config['elite_attr']: config['elite_pattern']})
            if elite_elem:
                review['status'] = elite_elem.get_text(strip=True)
                review['tema_pengalaman'] = review['status']
        
        return review
    
    def filter_by_year(self, reviews: list, start: int, end: int) -> list:
        """Filter reviews by year range"""
        filtered = []
        for r in reviews:
            date_str = r.get('written_date', '')
            match = re.search(r'(\d{4})', date_str)
            if match:
                year = int(match.group(1))
                if start <= year <= end:
                    filtered.append(r)
        return filtered
    
    def deduplicate(self, reviews: list) -> list:
        """Remove duplicate reviews"""
        seen = set()
        unique = []
        for r in reviews:
            key = (r.get('username', ''), r.get('review_text', '')[:100])
            if key not in seen and r.get('username'):
                seen.add(key)
                unique.append(r)
        return unique
    
    def add_to_tree(self, review: dict):
        """Add review to treeview"""
        text_preview = review.get('review_text', '')[:50] + '...'
        self.tree.insert('', tk.END, values=(
            review.get('username', ''),
            review.get('from', ''),
            review.get('written_date', ''),
            review.get('rating', ''),
            text_preview
        ))
    
    def export_csv(self):
        """Export reviews to CSV"""
        if not self.reviews:
            messagebox.showwarning("Warning", "No reviews to export!")
            return
        
        # Ask for save location
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=self.output_file.get()
        )
        
        if not filename:
            return
        
        try:
            columns = ['username', 'from', 'written_date', 'rating', 'title',
                      'review_text', 'tema_pengalaman', 'daya_tarik_wisata',
                      'status', 'contribution']
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()
                writer.writerows(self.reviews)
            
            self.log(f"Exported {len(self.reviews)} reviews to {filename}")
            messagebox.showinfo("Success", f"Exported {len(self.reviews)} reviews!")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")
    
    def validate_data(self):
        """Validate scraped data and show report"""
        if not self.reviews:
            messagebox.showwarning("Warning", "No data to validate! Run scraping first.")
            return
        
        self.log("\n" + "=" * 50)
        self.log("DATA VALIDATION REPORT")
        self.log("=" * 50)
        
        total = len(self.reviews)
        self.log(f"\nTotal Reviews: {total}")
        
        # Track issues
        issues = []
        warnings = []
        
        # 1. Check for empty fields
        empty_counts = {
            'username': 0,
            'from': 0,
            'written_date': 0,
            'rating': 0,
            'review_text': 0
        }
        
        for r in self.reviews:
            for field in empty_counts:
                if not r.get(field, '').strip():
                    empty_counts[field] += 1
        
        self.log("\n--- Empty Fields Check ---")
        for field, count in empty_counts.items():
            pct = (count / total) * 100
            status = "✓" if count == 0 else "⚠" if pct < 20 else "✗"
            self.log(f"  {status} {field}: {count} empty ({pct:.1f}%)")
            if count > 0 and field in ['username', 'review_text']:
                issues.append(f"{field} has {count} empty values")
            elif count > 0:
                warnings.append(f"{field} has {count} empty values")
        
        # 2. Check rating validity
        self.log("\n--- Rating Validation ---")
        valid_ratings = 0
        invalid_ratings = 0
        rating_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
        for r in self.reviews:
            rating = r.get('rating', '')
            if rating:
                try:
                    rating_int = int(rating)
                    if 1 <= rating_int <= 5:
                        valid_ratings += 1
                        rating_dist[rating_int] += 1
                    else:
                        invalid_ratings += 1
                except ValueError:
                    invalid_ratings += 1
        
        self.log(f"  ✓ Valid ratings (1-5): {valid_ratings}")
        if invalid_ratings > 0:
            self.log(f"  ✗ Invalid ratings: {invalid_ratings}")
            issues.append(f"{invalid_ratings} invalid ratings")
        
        self.log("  Rating distribution:")
        for star, count in rating_dist.items():
            bar = "█" * int(count / max(1, total) * 20)
            self.log(f"    {star}★: {count} {bar}")
        
        # 3. Check date validity
        self.log("\n--- Date Validation ---")
        valid_dates = 0
        invalid_dates = 0
        year_dist = {}
        
        date_pattern = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+(\d{4})'
        
        for r in self.reviews:
            date_str = r.get('written_date', '')
            if date_str:
                match = re.search(date_pattern, date_str)
                if match:
                    valid_dates += 1
                    year = match.group(2)
                    year_dist[year] = year_dist.get(year, 0) + 1
                else:
                    invalid_dates += 1
        
        self.log(f"  ✓ Valid dates: {valid_dates}")
        if invalid_dates > 0:
            self.log(f"  ⚠ Invalid/missing dates: {invalid_dates}")
            warnings.append(f"{invalid_dates} invalid dates")
        
        self.log("  Year distribution:")
        for year in sorted(year_dist.keys()):
            count = year_dist[year]
            bar = "█" * int(count / max(1, total) * 20)
            self.log(f"    {year}: {count} {bar}")
        
        # 4. Check review text length
        self.log("\n--- Review Text Analysis ---")
        text_lengths = [len(r.get('review_text', '')) for r in self.reviews]
        if text_lengths:
            avg_len = sum(text_lengths) / len(text_lengths)
            min_len = min(text_lengths)
            max_len = max(text_lengths)
            short_reviews = sum(1 for l in text_lengths if l < 50)
            
            self.log(f"  Average length: {avg_len:.0f} chars")
            self.log(f"  Min length: {min_len} chars")
            self.log(f"  Max length: {max_len} chars")
            if short_reviews > 0:
                self.log(f"  ⚠ Short reviews (<50 chars): {short_reviews}")
                warnings.append(f"{short_reviews} very short reviews")
        
        # 5. Check for duplicates
        self.log("\n--- Duplicate Check ---")
        seen_reviews = set()
        duplicates = 0
        for r in self.reviews:
            key = (r.get('username', ''), r.get('review_text', '')[:100])
            if key in seen_reviews:
                duplicates += 1
            seen_reviews.add(key)
        
        if duplicates == 0:
            self.log(f"  ✓ No duplicates found")
        else:
            self.log(f"  ⚠ Potential duplicates: {duplicates}")
            warnings.append(f"{duplicates} potential duplicates")
        
        # Summary
        self.log("\n" + "=" * 50)
        self.log("VALIDATION SUMMARY")
        self.log("=" * 50)
        
        if not issues and not warnings:
            self.log("✓ All checks passed! Data looks valid.")
            score = 100
        else:
            if issues:
                self.log(f"\n✗ Issues ({len(issues)}):")
                for issue in issues:
                    self.log(f"   - {issue}")
            if warnings:
                self.log(f"\n⚠ Warnings ({len(warnings)}):")
                for warning in warnings:
                    self.log(f"   - {warning}")
            
            # Calculate score
            score = max(0, 100 - (len(issues) * 20) - (len(warnings) * 5))
        
        self.log(f"\nData Quality Score: {score}/100")
        
        if score >= 80:
            self.log("→ Data quality: GOOD")
        elif score >= 50:
            self.log("→ Data quality: ACCEPTABLE")
        else:
            self.log("→ Data quality: NEEDS REVIEW")
        
        self.log("=" * 50)
        
        # Show summary popup
        messagebox.showinfo(
            "Validation Complete",
            f"Data Quality Score: {score}/100\n\n"
            f"Total Reviews: {total}\n"
            f"Issues: {len(issues)}\n"
            f"Warnings: {len(warnings)}\n\n"
            f"See log for details."
        )


def main():
    root = tk.Tk()
    app = ScraperApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
