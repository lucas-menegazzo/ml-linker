"""
Main execution script for Instagram Deal Generator
"""

import os
import time
import sys
from src.config import (
    INPUT_CSV, OUTPUT_IMAGES_DIR, OUTPUT_DATA_DIR,
    SCRAPING_DELAY
)
from src.utils import parse_product_links, ensure_directory
from src.scraper import scrape_product
from src.image_generator import generate_instagram_image
from src.database import load_products, save_product, is_product_processed, get_product_count


def main():
    """Main execution pipeline."""
    print("=" * 60)
    print("Instagram Deal Post Generator")
    print("=" * 60)
    print()
    
    # Check if Selenium is available
    try:
        from src.scraper_selenium import SELENIUM_AVAILABLE
        if not SELENIUM_AVAILABLE:
            print("WARNING: Selenium not available!")
            print("   For reliable scraping of Mercado Livre pages, install:")
            print("   pip install selenium webdriver-manager")
            print("   The scraper will try HTML parsing but may fail on JavaScript-rendered pages.")
            print()
    except:
        print("WARNING: Selenium check failed!")
        print("   Install with: pip install selenium webdriver-manager")
        print()
    
    # Ensure output directories exist
    ensure_directory(OUTPUT_IMAGES_DIR)
    ensure_directory(OUTPUT_DATA_DIR)
    ensure_directory("temp")
    
    # Parse product links
    print(f"Reading product links from: {INPUT_CSV}")
    try:
        products = parse_product_links(INPUT_CSV)
        print(f"Found {len(products)} products to process")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    
    if not products:
        print("No products found in CSV file!")
        sys.exit(1)
    
    # Load existing products
    existing_products = load_products()
    print(f"Already processed: {len(existing_products)} products")
    print()
    
    # Process each product
    successful = 0
    failed = 0
    skipped = 0
    
    for i, product in enumerate(products, 1):
        internal_id = product['id']
        url = product['url']
        
        print(f"[{i}/{len(products)}] Processing product ID {internal_id}")
        print(f"  URL: {url}")
        
        # Check if already processed
        if is_product_processed(internal_id):
            print(f"  [OK] Already processed, skipping...")
            skipped += 1
            print()
            continue
        
        # Scrape product data
        product_data = scrape_product(url)
        
        if not product_data:
            print(f"  [FAIL] Failed to scrape product data")
            failed += 1
            print()
            time.sleep(SCRAPING_DELAY)
            continue
        
        print(f"  [OK] Scraped: {product_data.get('title', 'N/A')[:50]}...")
        print(f"    Price: {product_data.get('currency', 'R$')} {product_data.get('current_price', 'N/A')}")
        if product_data.get('discount_percentage', 0) > 0:
            print(f"    Discount: {product_data.get('discount_percentage', 0)}%")
        
        # Generate Instagram image
        image_filename = f"product_{internal_id}.jpg"
        image_path = os.path.join(OUTPUT_IMAGES_DIR, image_filename)
        
        print(f"  Generating Instagram image...")
        if generate_instagram_image(product_data, image_path):
            print(f"  [OK] Image generated: {image_path}")
            
            # Save product data
            if save_product(internal_id, product_data, image_path):
                print(f"  [OK] Product data saved")
                successful += 1
            else:
                print(f"  [FAIL] Failed to save product data")
                failed += 1
        else:
            print(f"  [FAIL] Failed to generate image")
            failed += 1
        
        print()
        
        # Rate limiting delay
        if i < len(products):
            time.sleep(SCRAPING_DELAY)
    
    # Summary
    print("=" * 60)
    print("Processing Complete!")
    print("=" * 60)
    print(f"Total products: {len(products)}")
    print(f"  [OK] Successful: {successful}")
    print(f"  [SKIP] Skipped: {skipped}")
    print(f"  [FAIL] Failed: {failed}")
    print()
    print(f"Generated images: {OUTPUT_IMAGES_DIR}")
    print(f"Product data: {OUTPUT_DATA_DIR}/products.json")
    print()


if __name__ == "__main__":
    main()

