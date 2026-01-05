"""
Database/storage module for product data
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from src.config import OUTPUT_DATA_FILE
from src.utils import ensure_directory


def load_products() -> Dict[int, Dict]:
    """
    Load existing products from JSON file.
    
    Returns:
        Dictionary mapping internal_id to product data
    """
    if not os.path.exists(OUTPUT_DATA_FILE):
        return {}
    
    try:
        with open(OUTPUT_DATA_FILE, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return {}
            data = json.loads(content)
            products = {}
            for product in data.get('products', []):
                products[product['internal_id']] = product
            return products
    except json.JSONDecodeError as e:
        # File is empty or corrupted, return empty dict
        return {}
    except Exception as e:
        print(f"Error loading products: {str(e)}")
        return {}


def save_product(internal_id: int, product_data: Dict, image_path: str) -> bool:
    """
    Save product data to JSON file.
    
    Args:
        internal_id: Internal product ID
        product_data: Scraped product data
        image_path: Path to generated image
        
    Returns:
        True if successful, False otherwise
    """
    ensure_directory(os.path.dirname(OUTPUT_DATA_FILE))
    
    # Load existing products
    existing_products = load_products()
    
    # Create product entry
    product_entry = {
        'internal_id': internal_id,
        'url': product_data.get('url'),
        'title': product_data.get('title'),
        'original_price': product_data.get('original_price'),
        'current_price': product_data.get('current_price'),
        'discount_percentage': product_data.get('discount_percentage', 0.0),
        'currency': product_data.get('currency', 'R$'),
        'image_path': image_path,
        'image_url': product_data.get('image_url'),
        'scraped_at': datetime.now().isoformat(),
        'affiliate_link': product_data.get('affiliate_link') or product_data.get('url')  # Use affiliate link if provided
    }
    
    # Update existing products
    existing_products[internal_id] = product_entry
    
    # Save to file
    try:
        data = {
            'products': list(existing_products.values()),
            'last_updated': datetime.now().isoformat()
        }
        
        with open(OUTPUT_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"Error saving product: {str(e)}")
        return False


def is_product_processed(internal_id: int) -> bool:
    """Check if product has already been processed."""
    products = load_products()
    return internal_id in products


def get_product_count() -> int:
    """Get total number of processed products."""
    products = load_products()
    return len(products)

