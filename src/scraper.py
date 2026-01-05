"""
Mercado Livre product scraper
"""

import requests
from bs4 import BeautifulSoup
import time
import re
import json
from typing import Dict, Optional
from src.config import SCRAPING_DELAY, REQUEST_TIMEOUT, USER_AGENT


def normalize_url(url: str) -> str:
    """Normalize Mercado Livre URL to standard format."""
    # Remove hash/fragment
    url = url.split('#')[0]
    
    # Convert /p/ URLs to /produto/ format if possible
    # Example: /p/MLB51568808 -> try to get product page
    if '/p/' in url:
        # Extract product ID
        match = re.search(r'/p/(MLB\d+)', url)
        if match:
            product_id = match.group(1)
            # Try to construct standard URL (though this might not always work)
            # We'll keep original URL but note the format
            pass
    
    return url


def try_mercado_livre_api(product_id: str) -> Optional[Dict]:
    """
    Try to fetch product data from Mercado Livre API.
    This is a fallback when HTML parsing fails.
    """
    try:
        # Mercado Livre API endpoint for items
        api_url = f"https://api.mercadolivre.com/items/MLB{product_id}"
        
        headers = {
            'User-Agent': USER_AGENT,
            'Accept': 'application/json',
        }
        
        print(f"  Trying Mercado Livre API for product ID: MLB{product_id}")
        response = requests.get(api_url, headers=headers, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            
            product_data = {
                'url': f"https://produto.mercadolivre.com.br/MLB-{product_id}",
                'title': data.get('title', ''),
                'image_url': None,
                'original_price': None,
                'current_price': None,
                'discount_percentage': 0.0,
                'currency': 'R$'
            }
            
            # Extract image
            pictures = data.get('pictures', [])
            if pictures and len(pictures) > 0:
                product_data['image_url'] = pictures[0].get('url', pictures[0].get('secure_url'))
            
            # Extract price
            price = data.get('price')
            if price:
                product_data['current_price'] = float(price)
            
            # Extract currency
            currency_id = data.get('currency_id', 'BRL')
            product_data['currency'] = 'R$' if currency_id == 'BRL' else currency_id
            
            if product_data['title'] and product_data['current_price']:
                print(f"  [OK] Successfully fetched data from Mercado Livre API")
                return product_data
        else:
            print(f"  API returned status {response.status_code}")
    except Exception as e:
        print(f"  API fetch failed: {str(e)}")
    
    return None


def scrape_product(url: str) -> Optional[Dict[str, any]]:
    """
    Scrape product information from Mercado Livre URL.
    Tries Selenium first (if available), then falls back to HTML parsing.
    
    Args:
        url: Mercado Livre product URL
        
    Returns:
        Dictionary with product data or None if failed
    """
    # Normalize and clean URL
    clean_url = normalize_url(url)
    print(f"Scraping: {clean_url}")
    
    # Try to extract product ID for API fallback
    product_id = None
    id_match = re.search(r'MLB-?(\d+)', clean_url, re.IGNORECASE)
    if id_match:
        product_id = id_match.group(1)
    
    # Try to extract product ID for API fallback
    product_id = None
    id_match = re.search(r'MLB-?(\d+)', clean_url, re.IGNORECASE)
    if id_match:
        product_id = id_match.group(1)
    
    # Try Selenium first (most reliable for JavaScript-rendered pages)
    # But skip if we're in a cloud environment where Chrome is not available
    try:
        from src.scraper_selenium import scrape_product_selenium, SELENIUM_AVAILABLE
        if SELENIUM_AVAILABLE:
            # Check if we're in a cloud environment (Render, Heroku, etc.)
            import os
            is_cloud = os.environ.get('RENDER') or os.environ.get('DYNO') or os.environ.get('FLY_APP_NAME')
            
            if not is_cloud:
                # Only try Selenium if not in cloud (where Chrome is not available)
                print("  Using Selenium for JavaScript-rendered content...")
                result = scrape_product_selenium(clean_url)
                if result:
                    return result
                print("  Selenium extraction failed, trying HTML parser...")
            else:
                print("  Cloud environment detected, skipping Selenium (Chrome not available), using HTML parser...")
        else:
            print("  Selenium not available, using HTML parser...")
    except ImportError:
        print("  Selenium not available, using HTML parser...")
    except Exception as e:
        error_msg = str(e).lower()
        if 'chrome' in error_msg and ('binary' in error_msg or 'executable' in error_msg):
            print("  Chrome not available in this environment, using HTML parser...")
        else:
            print(f"  Selenium error: {str(e)}, trying HTML parser...")
    
    # Fall back to HTML parsing
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Referer': 'https://www.mercadolivre.com.br/',
    }
    
    try:
        response = requests.get(clean_url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # First, try to extract from JSON-LD or embedded JSON
        product_data = extract_from_json(soup, clean_url)
        
        # If JSON extraction failed, try HTML parsing
        if not product_data or not product_data.get('title'):
            product_data = {
                'url': clean_url,
                'title': extract_title(soup),
                'image_url': extract_image(soup),
                'original_price': None,
                'current_price': extract_price(soup),
                'discount_percentage': 0.0,
                'currency': 'R$'
            }
            
            # Try to extract original price
            original_price = extract_original_price(soup)
            if original_price:
                product_data['original_price'] = original_price
                if product_data['current_price']:
                    product_data['discount_percentage'] = calculate_discount(
                        original_price, product_data['current_price']
                    )
        
        # Validate that we got at least title and price
        if not product_data.get('title') or not product_data.get('current_price'):
            print(f"Warning: Incomplete data extracted from {clean_url}")
            print(f"  Title found: {bool(product_data.get('title'))}")
            print(f"  Price found: {bool(product_data.get('current_price'))}")
            print(f"  Image found: {bool(product_data.get('image_url'))}")
            
            # Try one more time with more aggressive extraction
            if not product_data.get('title'):
                product_data['title'] = extract_title_aggressive(soup)
            if not product_data.get('current_price'):
                product_data['current_price'] = extract_price_aggressive(soup)
            if not product_data.get('image_url'):
                product_data['image_url'] = extract_image_aggressive(soup)
            
            # Final validation
            if not product_data.get('title') or not product_data.get('current_price'):
                print(f"  HTML parser failed to extract data")
                print(f"  Final title: {product_data.get('title', 'None')}")
                print(f"  Final price: {product_data.get('current_price', 'None')}")
                
                # Try Mercado Livre API as last resort
                if product_id:
                    print(f"  Trying Mercado Livre API as fallback...")
                    api_data = try_mercado_livre_api(product_id)
                    if api_data:
                        return api_data
                
                print(f"  Error: Could not extract required data (title and price)")
                print(f"  Note: Mercado Livre pages are JavaScript-rendered.")
                print(f"  Consider using Selenium for full page rendering (requires Chrome).")
                return None
        
        return product_data
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {str(e)}")
        return None
    except Exception as e:
        print(f"Error parsing {url}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def extract_from_json(soup: BeautifulSoup, url: str) -> Optional[Dict]:
    """Try to extract product data from JSON-LD or embedded JSON scripts."""
    product_data = {
        'url': url,
        'title': None,
        'image_url': None,
        'original_price': None,
        'current_price': None,
        'discount_percentage': 0.0,
        'currency': 'R$'
    }
    
    # Look for JSON-LD structured data
    json_ld = soup.find_all('script', type='application/ld+json')
    for script in json_ld:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                if data.get('@type') in ['Product', 'Offer']:
                    if 'name' in data:
                        product_data['title'] = data['name']
                    if 'image' in data:
                        img = data['image']
                        if isinstance(img, list):
                            img = img[0]
                        if isinstance(img, dict):
                            img = img.get('url', img.get('@id', ''))
                        product_data['image_url'] = img
                    if 'offers' in data:
                        offers = data['offers']
                        if isinstance(offers, list):
                            offers = offers[0]
                        if 'price' in offers:
                            product_data['current_price'] = float(offers['price'])
                        if 'priceCurrency' in offers:
                            product_data['currency'] = offers['priceCurrency']
        except:
            continue
    
    # Look for window.__PRELOADED_STATE__ or similar JSON data
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string:
            script_text = script.string
            
            # Look for product data in window.__PRELOADED_STATE__
            if '__PRELOADED_STATE__' in script_text or 'window.__PRELOADED_STATE__' in script_text:
                try:
                    # Extract JSON from script
                    text = script_text
                    # Try to find JSON object - look for window.__PRELOADED_STATE__ = {...}
                    # Pattern: window.__PRELOADED_STATE__ = {...}
                    pattern = r'window\.__PRELOADED_STATE__\s*=\s*(\{.*?\});'
                    match = re.search(pattern, text, re.DOTALL)
                    if match:
                        json_str = match.group(1)
                    else:
                        # Try to find JSON object
                        start = text.find('{')
                        end = text.rfind('}') + 1
                        if start >= 0 and end > start:
                            json_str = text[start:end]
                        else:
                            continue
                    
                    data = json.loads(json_str)
                    # Navigate through the structure to find product data
                    # This structure varies, so we'll try common paths
                    if isinstance(data, dict):
                        # Try common paths for product data
                        paths = [
                            ['initialState', 'components', 'product'],
                            ['initialState', 'product'],
                            ['product'],
                            ['item', 'product'],
                        ]
                        for path in paths:
                            current = data
                            try:
                                for key in path:
                                    current = current[key]
                                if isinstance(current, dict):
                                    if 'title' in current and not product_data['title']:
                                        product_data['title'] = current['title']
                                    if 'pictures' in current and not product_data['image_url']:
                                        pics = current['pictures']
                                        if isinstance(pics, list) and len(pics) > 0:
                                            product_data['image_url'] = pics[0].get('url', pics[0])
                                    if 'price' in current and not product_data['current_price']:
                                        price = current['price']
                                        if isinstance(price, (int, float)):
                                            product_data['current_price'] = float(price)
                                        elif isinstance(price, dict):
                                            product_data['current_price'] = float(price.get('amount', 0))
                                    break
                            except (KeyError, TypeError):
                                continue
                except:
                    continue
            
            # Look for price in data attributes or data-* patterns
            price_patterns = [
                r'"price"\s*:\s*(\d+(?:\.\d+)?)',
                r'"amount"\s*:\s*(\d+(?:\.\d+)?)',
                r'"value"\s*:\s*(\d+(?:\.\d+)?)',
                r'price["\']?\s*:\s*["\']?(\d+(?:\.\d+)?)',
            ]
            for pattern in price_patterns:
                price_match = re.search(pattern, script_text, re.IGNORECASE)
                if price_match and not product_data['current_price']:
                    try:
                        price_val = float(price_match.group(1))
                        # Validate it's a reasonable price (between 1 and 1 million)
                        if 1 <= price_val <= 1000000:
                            product_data['current_price'] = price_val
                            break
                    except:
                        pass
            
            # Look for title in JSON patterns
            if not product_data['title']:
                title_patterns = [
                    r'"title"\s*:\s*"([^"]+)"',
                    r'"name"\s*:\s*"([^"]+)"',
                    r'"productName"\s*:\s*"([^"]+)"',
                ]
                for pattern in title_patterns:
                    title_match = re.search(pattern, script_text, re.IGNORECASE)
                    if title_match:
                        title = title_match.group(1)
                        # Basic validation - should be longer than 5 chars
                        if len(title) > 5 and 'mercado livre' not in title.lower():
                            product_data['title'] = title
                            break
    
    # Return only if we got at least title or price
    if product_data['title'] or product_data['current_price']:
        return product_data
    return None


def extract_title(soup: BeautifulSoup) -> Optional[str]:
    """Extract product title from HTML."""
    # Try multiple selectors
    selectors = [
        'h1.ui-pdp-title',
        'h1[class*="title"]',
        'h1.andes-visually-hidden',
        'h1',
        '.ui-pdp-title',
        '[data-testid="title"]'
    ]
    
    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            title = element.get_text(strip=True)
            if title and len(title) > 5:  # Basic validation
                return title
    
    return None


def extract_title_aggressive(soup: BeautifulSoup) -> Optional[str]:
    """More aggressive title extraction."""
    # Try meta tags
    meta_title = soup.find('meta', property='og:title')
    if meta_title and meta_title.get('content'):
        return meta_title.get('content').strip()
    
    # Try title tag
    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.get_text(strip=True)
        # Remove common suffixes
        title = re.sub(r'\s*-\s*Mercado Livre.*$', '', title, flags=re.IGNORECASE)
        if title and len(title) > 5:
            return title
    
    # Try any h1
    h1 = soup.find('h1')
    if h1:
        title = h1.get_text(strip=True)
        if title and len(title) > 5:
            return title
    
    return None


def extract_image(soup: BeautifulSoup) -> Optional[str]:
    """Extract main product image URL."""
    # Try multiple selectors for product image
    selectors = [
        'img.ui-pdp-image',
        'img[class*="ui-pdp-image"]',
        'img[data-zoom]',
        'img[class*="gallery"]',
        '.ui-pdp-image img',
        'img[alt*="produto"]',
        'img[alt*="product"]'
    ]
    
    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            img_url = element.get('src') or element.get('data-src') or element.get('data-zoom')
            if img_url:
                # Clean up URL (remove size parameters if present)
                img_url = img_url.split('?')[0]
                # Ensure full URL
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif img_url.startswith('/'):
                    img_url = 'https://www.mercadolivre.com.br' + img_url
                return img_url
    
    # Fallback: try to find any large image
    images = soup.find_all('img')
    for img in images:
        src = img.get('src') or img.get('data-src')
        if src and ('produto' in src.lower() or 'product' in src.lower() or 'mlb' in src.lower()):
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                src = 'https://www.mercadolivre.com.br' + src
            return src
    
    return None


def extract_image_aggressive(soup: BeautifulSoup) -> Optional[str]:
    """More aggressive image extraction."""
    # Try og:image meta tag
    og_image = soup.find('meta', property='og:image')
    if og_image and og_image.get('content'):
        img_url = og_image.get('content')
        if img_url.startswith('//'):
            img_url = 'https:' + img_url
        return img_url
    
    # Try all images and find the largest one
    images = soup.find_all('img')
    largest_img = None
    largest_size = 0
    
    for img in images:
        src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
        if src:
            # Check if it looks like a product image
            if any(keyword in src.lower() for keyword in ['mlb', 'produto', 'product', 'item', 'o-l', 'o-f']):
                # Try to get dimensions
                width = img.get('width')
                height = img.get('height')
                if width and height:
                    try:
                        size = int(width) * int(height)
                        if size > largest_size:
                            largest_size = size
                            largest_img = src
                    except:
                        pass
                elif not largest_img:
                    largest_img = src
    
    if largest_img:
        if largest_img.startswith('//'):
            largest_img = 'https:' + largest_img
        elif largest_img.startswith('/'):
            largest_img = 'https://www.mercadolivre.com.br' + largest_img
        return largest_img
    
    return None


def extract_price(soup: BeautifulSoup) -> Optional[float]:
    """Extract current price from HTML."""
    # Try multiple selectors
    selectors = [
        '.ui-pdp-price__second-line .andes-money-amount__fraction',
        '.ui-pdp-price .andes-money-amount__fraction',
        '[class*="price"] [class*="fraction"]',
        '.andes-money-amount__fraction',
        '[data-testid="price"]',
        '.price-tag-fraction'
    ]
    
    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            price_text = element.get_text(strip=True)
            price = parse_price(price_text)
            if price:
                return price
    
    # Fallback: search for price patterns in text
    price_pattern = r'R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)'
    text = soup.get_text()
    matches = re.findall(price_pattern, text)
    if matches:
        return parse_price(matches[0])
    
    return None


def extract_price_aggressive(soup: BeautifulSoup) -> Optional[float]:
    """More aggressive price extraction."""
    # Look for price in meta tags
    price_meta = soup.find('meta', property='product:price:amount')
    if price_meta and price_meta.get('content'):
        try:
            return float(price_meta.get('content'))
        except:
            pass
    
    # Search entire page text for price patterns
    page_text = soup.get_text()
    
    # Look for R$ patterns more aggressively
    price_patterns = [
        r'R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
        r'R\$\s*(\d+(?:,\d{2})?)',
        r'price["\']?\s*:\s*["\']?(\d+(?:\.\d+)?)',
        r'"amount"\s*:\s*(\d+(?:\.\d+)?)',
    ]
    
    for pattern in price_patterns:
        matches = re.findall(pattern, page_text, re.IGNORECASE)
        for match in matches:
            price = parse_price(match)
            if price and price > 0:
                return price
    
    return None


def extract_original_price(soup: BeautifulSoup) -> Optional[float]:
    """Extract original price (before discount) from HTML."""
    # Look for strikethrough prices or "de" prices
    selectors = [
        '.ui-pdp-price__original .andes-money-amount__fraction',
        '[class*="price"] [class*="original"] [class*="fraction"]',
        's .andes-money-amount__fraction',
        'del .andes-money-amount__fraction',
        '[class*="strikethrough"] [class*="fraction"]'
    ]
    
    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            price_text = element.get_text(strip=True)
            price = parse_price(price_text)
            if price:
                return price
    
    # Look for "de R$" pattern
    text = soup.get_text()
    de_pattern = r'de\s+R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)'
    matches = re.findall(de_pattern, text, re.IGNORECASE)
    if matches:
        return parse_price(matches[0])
    
    return None


def parse_price(price_text: str) -> Optional[float]:
    """Parse price string to float."""
    if not price_text:
        return None
    
    # Remove currency symbols and whitespace
    price_text = price_text.replace('R$', '').replace('$', '').strip()
    
    # Handle Brazilian format: 1.234,56
    if ',' in price_text and '.' in price_text:
        # Remove thousands separator (dots)
        price_text = price_text.replace('.', '')
        # Replace comma with dot for decimal
        price_text = price_text.replace(',', '.')
    elif ',' in price_text:
        # Assume comma is decimal separator
        price_text = price_text.replace(',', '.')
    
    try:
        return float(price_text)
    except ValueError:
        return None


def calculate_discount(original: float, current: float) -> float:
    """Calculate discount percentage."""
    if original <= 0 or current >= original:
        return 0.0
    return round(((original - current) / original) * 100, 2)


def download_image(image_url: str, save_path: str) -> bool:
    """Download product image and save to file."""
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
    }
    
    try:
        response = requests.get(image_url, headers=headers, timeout=REQUEST_TIMEOUT, stream=True)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True
    except Exception as e:
        print(f"Error downloading image {image_url}: {str(e)}")
        return False

