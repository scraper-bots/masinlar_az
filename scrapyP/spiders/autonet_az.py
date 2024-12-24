import aiohttp
import asyncio
import json
from typing import List, Dict
import logging
import pandas as pd
from datetime import datetime
from http.cookies import SimpleCookie
import urllib.parse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AutonetScraper:
    def __init__(self, base_url: str = "https://autonet.az/api/items/searchItem"):
        self.base_url = base_url
        self.results = []
        self.cookies = {}
        self.x_auth_token = "00028c2ddcc1ca6c32bc919dca64c288bf32ff2a"  # Fixed X-Authorization token

    async def _get_tokens(self, session: aiohttp.ClientSession) -> None:
        """Get CSRF token and session token from main page"""
        try:
            async with session.get("https://autonet.az/items") as response:
                if response.status == 200:
                    # Get cookies from response headers
                    if 'set-cookie' in response.headers:
                        cookie = SimpleCookie()
                        for cookie_str in response.headers.getall('set-cookie', []):
                            cookie.load(cookie_str)
                            for key, morsel in cookie.items():
                                self.cookies[key] = morsel.value
                                if key == 'XSRF-TOKEN':
                                    # URL decode the XSRF token
                                    self.cookies['XSRF-TOKEN'] = urllib.parse.unquote(morsel.value)
                    
                    logger.info("Successfully obtained cookies and tokens")
                else:
                    logger.error(f"Failed to get tokens: {response.status}")
        except Exception as e:
            logger.error(f"Error getting tokens: {str(e)}")
            raise

    def _get_headers(self) -> Dict[str, str]:
        """Get exact headers from successful browser request"""
        xsrf_token = self.cookies.get('XSRF-TOKEN', '')
        
        return {
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8,ru;q=0.7,az;q=0.6",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Host": "autonet.az",
            "Pragma": "no-cache",
            "Referer": "https://autonet.az/items",
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "X-Authorization": self.x_auth_token,
            "X-XSRF-TOKEN": xsrf_token
        }

    async def _fetch_page(self, session: aiohttp.ClientSession, page: int) -> Dict:
        """Fetch a single page of results"""
        try:
            params = {"page": str(page)}
            headers = self._get_headers()
            
            async with session.get(
                self.base_url, 
                params=params,
                headers=headers,
                cookies=self.cookies
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Error fetching page {page}: {response.status}")
                    text = await response.text()
                    logger.error(f"Response: {text[:200]}")
                    headers_sent = json.dumps(dict(response.request_info.headers))
                    logger.error(f"Headers sent: {headers_sent}")
                    return None

        except Exception as e:
            logger.error(f"Error on page {page}: {str(e)}")
            return None

    async def scrape(self, start_page: int = 1, end_page: int = 3) -> List[Dict]:
        """Scrape all pages sequentially"""
        try:
            logger.info(f"Starting scrape from page {start_page} to {end_page}")
            
            session_timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=session_timeout) as session:
                # Get initial tokens
                await self._get_tokens(session)
                
                # First do a test request
                test_data = await self._fetch_page(session, 1)
                if not test_data:
                    raise Exception("Initial test request failed")
                
                # Continue with all pages
                for page in range(start_page, end_page + 1):
                    data = await self._fetch_page(session, page)
                    if data and "data" in data:
                        self.results.extend(data["data"])
                        logger.info(f"Successfully scraped page {page}")
                        # Small delay between requests
                        await asyncio.sleep(1)
                    else:
                        logger.error(f"Failed to get data from page {page}")

            return self.results

        except Exception as e:
            logger.error(f"Scraping failed: {str(e)}")
            raise

    def save_to_csv(self, filename: str = None) -> None:
        """Save results to CSV file"""
        if not filename:
            filename = f"autonet_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        df = pd.DataFrame(self.results)
        
        if not df.empty:
            # Clean numeric columns
            numeric_columns = ['price', 'id', 'engine_capacity', 'at_gucu', 'yurus']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Convert dates
            date_columns = ['date', 'created_at', 'updated_at']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col])
            
            # Sort by date
            if 'date' in df.columns:
                df = df.sort_values('date', ascending=False)
        
        df.to_csv(filename, index=False, encoding='utf-8')
        logger.info(f"Data saved to {filename}")
        logger.info(f"Total records saved: {len(df)}")

async def main():
    scraper = AutonetScraper()

    try:
        # Start with test range
        results = await scraper.scrape(start_page=1, end_page=3)
        
        if results:
            scraper.save_to_csv()
            logger.info(f"Successfully scraped {len(results)} listings")
        else:
            logger.error("No results were scraped")
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())