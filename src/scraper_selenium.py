"""
Optional Selenium-based scraper for JavaScript-rendered Mercado Livre pages
Requires: pip install selenium webdriver-manager
"""

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

from typing import Dict, Optional
from src.config import REQUEST_TIMEOUT, USER_AGENT
import time


def scrape_product_selenium(url: str) -> Optional[Dict[str, any]]:
    """
    Scrape product using Selenium (for JavaScript-rendered pages).
    
    Args:
        url: Mercado Livre product URL
        
    Returns:
        Dictionary with product data or None if failed
    """
    if not SELENIUM_AVAILABLE:
        print("Selenium not available. Install with: pip install selenium webdriver-manager")
        return None
    
    driver = None
    try:
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument(f'user-agent={USER_AGENT}')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Create driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Clean URL
        clean_url = url.split('#')[0]
        print(f"Scraping with Selenium: {clean_url}")
        
        # Load page
        driver.get(clean_url)
        
        # Wait for page to load - wait for body or main content
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except:
            pass
        
        # Additional wait for JavaScript to render
        time.sleep(5)  # Give JavaScript more time to render
        
        # Extract data
        product_data = {
            'url': clean_url,
            'title': None,
            'image_url': None,
            'original_price': None,
            'current_price': None,
            'discount_percentage': 0.0,
            'currency': 'R$'
        }
        
        # Extract title - try multiple strategies
        title_selectors = [
            "h1.ui-pdp-title",
            "h1[class*='ui-pdp-title']",
            "h1[class*='title']",
            "h1.andes-visually-hidden",
            "h1",
            "[data-testid='title']",
            ".ui-pdp-title"
        ]
        
        for selector in title_selectors:
            try:
                title_element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                title_text = title_element.text.strip()
                if title_text and len(title_text) > 5:
                    product_data['title'] = title_text
                    break
            except:
                continue
        
        # Fallback: try any h1
        if not product_data['title']:
            try:
                title_element = driver.find_element(By.TAG_NAME, "h1")
                title_text = title_element.text.strip()
                if title_text and len(title_text) > 5:
                    product_data['title'] = title_text
            except:
                pass
        
        # Extract price - try multiple strategies
        price_selectors = [
            ".ui-pdp-price__second-line .andes-money-amount__fraction",
            ".ui-pdp-price .andes-money-amount__fraction",
            ".andes-money-amount__fraction",
            "[data-testid='price']",
            ".ui-pdp-price__second-line .andes-money-amount",
            ".ui-pdp-price .andes-money-amount",
            "[class*='price'] [class*='fraction']",
            ".price-tag-fraction"
        ]
        
        for selector in price_selectors:
            try:
                price_element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                price_text = price_element.text.strip()
                from src.scraper import parse_price
                price = parse_price(price_text)
                if price and price > 0:
                    product_data['current_price'] = price
                    break
            except:
                continue
        
        # Fallback: search page source for price pattern
        if not product_data['current_price']:
            try:
                page_source = driver.page_source
                import re
                from src.scraper import parse_price
                price_pattern = r'R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)'
                matches = re.findall(price_pattern, page_source)
                for match in matches:
                    price = parse_price(match)
                    if price and price > 0:
                        product_data['current_price'] = price
                        break
            except:
                pass
        
        # Extract original price
        try:
            original_selectors = [
                ".ui-pdp-price__original .andes-money-amount__fraction",
                "s .andes-money-amount__fraction",
                "del .andes-money-amount__fraction"
            ]
            for selector in original_selectors:
                try:
                    original_element = driver.find_element(By.CSS_SELECTOR, selector)
                    price_text = original_element.text.strip()
                    from src.scraper import parse_price
                    price = parse_price(price_text)
                    if price:
                        product_data['original_price'] = price
                        break
                except:
                    continue
        except:
            pass
        
        # Extract image - try multiple strategies
        img_selectors = [
            "img.ui-pdp-image",
            "img[class*='ui-pdp-image']",
            "img[data-zoom]",
            ".ui-pdp-image img",
            "img[alt*='produto']",
            "img[alt*='product']",
            ".ui-pdp-gallery img",
            "[class*='gallery'] img"
        ]
        
        for selector in img_selectors:
            try:
                img_element = driver.find_element(By.CSS_SELECTOR, selector)
                img_url = (img_element.get_attribute('src') or 
                          img_element.get_attribute('data-src') or 
                          img_element.get_attribute('data-zoom') or
                          img_element.get_attribute('data-lazy-src'))
                if img_url:
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    elif img_url.startswith('/'):
                        img_url = 'https://www.mercadolivre.com.br' + img_url
                    # Clean URL
                    img_url = img_url.split('?')[0]
                    # Check if it looks like a product image
                    if any(keyword in img_url.lower() for keyword in ['mlb', 'produto', 'product', 'o-l', 'o-f']):
                        product_data['image_url'] = img_url
                        break
            except:
                continue
        
        # Fallback: try og:image meta tag
        if not product_data['image_url']:
            try:
                og_image = driver.find_element(By.CSS_SELECTOR, "meta[property='og:image']")
                img_url = og_image.get_attribute('content')
                if img_url:
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    product_data['image_url'] = img_url.split('?')[0]
            except:
                pass
        
        # Calculate discount
        if product_data['original_price'] and product_data['current_price']:
            from src.scraper import calculate_discount
            product_data['discount_percentage'] = calculate_discount(
                product_data['original_price'], product_data['current_price']
            )
        
        # Validate and print debug info
        print(f"  Extracted - Title: {bool(product_data.get('title'))}, Price: {bool(product_data.get('current_price'))}, Image: {bool(product_data.get('image_url'))}")
        
        if not product_data.get('title') or not product_data.get('current_price'):
            print(f"  Missing required data - Title: '{product_data.get('title')}', Price: {product_data.get('current_price')}")
            return None
        
        return product_data
    
    except Exception as e:
        print(f"Error with Selenium scraper: {str(e)}")
        return None
    
    finally:
        if driver:
            driver.quit()

