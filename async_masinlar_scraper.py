#!/usr/bin/env python3
"""
Fast Async Masinlar.az Car Scraper using asyncio and aiohttp

High-performance scraper that can handle multiple concurrent requests.
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import csv
import time
import re
from urllib.parse import urljoin, urlparse, parse_qs
import logging
from datetime import datetime
from typing import List, Dict, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AsyncMasinlarScraper:
    def __init__(self, concurrent_limit: int = 10):
        self.base_url = "https://masinlar.az"
        self.concurrent_limit = concurrent_limit
        self.semaphore = asyncio.Semaphore(concurrent_limit)
        
        # Headers to mimic a real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8,ru;q=0.7,az;q=0.6',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    async def fetch(self, session: aiohttp.ClientSession, url: str, method: str = 'GET', data=None) -> Optional[aiohttp.ClientResponse]:
        """Fetch a URL with semaphore limiting"""
        async with self.semaphore:
            try:
                if method == 'GET':
                    async with session.get(url) as response:
                        response.raise_for_status()
                        return await response.text()
                else:  # POST
                    async with session.post(url, data=data) as response:
                        response.raise_for_status()
                        return await response.json()
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                return None
    
    def extract_listing_links(self, html: str) -> List[str]:
        """Extract car detail page links from listing page"""
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        prod_divs = soup.find_all('div', class_='nobj prod prodbig')
        
        for div in prod_divs:
            link_tag = div.find('a', href=True)
            if link_tag:
                href = link_tag['href']
                full_url = urljoin(self.base_url, href)
                links.append(full_url)
                
        return links
    
    def extract_detailed_info(self, html: str, url: str) -> Dict:
        """Extract detailed information from car detail page"""
        soup = BeautifulSoup(html, 'html.parser')
        car_info = {'detail_url': url}
        
        # Extract title
        title_h1 = soup.find('h1')
        if title_h1:
            car_info['title'] = title_h1.get_text(strip=True)
        
        # Extract listing ID
        id_span = soup.find('span', class_='open_idshow')
        if id_span:
            id_text = id_span.get_text(strip=True)
            id_match = re.search(r'(\d+)', id_text)
            if id_match:
                car_info['listing_id'] = id_match.group(1)
        
        # Extract all details from the info section
        info_div = soup.find('div', class_='halfdiv openproduct')
        if info_div:
            for p in info_div.find_all('p'):
                bold_tag = p.find('b')
                if bold_tag:
                    label = bold_tag.get_text(strip=True)
                    text_content = p.get_text(strip=True)
                    value = text_content.replace(label, '', 1).strip()
                    
                    if value:
                        car_info[self._clean_label(label)] = value
        
        # Extract description
        desc_p = soup.find('p', class_='infop100 fullteshow')
        if desc_p:
            car_info['full_description'] = desc_p.get_text(strip=True)
        
        # Extract contact information
        contact_div = soup.find('div', class_='infocontact')
        if contact_div:
            contact_text = contact_div.get_text()
            lines = [line.strip() for line in contact_text.split('\n') if line.strip()]
            for line in lines:
                if not line.startswith('0') and len(line) > 2:
                    car_info['contact_person'] = line.replace('👤', '').strip()
                    break
            
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
                'rf': tel_div.get('data-rf', '')
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
        
        return car_info
    
    def _clean_label(self, label: str) -> str:
        """Clean and normalize field labels"""
        label = re.sub(r'[^\w\s]', '', label)
        label = label.lower().replace(' ', '_')
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
    
    async def get_phone_number(self, session: aiohttp.ClientSession, ajax_data: Dict, referer_url: str) -> Optional[str]:
        """Fetch phone number via AJAX call"""
        if not ajax_data or not ajax_data.get('id') or not ajax_data.get('h'):
            return None
            
        ajax_url = urljoin(self.base_url, '/ajax.php')
        
        post_data = {
            'act': 'telshow',
            'id': ajax_data['id'],
            't': ajax_data['t'],
            'h': ajax_data['h'],
            'rf': ajax_data['rf']
        }
        
        ajax_headers = {
            **self.headers,
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': referer_url,
            'Origin': self.base_url
        }
        
        try:
            async with self.semaphore:
                async with session.post(ajax_url, data=post_data, headers=ajax_headers) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    if data.get('ok') == 1 and data.get('tel'):
                        logger.debug(f"Got phone for ID {ajax_data['id']}: {data['tel']}")
                        return data['tel']
                    
        except Exception as e:
            logger.error(f"Error fetching phone for ID {ajax_data['id']}: {e}")
            
        return None
    
    async def scrape_detail_page(self, session: aiohttp.ClientSession, url: str) -> Optional[Dict]:
        """Scrape detailed information from a car detail page"""
        html = await self.fetch(session, url)
        if not html:
            return None
        
        car_info = self.extract_detailed_info(html, url)
        
        # Get phone number if AJAX data is available
        if 'ajax_data' in car_info:
            phone = await self.get_phone_number(session, car_info['ajax_data'], url)
            if phone:
                car_info['phone'] = phone
            del car_info['ajax_data']
        
        return car_info
    
    async def scrape_listing_page(self, session: aiohttp.ClientSession, url: str) -> List[str]:
        """Scrape a listing page and return car detail URLs"""
        html = await self.fetch(session, url)
        if not html:
            return []
        
        links = self.extract_listing_links(html)
        logger.debug(f"Found {len(links)} car links on {url}")
        return links
    
    async def scrape_cars_batch(self, session: aiohttp.ClientSession, car_urls: List[str]) -> List[Dict]:
        """Scrape multiple car detail pages concurrently"""
        tasks = [self.scrape_detail_page(session, url) for url in car_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        cars = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error scraping {car_urls[i]}: {result}")
            elif result:
                cars.append(result)
        
        return cars
    
    async def scrape_with_pagination(self, start_url: str, max_pages: Optional[int] = None) -> List[Dict]:
        """Scrape multiple pages with pagination - detects when site loops back to beginning"""
        all_cars = []
        current_page = 1
        consecutive_empty_pages = 0
        max_consecutive_empty = 3  # Stop after 3 consecutive empty pages  
        safety_limit = 60  # Based on site analysis - loops after ~40 pages
        seen_car_urls = set()  # Track seen URLs to detect loops
        first_page_urls = []  # Store first page URLs to detect loop
        
        # Extract start parameter from URL
        parsed_url = urlparse(start_url)
        query_params = parse_qs(parsed_url.query)
        start_param = int(query_params.get('start', [0])[0])
        
        base_listing_url = f"{self.base_url}/masin-satisi/"
        
        connector = aiohttp.TCPConnector(limit=50, limit_per_host=20)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(
            headers=self.headers, 
            connector=connector, 
            timeout=timeout
        ) as session:
            
            while True:
                # Safety check to prevent infinite loops
                if current_page > safety_limit:
                    logger.warning(f"Reached safety limit of {safety_limit} pages. Stopping.")
                    break
                    
                # Only check max_pages if explicitly set
                if max_pages and current_page > max_pages:
                    logger.info(f"Reached max_pages limit: {max_pages}")
                    break
                
                current_start = start_param + (current_page - 1) * 20
                current_url = f"{base_listing_url}?start={current_start}"
                
                logger.info(f"Scraping page {current_page}: start={current_start} (Total cars so far: {len(all_cars)})")
                
                # Progress update every 50 pages
                if current_page % 50 == 0:
                    elapsed = time.time() - time.time()  # This will be set from caller
                    print(f"🔄 Progress: Page {current_page}, Total cars: {len(all_cars)}")
                
                # Get car URLs from current page
                car_urls = await self.scrape_listing_page(session, current_url)
                
                if not car_urls:
                    consecutive_empty_pages += 1
                    logger.warning(f"No cars found on page {current_page} (URL: {current_url}). Empty pages: {consecutive_empty_pages}")
                    
                    if consecutive_empty_pages >= max_consecutive_empty:
                        logger.info(f"Found {consecutive_empty_pages} consecutive empty pages. Reached end of listings.")
                        break
                    
                    # Continue to next page in case it's just a gap
                    current_page += 1
                    await asyncio.sleep(2)  # Longer delay for empty pages
                    continue
                else:
                    consecutive_empty_pages = 0  # Reset counter
                    logger.info(f"Found {len(car_urls)} car URLs on page {current_page}")
                
                # Store first page URLs for loop detection
                if current_page == 1:
                    first_page_urls = car_urls[:5]  # Store first 5 URLs
                
                # Detect if we're seeing the same URLs as page 1 (pagination loop)
                if current_page > 35 and car_urls[:5] == first_page_urls:
                    logger.info(f"🔄 PAGINATION LOOP DETECTED at page {current_page} - same URLs as page 1!")
                    logger.info(f"Real end of listings reached. Total unique cars: {len(all_cars)}")
                    break
                
                # Check for duplicate URLs (another way to detect loops)
                new_urls = [url for url in car_urls if url not in seen_car_urls]
                duplicate_count = len(car_urls) - len(new_urls)
                
                if duplicate_count > len(car_urls) * 0.8:  # More than 80% duplicates
                    logger.info(f"🔄 High duplicate rate ({duplicate_count}/{len(car_urls)}) at page {current_page} - likely reached end!")
                    break
                
                # Add new URLs to seen set
                seen_car_urls.update(car_urls)
                
                # Scrape only new URLs to avoid duplicates
                cars = await self.scrape_cars_batch(session, new_urls)
                all_cars.extend(cars)
                
                if new_urls:
                    logger.info(f"Page {current_page}: scraped {len(cars)} new cars (Total: {len(all_cars)})")
                else:
                    logger.info(f"Page {current_page}: all URLs already seen, skipping")
                
                current_page += 1
                
                # Small delay between pages
                await asyncio.sleep(0.5)
        
        logger.info(f"🏁 Finished scraping! Total cars: {len(all_cars)}")
        return all_cars
    
    def save_to_csv(self, cars: List[Dict], filename: Optional[str] = None):
        """Save car data to CSV file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"masinlar_az_async_{timestamp}.csv"
        
        if not cars:
            logger.warning("No car data to save")
            return
        
        fieldnames = set()
        for car in cars:
            fieldnames.update(car.keys())
        
        fieldnames = sorted(list(fieldnames))
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(cars)
        
        logger.info(f"Saved {len(cars)} cars to {filename}")
    
    def save_to_json(self, cars: List[Dict], filename: Optional[str] = None):
        """Save car data to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"masinlar_az_async_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(cars, jsonfile, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(cars)} cars to {filename}")


async def main():
    """Main async function to run the scraper"""
    scraper = AsyncMasinlarScraper(concurrent_limit=15)
    
    start_url = "https://masinlar.az/masin-satisi/?start=0"
    
    # Choose your scraping mode:
    # 1. UNLIMITED (will scrape until end - could be 50,000+ cars!)
    # 2. LIMITED for testing/development
    
    print("🚗 Masinlar.az Async Scraper")
    print("Choose scraping mode:")
    print("1. Test mode (10 pages ~ 200-300 cars)")
    print("2. Full mode (ALL pages until loop detected ~ 800-1000 cars)")  
    print("3. Custom pages")
    
    try:
        choice = input("Enter your choice (1/2/3): ").strip()
    except:
        choice = "2"  # Default to full mode
    
    if choice == "1":
        max_pages = 10
        print("🧪 Running in TEST MODE (10 pages)")
    elif choice == "3":
        try:
            max_pages = int(input("Enter number of pages: "))
            print(f"🚀 Running CUSTOM MODE ({max_pages} pages)")
        except:
            max_pages = 10
            print("🧪 Invalid input, defaulting to TEST MODE (10 pages)")
    else:
        max_pages = None
        print("🌟 Running FULL MODE - will auto-detect end (loop detection enabled)!")
    
    start_time = time.time()
    cars = await scraper.scrape_with_pagination(start_url, max_pages=max_pages)
    
    end_time = time.time()
    
    if cars:
        # Save to both formats
        scraper.save_to_csv(cars)
        scraper.save_to_json(cars)
        
        elapsed = end_time - start_time
        print(f"\n🎉 Successfully scraped {len(cars)} cars in {elapsed:.2f} seconds")
        print(f"⚡ Speed: {len(cars)/elapsed:.2f} cars/second")
        print(f"🏁 Scraped ALL available cars from masinlar.az!")
        
        # Show sample and stats
        if cars:
            print("\nSample car info:")
            sample_car = cars[0]
            print(f"Title: {sample_car.get('title', 'N/A')}")
            print(f"Price: {sample_car.get('price', 'N/A')}")
            print(f"Phone: {sample_car.get('phone', 'N/A')}")
            print(f"Brand: {sample_car.get('brand', 'N/A')}")
            
            # Basic stats
            with_phones = sum(1 for car in cars if car.get('phone'))
            print(f"\n📊 Stats:")
            print(f"Total cars: {len(cars)}")
            print(f"Cars with phone numbers: {with_phones} ({with_phones/len(cars)*100:.1f}%)")
    else:
        print("No cars found")


if __name__ == "__main__":
    asyncio.run(main())