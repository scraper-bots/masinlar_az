#!/usr/bin/env python3
"""
Masinlar.az Car Listings Scraper

This scraper extracts car listings from masinlar.az website including:
- Basic car information from listing pages
- Detailed information from individual car pages
- Phone numbers through AJAX calls
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import time
import re
from urllib.parse import urljoin, urlparse, parse_qs
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MasinlarScraper:
    def __init__(self):
        self.base_url = "https://masinlar.az"
        self.session = requests.Session()
        # Set headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8,ru;q=0.7,az;q=0.6',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
    def get_page(self, url):
        """Fetch a page with error handling"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def extract_listing_links(self, soup):
        """Extract car detail page links from listing page"""
        links = []
        # Find all product divs
        prod_divs = soup.find_all('div', class_='nobj prod prodbig')
        
        for div in prod_divs:
            link_tag = div.find('a', href=True)
            if link_tag:
                href = link_tag['href']
                # Convert relative URLs to absolute
                full_url = urljoin(self.base_url, href)
                links.append(full_url)
                
        return links
    
    def extract_basic_info(self, soup):
        """Extract basic car information from listing page"""
        cars = []
        prod_divs = soup.find_all('div', class_='nobj prod prodbig')
        
        for div in prod_divs:
            car_info = {}
            
            # Extract title and link
            title_link = div.find('div', class_='prodname').find('a')
            if title_link:
                car_info['title'] = title_link.get_text(strip=True)
                car_info['url'] = urljoin(self.base_url, title_link['href'])
            
            # Extract price
            price_span = div.find('span', class_='sprice')
            if price_span:
                car_info['price'] = price_span.get_text(strip=True)
            
            # Extract description
            desc_p = div.find('p', class_='prodful')
            if desc_p:
                car_info['description'] = desc_p.get_text(strip=True)
            
            # Extract image
            img_tag = div.find('img')
            if img_tag and img_tag.get('src'):
                car_info['image_url'] = urljoin(self.base_url, img_tag['src'])
            
            cars.append(car_info)
            
        return cars
    
    def extract_detailed_info(self, soup, url):
        """Extract detailed information from car detail page"""
        car_info = {}
        
        # Extract title
        title_h1 = soup.find('h1')
        if title_h1:
            car_info['title'] = title_h1.get_text(strip=True)
        
        # Extract listing ID
        id_span = soup.find('span', class_='open_idshow')
        if id_span:
            id_text = id_span.get_text(strip=True)
            # Extract ID number from "Elan kodu: 46348"
            id_match = re.search(r'(\d+)', id_text)
            if id_match:
                car_info['listing_id'] = id_match.group(1)
        
        # Extract all details from the info section
        info_div = soup.find('div', class_='halfdiv openproduct')
        if info_div:
            # Extract all paragraphs with bold labels
            for p in info_div.find_all('p'):
                bold_tag = p.find('b')
                if bold_tag:
                    label = bold_tag.get_text(strip=True)
                    # Get text after the bold tag
                    text_content = p.get_text(strip=True)
                    value = text_content.replace(label, '', 1).strip()
                    
                    # Clean up the value
                    if value:
                        car_info[self._clean_label(label)] = value
        
        # Extract description from fullteshow
        desc_p = soup.find('p', class_='infop100 fullteshow')
        if desc_p:
            car_info['full_description'] = desc_p.get_text(strip=True)
        
        # Extract contact information
        contact_div = soup.find('div', class_='infocontact')
        if contact_div:
            # Extract contact person
            contact_text = contact_div.get_text()
            lines = [line.strip() for line in contact_text.split('\n') if line.strip()]
            for line in lines:
                if not line.startswith('0') and len(line) > 2:  # Skip phone numbers
                    car_info['contact_person'] = line.replace('👤', '').strip()
                    break
            
            # Extract location
            location_match = re.search(r'📍\s*(.+?)(?:\n|$)', contact_text)
            if location_match:
                car_info['location'] = location_match.group(1).strip()
        
        # Extract phone data for AJAX call
        tel_div = soup.find('div', id='telshow')
        if tel_div:
            car_info['ajax_data'] = {
                'id': tel_div.get('data-id'),
                't': tel_div.get('data-t'),
                'h': tel_div.get('data-h'),
                'rf': tel_div.get('data-rf')
            }
        
        # Extract images
        images = []
        pic_area = soup.find('div', id='picappendarea')
        if pic_area:
            for img in pic_area.find_all('img'):
                if img.get('src'):
                    images.append(urljoin(self.base_url, img['src']))
        car_info['images'] = images
        
        # Extract date
        views_span = soup.find('span', class_='viewsbb clear')
        if views_span:
            date_text = views_span.get_text(strip=True)
            date_match = re.search(r'Tarix:\s*(.+)', date_text)
            if date_match:
                car_info['listing_date'] = date_match.group(1).strip()
        
        car_info['detail_url'] = url
        return car_info
    
    def _clean_label(self, label):
        """Clean and normalize field labels"""
        # Remove special characters and convert to lowercase
        label = re.sub(r'[^\w\s]', '', label)
        label = label.lower().replace(' ', '_')
        # Map Azerbaijani labels to English
        label_map = {
            'qiymət': 'price',
            'marka': 'brand',
            'model': 'model',
            'rəng': 'color',
            'il': 'year',
            'mühərrik_sm³': 'engine_size',
            'yürüş_km': 'mileage',
            'ban_növü': 'body_type',
            'yanacaq_növü': 'fuel_type',
            'sürətlər_qutusu': 'transmission',
            'kateqoriya': 'category'
        }
        return label_map.get(label, label)
    
    def get_phone_number(self, ajax_data):
        """Fetch phone number via AJAX call"""
        if not ajax_data or not all(ajax_data.values()):
            return None
            
        ajax_url = urljoin(self.base_url, '/ajax.php')
        
        # Prepare data for POST request
        post_data = {
            'act': 'telshow',
            'id': ajax_data['id'],
            't': ajax_data['t'],
            'h': ajax_data['h'],
            'rf': ajax_data['rf']
        }
        
        # Set headers for AJAX request
        ajax_headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': ajax_data.get('referer', self.base_url)
        }
        
        try:
            response = self.session.post(ajax_url, data=post_data, headers=ajax_headers)
            response.raise_for_status()
            
            data = response.json()
            if data.get('ok') == 1 and data.get('tel'):
                return data['tel']
            
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            logger.error(f"Error fetching phone number: {e}")
            
        return None
    
    def scrape_listing_page(self, url):
        """Scrape a single listing page"""
        logger.info(f"Scraping listing page: {url}")
        
        response = self.get_page(url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract basic info and links
        cars = self.extract_basic_info(soup)
        
        return cars
    
    def scrape_detail_page(self, url):
        """Scrape detailed information from a car detail page"""
        logger.info(f"Scraping detail page: {url}")
        
        response = self.get_page(url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract detailed information
        car_info = self.extract_detailed_info(soup, url)
        
        # Get phone number if AJAX data is available
        if 'ajax_data' in car_info:
            phone = self.get_phone_number(car_info['ajax_data'])
            if phone:
                car_info['phone'] = phone
            # Remove ajax_data from final output
            del car_info['ajax_data']
        
        return car_info
    
    def scrape_with_pagination(self, start_url, max_pages=None):
        """Scrape multiple pages with pagination"""
        all_cars = []
        current_page = 1
        
        # Extract start parameter from URL
        parsed_url = urlparse(start_url)
        query_params = parse_qs(parsed_url.query)
        start_param = int(query_params.get('start', [0])[0])
        
        base_listing_url = f"{self.base_url}/masin-satisi/"
        
        while True:
            if max_pages and current_page > max_pages:
                break
                
            # Calculate current start parameter
            current_start = start_param + (current_page - 1) * 20  # Assuming 20 items per page
            current_url = f"{base_listing_url}?start={current_start}"
            
            logger.info(f"Scraping page {current_page}: {current_url}")
            
            response = self.get_page(current_url)
            if not response:
                break
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract car links
            car_links = self.extract_listing_links(soup)
            
            if not car_links:
                logger.info("No more cars found. Stopping pagination.")
                break
            
            # Scrape each detail page
            for car_url in car_links:
                car_info = self.scrape_detail_page(car_url)
                if car_info:
                    all_cars.append(car_info)
                    
                # Be respectful with delays
                time.sleep(1)
            
            current_page += 1
            
            # Add delay between pages
            time.sleep(2)
        
        return all_cars
    
    def save_to_csv(self, cars, filename=None):
        """Save car data to CSV file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"masinlar_az_{timestamp}.csv"
        
        if not cars:
            logger.warning("No car data to save")
            return
        
        # Get all possible fieldnames
        fieldnames = set()
        for car in cars:
            fieldnames.update(car.keys())
        
        fieldnames = sorted(list(fieldnames))
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(cars)
        
        logger.info(f"Saved {len(cars)} cars to {filename}")
    
    def save_to_json(self, cars, filename=None):
        """Save car data to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"masinlar_az_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(cars, jsonfile, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(cars)} cars to {filename}")


def main():
    """Main function to run the scraper"""
    scraper = MasinlarScraper()
    
    # Example usage
    start_url = "https://masinlar.az/masin-satisi/?start=7"
    
    # Scrape with pagination (limit to 5 pages for testing)
    cars = scraper.scrape_with_pagination(start_url, max_pages=5)
    
    if cars:
        # Save to both CSV and JSON
        scraper.save_to_csv(cars)
        scraper.save_to_json(cars)
        
        print(f"Successfully scraped {len(cars)} cars")
        
        # Print sample car info
        if cars:
            print("\nSample car info:")
            print(json.dumps(cars[0], ensure_ascii=False, indent=2))
    else:
        print("No cars found")


if __name__ == "__main__":
    main()