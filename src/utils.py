"""
Utility functions for product link parsing and helpers
"""

import pandas as pd
import re
from typing import List, Dict, Optional
import os


def parse_product_links(csv_path: str) -> List[Dict[str, any]]:
    """
    Parse product links from CSV file and assign internal IDs.
    
    Args:
        csv_path: Path to CSV file with product URLs
        
    Returns:
        List of dictionaries with 'id' and 'url' keys
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    try:
        products = []
        internal_id = 1
        
        # First, try reading with pandas
        try:
            df = pd.read_csv(csv_path, keep_default_na=False, on_bad_lines='skip')
            
            # Find URL column (case-insensitive)
            url_column = None
            for col in df.columns:
                if 'url' in col.lower() or 'link' in col.lower():
                    url_column = col
                    break
            
            if url_column is None:
                url_column = df.columns[0]
            
            for idx, row in df.iterrows():
                url = str(row[url_column]).strip()
                
                # Validate URL
                if not url or url.lower() in ['nan', 'none', ''] or url.lower() == 'url':
                    continue
                
                # Check if it's a Mercado Livre URL
                if 'mercadolivre.com.br' not in url.lower():
                    continue
                
                products.append({
                    'id': internal_id,
                    'url': url
                })
                internal_id += 1
        except Exception as e:
            print(f"Warning: Pandas CSV reading failed: {str(e)}, trying manual parsing...")
        
        # Fallback: read file directly line by line (more reliable for malformed CSV)
        # This ensures we catch all URLs even if CSV formatting is off
        with open(csv_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip header and empty lines
                if line_num == 1 or not line or line.lower() == 'url':
                    continue
                
                # Check if line contains a Mercado Livre URL
                if 'mercadolivre.com.br' in line.lower():
                    # Extract URL (might be the whole line or part of it)
                    # URLs typically start with http
                    if line.startswith('http'):
                        # Check if this URL is already added (avoid duplicates from pandas + manual)
                        url = line.split(',')[0].strip()  # Take first part if comma-separated
                        if not any(p['url'] == url for p in products):
                            products.append({
                                'id': internal_id,
                                'url': url
                            })
                            internal_id += 1
        
        return products
    
    except Exception as e:
        raise Exception(f"Error parsing CSV file: {str(e)}")


def validate_url(url: str) -> bool:
    """Validate if URL is a valid Mercado Livre product URL."""
    if not url:
        return False
    return 'mercadolivre.com.br' in url.lower() and ('produto' in url.lower() or 'MLB-' in url.upper())


def truncate_text(text: str, max_length: int) -> str:
    """Truncate text to max length and add ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def format_price(price: float, currency: str = "R$") -> str:
    """Format price as Brazilian Real."""
    return f"{currency} {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def calculate_discount_percentage(original: float, current: float) -> float:
    """Calculate discount percentage."""
    if original <= 0 or current >= original:
        return 0.0
    return round(((original - current) / original) * 100, 2)


def ensure_directory(path: str):
    """Ensure directory exists, create if it doesn't."""
    os.makedirs(path, exist_ok=True)

