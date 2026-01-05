"""
Configuration settings for Instagram Deal Generator
"""

# Instagram image dimensions
INSTAGRAM_IMAGE_SIZE = (1080, 1080)  # Square format
# Alternative: (1080, 1350) for portrait format

# Image quality (1-100)
IMAGE_QUALITY = 95

# Font settings
FONT_FAMILY = "arial"  # Will try to use system default
FONT_SIZE_TITLE = 42
FONT_SIZE_BANNER = 36
FONT_SIZE_PRICE_ORIGINAL = 28
FONT_SIZE_PRICE_CURRENT = 72  # Larger for prominence
FONT_SIZE_PRICE_CURRENCY = 32
FONT_SIZE_DISCOUNT = 38
FONT_SIZE_CTA = 32
FONT_SIZE_BRANDING = 24

# Color scheme - Inspired by template design
COLORS = {
    "background": "#FFFFFF",  # White background
    "background_dark": "#1A1A1A",  # Dark/black for alternative designs
    "text": "#000000",  # Black text
    "text_white": "#FFFFFF",  # White text
    "text_secondary": "#333333",
    "price_original": "#999999",  # Gray for original price
    "price_current": "#00AA00",  # Green for current price (matches template)
    "discount_badge_bg": "#FFD700",  # Yellow/Gold for badges
    "discount_badge_text": "#000000",  # Black text on yellow
    "banner_bg": "#000000",  # Black banner
    "banner_text": "#FFFFFF",  # White text on banner
    "banner_yellow": "#FFD700",  # Yellow banner
    "banner_yellow_text": "#000000",  # Black text on yellow
    "cta_button": "#FFD700",  # Yellow CTA button
    "cta_button_text": "#000000",  # Black text on CTA
    "branding_green": "#00AA00",  # Green for branding
}

# Layout settings
PADDING = 30
IMAGE_PADDING = 20
ELEMENT_GAP = 20
BANNER_HEIGHT = 80
PRODUCT_IMAGE_HEIGHT_RATIO = 0.55  # 55% of canvas height
BRANDING_HEIGHT = 60

# Scraping settings
SCRAPING_DELAY = 3  # seconds between requests
REQUEST_TIMEOUT = 10  # seconds
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# File paths
INPUT_CSV = "input/products.csv"
OUTPUT_IMAGES_DIR = "output/images"
OUTPUT_DATA_DIR = "output/data"
OUTPUT_DATA_FILE = "output/data/products.json"

# Text settings
MAX_TITLE_LINES = 2
TITLE_MAX_LENGTH = 60  # characters before truncation

