#!/usr/bin/env python3
"""
FS25 Documentation Scraper
Scrapes the GIANTS Developer Network documentation for Farming Simulator 25
and saves it in an organized, offline-readable format.
"""

import requests
from bs4 import BeautifulSoup
import time
import os
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs
import re
import html2text
import json
from datetime import datetime


class FS25DocScraper:
    def __init__(self, base_url="https://gdn.giants-software.com/documentation_scripting_fs25.php", output_dir="output"):
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.body_width = 0  # Don't wrap text
        self.manifest = {
            'metadata': {
                'generated_at': None,
                'source_url': self.base_url,
                'total_files': 0
            },
            'versions': {}
        }
        
    def get_page(self, url, params=None):
        """Fetch a page with error handling and rate limiting"""
        try:
            time.sleep(0.5)  # Rate limiting
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def parse_main_page(self):
        """Parse the main documentation page to get all categories"""
        print("Fetching main documentation page...")
        html = self.get_page(self.base_url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        categories = []
        
        # Find all category links in the sidebar
        sidebar = soup.find('div', style=lambda x: x and 'width:200px' in x and 'float:left' in x)
        if not sidebar:
            print("Could not find sidebar")
            return []
        
        # Process Script categories
        script_section = sidebar.find('h3', class_='version', string=lambda x: x and 'Script' in x)
        if script_section:
            script_ul = script_section.find_next('ul')
            if script_ul:
                for link in script_ul.find_all('a', href=True):
                    href = link['href']
                    if 'version=script' in href and 'category=' in href:
                        parsed = parse_qs(urlparse(href).query)
                        if 'category' in parsed and 'class' in parsed:
                            categories.append({
                                'version': 'script',
                                'category': parsed['category'][0],
                                'class': parsed['class'][0],
                                'name': link.text.strip()
                            })
        
        # Process Engine categories
        engine_section = sidebar.find('h3', class_='version', string=lambda x: x and 'Engine' in x)
        if engine_section:
            engine_ul = engine_section.find_next('ul')
            if engine_ul:
                for link in engine_ul.find_all('a', href=True):
                    href = link['href']
                    if 'version=engine' in href and 'category=' in href:
                        parsed = parse_qs(urlparse(href).query)
                        if 'category' in parsed and 'function' in parsed:
                            categories.append({
                                'version': 'engine',
                                'category': parsed['category'][0],
                                'function': parsed['function'][0],
                                'name': link.text.strip()
                            })
        
        print(f"Found {len(categories)} categories")
        return categories
    
    def get_subcategories(self, category_info):
        """Get all classes/functions within a category"""
        print(f"Fetching subcategories for {category_info['name']}...")
        
        params = {
            'version': category_info['version'],
            'category': category_info['category']
        }
        
        if category_info['version'] == 'script':
            params['class'] = category_info['class']
        else:
            params['function'] = category_info['function']
        
        html = self.get_page(self.base_url, params=params)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        subcategories = []
        
        # Find the expanded category in sidebar
        sidebar = soup.find('div', style=lambda x: x and 'width:200px' in x and 'float:left' in x)
        if not sidebar:
            return []
        
        # Find the selected category's subcategories
        selected_li = sidebar.find('li', class_='selected')
        if selected_li:
            # Check if there's a nested ul with subcategories
            nested_ul = selected_li.find('ul')
            if nested_ul:
                for link in nested_ul.find_all('a', href=True):
                    href = link['href']
                    parsed = parse_qs(urlparse(href).query)
                    
                    sub_info = {
                        'version': category_info['version'],
                        'category': category_info['category'],
                        'name': link.text.strip(),
                        'category_name': category_info['name']
                    }
                    
                    if category_info['version'] == 'script' and 'class' in parsed:
                        sub_info['class'] = parsed['class'][0]
                        subcategories.append(sub_info)
                    elif category_info['version'] == 'engine' and 'function' in parsed:
                        sub_info['function'] = parsed['function'][0]
                        subcategories.append(sub_info)
        
        # If no subcategories found, the category itself is the content
        if not subcategories:
            subcategories.append(category_info)
        
        return subcategories
    
    def extract_content(self, soup):
        """Extract the main documentation content"""
        # Find the content div: #box5 > div.entry > div:nth-child(2)
        box5 = soup.find('div', id='box5')
        if not box5:
            return None
        
        entry = box5.find('div', class_='entry')
        if not entry:
            return None
        
        # Get the second div child (the content area, not the sidebar)
        content_divs = entry.find_all('div', recursive=False)
        if len(content_divs) < 2:
            return None
        
        content_div = content_divs[1]
        return content_div
    
    def html_to_markdown(self, html_content):
        """Convert HTML content to clean markdown"""
        if not html_content:
            return ""
        
        # Convert to string if it's a BeautifulSoup element
        html_str = str(html_content)
        
        # Use html2text for conversion
        markdown = self.h2t.handle(html_str)
        
        # Clean up the markdown
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)  # Remove excessive newlines
        
        return markdown.strip()
    
    def save_content(self, content, category_info):
        """Save content to a markdown file and update manifest"""
        version = category_info['version']
        category_name = category_info.get('category_name', category_info['name'])
        item_name = category_info['name']
        
        # Create safe filenames
        safe_category = re.sub(r'[^\w\s-]', '', category_name).strip().replace(' ', '_')
        safe_item = re.sub(r'[^\w\s-]', '', item_name).strip().replace(' ', '_')
        
        # Create directory structure
        output_path = self.output_dir / version / safe_category
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = output_path / f"{safe_item}.md"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# {item_name}\n\n")
            f.write(f"**Category:** {category_name}\n")
            f.write(f"**Version:** {version}\n\n")
            f.write("---\n\n")
            f.write(content)
        
        # Update manifest
        self._add_to_manifest(version, category_name, item_name, file_path)
        
        return file_path
    
    def _add_to_manifest(self, version, category_name, item_name, file_path):
        """Add an entry to the manifest"""
        # Initialize version if not exists
        if version not in self.manifest['versions']:
            self.manifest['versions'][version] = {
                'categories': {}
            }
        
        # Initialize category if not exists
        if category_name not in self.manifest['versions'][version]['categories']:
            self.manifest['versions'][version]['categories'][category_name] = {
                'items': []
            }
        
        # Calculate relative path from output directory
        relative_path = file_path.relative_to(self.output_dir).as_posix()
        
        # Add item
        self.manifest['versions'][version]['categories'][category_name]['items'].append({
            'name': item_name,
            'path': relative_path
        })
        
        # Update total count
        self.manifest['metadata']['total_files'] += 1
    
    def save_manifest(self):
        """Save the manifest file"""
        # Update generation timestamp
        self.manifest['metadata']['generated_at'] = datetime.now().isoformat()
        
        # Save JSON manifest
        manifest_path = self.output_dir / 'manifest.json'
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(self.manifest, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Manifest saved: {manifest_path}")
        
        # Also create a human-readable markdown index
        self._create_markdown_index()
    
    def _create_markdown_index(self):
        """Create a human-readable markdown index"""
        index_path = self.output_dir / 'INDEX.md'
        
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write("# FS25 Documentation Index\n\n")
            f.write(f"**Generated:** {self.manifest['metadata']['generated_at']}\n")
            f.write(f"**Source:** {self.manifest['metadata']['source_url']}\n")
            f.write(f"**Total Files:** {self.manifest['metadata']['total_files']}\n\n")
            f.write("---\n\n")
            
            # Write table of contents
            f.write("## Table of Contents\n\n")
            for version in sorted(self.manifest['versions'].keys()):
                f.write(f"- [{version.upper()}](#{version})\n")
            f.write("\n---\n\n")
            
            # Write each version section
            for version in sorted(self.manifest['versions'].keys()):
                version_data = self.manifest['versions'][version]
                f.write(f"## {version.upper()}\n\n")
                
                # Sort categories alphabetically
                for category in sorted(version_data['categories'].keys()):
                    category_data = version_data['categories'][category]
                    item_count = len(category_data['items'])
                    
                    f.write(f"### {category} ({item_count} items)\n\n")
                    
                    # Sort items alphabetically
                    for item in sorted(category_data['items'], key=lambda x: x['name']):
                        f.write(f"- [{item['name']}]({item['path']})\n")
                    
                    f.write("\n")
                
                f.write("\n")
        
        print(f"✓ Index saved: {index_path}")
    
    def scrape_page(self, category_info):
        """Scrape a single documentation page"""
        params = {
            'version': category_info['version'],
            'category': category_info['category']
        }
        
        if category_info['version'] == 'script':
            params['class'] = category_info['class']
        else:
            params['function'] = category_info['function']
        
        # Check if already exists
        version = category_info['version']
        category_name = category_info.get('category_name', category_info['name'])
        item_name = category_info['name']
        safe_category = re.sub(r'[^\w\s-]', '', category_name).strip().replace(' ', '_')
        safe_item = re.sub(r'[^\w\s-]', '', item_name).strip().replace(' ', '_')
        file_path = self.output_dir / version / safe_category / f"{safe_item}.md"
        
        if file_path.exists():
            print(f"  ✓ Already exists: {item_name}")
            return True
        
        print(f"  Scraping: {item_name}...")
        
        html = self.get_page(self.base_url, params=params)
        if not html:
            return False
        
        soup = BeautifulSoup(html, 'html.parser')
        content_div = self.extract_content(soup)
        
        if not content_div:
            print(f"  ✗ No content found for {item_name}")
            return False
        
        markdown = self.html_to_markdown(content_div)
        saved_path = self.save_content(markdown, category_info)
        print(f"  ✓ Saved: {saved_path}")
        
        return True
    
    def scrape_all(self):
        """Main scraping function"""
        print("=" * 60)
        print("FS25 Documentation Scraper")
        print("=" * 60)
        
        # Get all main categories
        categories = self.parse_main_page()
        if not categories:
            print("Failed to parse main page")
            return
        
        total_scraped = 0
        total_failed = 0
        
        # Process each category
        for i, category in enumerate(categories, 1):
            print(f"\n[{i}/{len(categories)}] Processing: {category['name']}")
            
            # Get subcategories (classes/functions within this category)
            subcategories = self.get_subcategories(category)
            
            if not subcategories:
                print(f"  No subcategories found, scraping main page...")
                if self.scrape_page(category):
                    total_scraped += 1
                else:
                    total_failed += 1
                continue
            
            # Scrape each subcategory
            for sub in subcategories:
                if self.scrape_page(sub):
                    total_scraped += 1
                else:
                    total_failed += 1
        
        # Save manifest and index
        print("\nGenerating manifest and index files...")
        self.save_manifest()
        
        print("\n" + "=" * 60)
        print(f"Scraping complete!")
        print(f"  Successfully scraped: {total_scraped}")
        print(f"  Failed: {total_failed}")
        print(f"  Output directory: {self.output_dir.absolute()}")
        print("=" * 60)


def main():
    scraper = FS25DocScraper()
    scraper.scrape_all()


if __name__ == "__main__":
    main()
