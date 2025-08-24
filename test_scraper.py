#!/usr/bin/env python3
"""
Test script for Masinlar.az scraper
"""

from masinlar_scraper import MasinlarScraper
import json

def test_single_detail_page():
    """Test scraping a single detail page"""
    scraper = MasinlarScraper()
    
    # Test with the provided detail page URL
    test_url = "https://masinlar.az/renault-tondar-2013-il-46348.html"
    
    print(f"Testing detail page scraping: {test_url}")
    car_info = scraper.scrape_detail_page(test_url)
    
    if car_info:
        print("Success! Car info extracted:")
        print(json.dumps(car_info, ensure_ascii=False, indent=2))
        return True
    else:
        print("Failed to extract car info")
        return False

def test_listing_page():
    """Test scraping a listing page"""
    scraper = MasinlarScraper()
    
    # Test with the provided listing page URL
    test_url = "https://masinlar.az/masin-satisi/?start=7"
    
    print(f"\nTesting listing page scraping: {test_url}")
    cars = scraper.scrape_listing_page(test_url)
    
    if cars:
        print(f"Success! Found {len(cars)} cars on listing page")
        print("Sample car from listing:")
        print(json.dumps(cars[0], ensure_ascii=False, indent=2))
        return True
    else:
        print("Failed to extract cars from listing page")
        return False

def test_pagination():
    """Test pagination scraping with limited pages"""
    scraper = MasinlarScraper()
    
    # Test with pagination (limit to 2 pages)
    test_url = "https://masinlar.az/masin-satisi/?start=7"
    
    print(f"\nTesting pagination scraping (2 pages): {test_url}")
    cars = scraper.scrape_with_pagination(test_url, max_pages=2)
    
    if cars:
        print(f"Success! Scraped {len(cars)} cars from 2 pages")
        
        # Save test results
        scraper.save_to_json(cars, "test_results.json")
        scraper.save_to_csv(cars, "test_results.csv")
        
        print("Test results saved to test_results.json and test_results.csv")
        
        # Show sample
        print("\nSample detailed car info:")
        print(json.dumps(cars[0], ensure_ascii=False, indent=2))
        
        return True
    else:
        print("Failed to scrape cars with pagination")
        return False

if __name__ == "__main__":
    print("=== Masinlar.az Scraper Test ===")
    
    # Run tests
    test1 = test_single_detail_page()
    test2 = test_listing_page()
    test3 = test_pagination()
    
    # Summary
    print(f"\n=== Test Results ===")
    print(f"Detail page test: {'✓' if test1 else '✗'}")
    print(f"Listing page test: {'✓' if test2 else '✗'}")
    print(f"Pagination test: {'✓' if test3 else '✗'}")
    
    if all([test1, test2, test3]):
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Some tests failed. Check the error messages above.")