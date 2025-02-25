import requests
from bs4 import BeautifulSoup
import os
import urllib.parse
import time
import re
import json
from urllib.parse import urlparse
import argparse

class FlexiblePDFScraper:
    def __init__(self, config=None):
        """
        Initialize the PDF scraper with a config
        
        Args:
            config (dict): Scraper configuration
        """
        self.config = config or {}
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Set default values if not provided
        self.base_url = self.config.get('base_url', '')
        self.download_folder = self.config.get('download_folder', 'downloaded_pdfs')
        
        # Create download folder
        if not os.path.exists(self.download_folder):
            os.makedirs(self.download_folder)
    
    def extract_domain(self, url):
        """Extract domain name from URL for naming"""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        # Remove www. if present
        domain = re.sub(r'^www\.', '', domain)
        # Remove .rs, .gov, etc.
        domain = re.sub(r'\.[a-z]+$', '', domain)
        return domain
    
    def save_config(self, filename=None):
        """Save the current configuration to a file"""
        if not filename:
            domain = self.extract_domain(self.base_url)
            filename = f"config_{domain}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)
        
        print(f"Configuration saved to {filename}")
    
    def load_config(self, filename):
        """Load configuration from a file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
                self.base_url = self.config.get('base_url', '')
                self.download_folder = self.config.get('download_folder', 'downloaded_pdfs')
            print(f"Configuration loaded from {filename}")
            return True
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return False
    
    def download_file(self, url, folder, filename=None):
        """Download a file from URL to the specified folder"""
        try:
            response = requests.get(url, headers=self.headers, stream=True)
            response.raise_for_status()
            
            # Generate filename if not provided
            if not filename:
                # Try to get from Content-Disposition header
                if "Content-Disposition" in response.headers:
                    content_disposition = response.headers["Content-Disposition"]
                    filename_match = re.search(r'filename="?([^"]+)"?', content_disposition)
                    if filename_match:
                        filename = filename_match.group(1)
                
                # If still not found, extract from URL
                if not filename:
                    filename = os.path.basename(urllib.parse.urlparse(url).path)
                
                # Clean up filename
                filename = filename.replace('%20', ' ')
                # Remove invalid characters
                filename = re.sub(r'[\\/*?:"<>|]', '_', filename)
                # Add .pdf extension if not present and it's a PDF
                content_type = response.headers.get('Content-Type', '').lower()
                if 'application/pdf' in content_type and not filename.lower().endswith('.pdf'):
                    filename += '.pdf'
            
            # Ensure the filename is valid and unique
            if not filename or filename == '':
                timestamp = int(time.time())
                filename = f"document_{timestamp}.pdf"
            
            # Save the file
            filepath = os.path.join(folder, filename)
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Downloaded: {filename}")
            return True
        except Exception as e:
            print(f"Failed to download {url}: {e}")
            return False
    
    def is_pdf_link(self, url, text=None):
        """Check if a URL likely points to a PDF"""
        # Check URL extension
        if url.lower().endswith('.pdf'):
            return True
        
        # Check URL contains pdf
        if 'pdf' in url.lower():
            return True
        
        # Check if link text suggests it's a PDF
        if text and ('pdf' in text.lower() or text.lower().endswith('.pdf')):
            return True
        
        # TODO: Could add more sophisticated checks here
        
        return False
    
    def interactive_setup(self):
        """Set up scraper configuration interactively"""
        print("\n--- Interactive PDF Scraper Setup ---")
        
        # Base URL
        self.base_url = input("Enter the base URL to scrape: ").strip()
        if not self.base_url:
            print("Error: Base URL is required")
            return False
        
        # Create default download folder based on domain
        domain = self.extract_domain(self.base_url)
        default_folder = f"{domain}_pdfs"
        
        # Download folder
        folder_input = input(f"Enter download folder name (press Enter for '{default_folder}'): ").strip()
        self.download_folder = folder_input if folder_input else default_folder
        
        # Create the folder
        if not os.path.exists(self.download_folder):
            os.makedirs(self.download_folder)
        
        # Scraping mode
        print("\nSelect scraping mode:")
        print("1. Simple mode - Download PDFs directly from the specified URL")
        print("2. Navigation mode - Navigate through links to find PDFs")
        
        mode = input("Enter your choice (1 or 2): ").strip()
        
        self.config = {
            'base_url': self.base_url,
            'download_folder': self.download_folder
        }
        
        if mode == '2':
            self.config['navigation_mode'] = True
            
            # Configure navigation depth
            depth_input = input("Enter maximum navigation depth (1-5, default is 2): ").strip()
            self.config['max_depth'] = int(depth_input) if depth_input.isdigit() and 1 <= int(depth_input) <= 5 else 2
            
            # Configure link patterns to follow
            follow_pattern = input("Enter regex pattern for links to follow (leave empty to follow all): ").strip()
            if follow_pattern:
                self.config['follow_pattern'] = follow_pattern
            
            # Configure link patterns to ignore
            ignore_pattern = input("Enter regex pattern for links to ignore (leave empty for none): ").strip()
            if ignore_pattern:
                self.config['ignore_pattern'] = ignore_pattern
        else:
            self.config['navigation_mode'] = False
        
        # Save config
        save_config = input("Save this configuration for future use? (y/n): ").strip().lower()
        if save_config == 'y':
            self.save_config()
        
        return True
    
    def scrape_single_page(self, url, folder=None):
        """Scrape a single page for PDF links"""
        if folder is None:
            folder = self.download_folder
        
        if not os.path.exists(folder):
            os.makedirs(folder)
        
        print(f"Scraping {url} for PDFs...")
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all links
            links = soup.find_all('a')
            
            pdf_count = 0
            for link in links:
                href = link.get('href')
                if not href:
                    continue
                
                # Convert to absolute URL if needed
                full_url = urllib.parse.urljoin(url, href)
                
                # Check if it's a PDF link
                if self.is_pdf_link(full_url, link.text):
                    # Get text for filename
                    link_text = link.text.strip()
                    filename = None
                    if link_text:
                        # Clean up the text for filename
                        filename = re.sub(r'[\\/*?:"<>|]', '_', link_text)
                        if not filename.lower().endswith('.pdf'):
                            filename += '.pdf'
                    
                    # Download the PDF
                    success = self.download_file(full_url, folder, filename)
                    if success:
                        pdf_count += 1
                    
                    # Add a small delay
                    time.sleep(0.5)
            
            print(f"Found {pdf_count} PDFs on this page")
            return pdf_count
        
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return 0
    
    def should_follow_link(self, url, link_text):
        """Determine if a link should be followed based on configuration"""
        # Skip if it's a PDF link
        if self.is_pdf_link(url, link_text):
            return False
        
        # Skip common non-content links
        skip_patterns = [
            r'mailto:', r'tel:', r'javascript:', r'#',
            r'/login', r'/logout', r'/register', r'/search',
            r'facebook.com', r'twitter.com', r'youtube.com', r'instagram.com'
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        # Check custom follow pattern if configured
        if 'follow_pattern' in self.config and self.config['follow_pattern']:
            if not re.search(self.config['follow_pattern'], url, re.IGNORECASE) and \
               not re.search(self.config['follow_pattern'], link_text, re.IGNORECASE):
                return False
        
        # Check custom ignore pattern if configured
        if 'ignore_pattern' in self.config and self.config['ignore_pattern']:
            if re.search(self.config['ignore_pattern'], url, re.IGNORECASE) or \
               re.search(self.config['ignore_pattern'], link_text, re.IGNORECASE):
                return False
        
        # Ensure we stay on the same domain
        base_domain = urlparse(self.base_url).netloc
        link_domain = urlparse(url).netloc
        
        if link_domain and link_domain != base_domain:
            return False
        
        return True
    
    def scrape_with_navigation(self, start_url=None, max_depth=None, visited=None, current_depth=0):
        """Scrape PDFs with navigation through links"""
        if start_url is None:
            start_url = self.base_url
        
        if max_depth is None:
            max_depth = self.config.get('max_depth', 2)
        
        if visited is None:
            visited = set()
        
        if current_depth > max_depth:
            return 0
        
        if start_url in visited:
            return 0
        
        visited.add(start_url)
        
        print(f"{'  ' * current_depth}Navigating to: {start_url} (Depth: {current_depth}/{max_depth})")
        
        try:
            # Create a subfolder for this page if needed
            if current_depth > 0:
                path_parts = urlparse(start_url).path.strip('/').split('/')
                if path_parts and path_parts[-1]:
                    subfolder_name = re.sub(r'[\\/*?:"<>|]', '_', path_parts[-1])
                    subfolder = os.path.join(self.download_folder, subfolder_name)
                else:
                    timestamp = int(time.time())
                    subfolder = os.path.join(self.download_folder, f"page_{timestamp}")
            else:
                subfolder = self.download_folder
            
            if not os.path.exists(subfolder):
                os.makedirs(subfolder)
            
            # First, download PDFs from this page
            pdf_count = self.scrape_single_page(start_url, subfolder)
            
            # If at max depth, don't go further
            if current_depth >= max_depth:
                return pdf_count
            
            # Then, find links to follow
            response = requests.get(start_url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            links = soup.find_all('a')
            
            for link in links:
                href = link.get('href')
                if not href:
                    continue
                
                # Convert to absolute URL
                full_url = urllib.parse.urljoin(start_url, href)
                
                # Check if we should follow this link
                if self.should_follow_link(full_url, link.text):
                    # Recursively scrape the linked page
                    pdf_count += self.scrape_with_navigation(
                        full_url, max_depth, visited, current_depth + 1
                    )
            
            return pdf_count
        
        except Exception as e:
            print(f"{'  ' * current_depth}Error navigating {start_url}: {e}")
            return 0
    
    def start_scraping(self):
        """Start the scraping process based on configuration"""
        print(f"\nStarting PDF scraper for: {self.base_url}")
        print(f"Files will be saved to: {os.path.abspath(self.download_folder)}")
        
        start_time = time.time()
        
        if self.config.get('navigation_mode', False):
            print("Using navigation mode...")
            total_pdfs = self.scrape_with_navigation()
        else:
            print("Using simple mode...")
            total_pdfs = self.scrape_single_page(self.base_url)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\nScraping complete!")
        print(f"Total PDFs downloaded: {total_pdfs}")
        print(f"Time taken: {duration:.2f} seconds")

def list_saved_configs():
    """List all saved configurations in the current directory"""
    configs = [f for f in os.listdir('.') if f.startswith('config_') and f.endswith('.json')]
    
    if not configs:
        print("No saved configurations found.")
        return []
    
    print("\nSaved configurations:")
    for i, config_file in enumerate(configs, 1):
        # Extract domain name from filename
        domain = config_file[7:-5]  # Remove 'config_' prefix and '.json' suffix
        print(f"{i}. {domain}")
    
    return configs

def main():
    parser = argparse.ArgumentParser(description='Flexible PDF Scraper')
    parser.add_argument('--url', help='URL to scrape for PDFs')
    parser.add_argument('--config', help='Path to configuration file')
    args = parser.parse_args()
    
    scraper = FlexiblePDFScraper()
    
    if args.config:
        # Load configuration from file
        if scraper.load_config(args.config):
            scraper.start_scraping()
        else:
            print("Failed to load configuration. Exiting.")
    elif args.url:
        # Quick scrape with just a URL
        scraper.config = {
            'base_url': args.url,
            'download_folder': scraper.extract_domain(args.url) + '_pdfs',
            'navigation_mode': False
        }
        scraper.base_url = args.url
        scraper.download_folder = scraper.config['download_folder']
        scraper.start_scraping()
    else:
        # Interactive mode
        print("=== Flexible PDF Scraper ===")
        print("1. Set up new scraper configuration")
        print("2. Use saved configuration")
        print("3. Quick scrape (URL only)")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            if scraper.interactive_setup():
                scraper.start_scraping()
        
        elif choice == '2':
            configs = list_saved_configs()
            if configs:
                config_choice = input("\nEnter the number of the configuration to use: ").strip()
                if config_choice.isdigit() and 1 <= int(config_choice) <= len(configs):
                    config_file = configs[int(config_choice) - 1]
                    if scraper.load_config(config_file):
                        scraper.start_scraping()
                else:
                    print("Invalid choice.")
        
        elif choice == '3':
            url = input("\nEnter URL to scrape: ").strip()
            if url:
                scraper.config = {
                    'base_url': url,
                    'download_folder': scraper.extract_domain(url) + '_pdfs',
                    'navigation_mode': False
                }
                scraper.base_url = url
                scraper.download_folder = scraper.config['download_folder']
                scraper.start_scraping()
            else:
                print("URL is required for quick scrape.")
        
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()