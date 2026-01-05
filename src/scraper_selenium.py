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
        chrome_options.add_argument('--headless=new')  # Use new headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument(f'user-agent={USER_AGENT}')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-extensions')
        
        # Try to find Chrome binary in common locations (for Docker/Render)
        import os
        chrome_binary = None
        possible_paths = [
            '/usr/bin/google-chrome',
            '/usr/bin/google-chrome-stable',
            '/usr/bin/chromium',
            '/usr/bin/chromium-browser',
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                chrome_binary = path
                chrome_options.binary_location = chrome_binary
                print(f"  Found Chrome binary at: {chrome_binary}")
                break
        
        # Create driver - try multiple methods
        driver = None
        try:
            # Method 1: Try with ChromeDriverManager (works locally)
            try:
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
                print("  [OK] Chrome driver created with ChromeDriverManager")
            except Exception as e1:
                print(f"  ChromeDriverManager failed: {str(e1)}")
                # Method 2: Try with system chromedriver (works in Docker)
                try:
                    service = Service('/usr/bin/chromedriver') if os.path.exists('/usr/bin/chromedriver') else None
                    if service:
                        driver = webdriver.Chrome(service=service, options=chrome_options)
                        print("  [OK] Chrome driver created with system chromedriver")
                    else:
                        # Method 3: Try without service (Chrome finds driver automatically)
                        driver = webdriver.Chrome(options=chrome_options)
                        print("  [OK] Chrome driver created without explicit service")
                except Exception as e2:
                    print(f"  System chromedriver failed: {str(e2)}")
                    # Method 4: Last resort - try without service
                    driver = webdriver.Chrome(options=chrome_options)
                    print("  [OK] Chrome driver created (last resort)")
        except Exception as chrome_error:
            # Chrome not available
            error_msg = str(chrome_error).lower()
            if 'chrome' in error_msg or 'binary' in error_msg or 'executable' in error_msg:
                print(f"  Chrome not available: {str(chrome_error)}")
                return None
            raise  # Re-raise if it's a different error
        
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
        # First, try XPath for large image (main gallery image)
        xpath_selectors = [
            "//*[@id=':Raool7le:']/div[2]/div/div/div[1]/a/img",  # Large gallery image
            "//div[contains(@class, 'ui-pdp-gallery')]//a/img",  # Gallery link image
            "//div[contains(@class, 'gallery')]//a/img",  # Generic gallery
        ]
        
        for xpath in xpath_selectors:
            try:
                img_element = driver.find_element(By.XPATH, xpath)
                img_url = (img_element.get_attribute('src') or 
                          img_element.get_attribute('data-src') or 
                          img_element.get_attribute('data-zoom') or
                          img_element.get_attribute('data-lazy-src') or
                          img_element.get_attribute('href'))
                if img_url:
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    elif img_url.startswith('/'):
                        img_url = 'https://www.mercadolivre.com.br' + img_url
                    # Clean URL - remove size parameters to get full resolution
                    img_url = img_url.split('?')[0]
                    # Remove size suffixes like -O.jpg, -V.jpg, etc. to get full size
                    if '-O.' in img_url or '-V.' in img_url or '-F.' in img_url:
                        # Replace with -O for original/full size
                        img_url = re.sub(r'-[OVF]\.[^.]+$', '-O.jpg', img_url)
                    # Check if it looks like a product image
                    if any(keyword in img_url.lower() for keyword in ['mlb', 'produto', 'product', 'o-l', 'o-f', 'http']):
                        product_data['image_url'] = img_url
                        print(f"  [OK] Found large image via XPath: {img_url[:80]}...")
                        break
            except:
                continue
        
        # If XPath didn't work, try CSS selectors
        if not product_data['image_url']:
            img_selectors = [
                "img.ui-pdp-image",
                "img[class*='ui-pdp-image']",
                "img[data-zoom]",
                ".ui-pdp-image img",
                "img[alt*='produto']",
                "img[alt*='product']",
                ".ui-pdp-gallery img",
                "[class*='gallery'] img",
                ".ui-pdp-gallery__column img",
                "a[href*='zoom'] img"
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
                        # Clean URL - remove size parameters
                        img_url = img_url.split('?')[0]
                        # Remove size suffixes to get full size
                        if '-O.' in img_url or '-V.' in img_url or '-F.' in img_url:
                            img_url = re.sub(r'-[OVF]\.[^.]+$', '-O.jpg', img_url)
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
        error_msg = str(e).lower()
        # Check if it's a Chrome binary error (common in cloud environments)
        if 'chrome' in error_msg and ('binary' in error_msg or 'executable' in error_msg or 'cannot find' in error_msg):
            print(f"  Chrome not available in this environment, using HTML parser fallback...")
        else:
            print(f"  Error with Selenium scraper: {str(e)}")
        return None
    
    finally:
        if driver:
            driver.quit()

