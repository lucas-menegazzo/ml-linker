# Instagram Deal Post Generator - Project Plan

## Overview
An application that processes Mercado Livre product links, extracts product information, and generates Instagram-ready images with deal information and affiliate links.

## Core Features

### 1. Product Link Management
- **Input**: Table/CSV file containing Mercado Livre product URLs
- **Internal ID System**: Auto-incrementing numeric IDs (1, 2, 3, ...)
- **Data Storage**: Database or JSON file to track processed products

### 2. Web Scraping Module
- Extract product information from Mercado Livre URLs:
  - Product image (high resolution)
  - Product title
  - Original price
  - Current/discounted price
  - Discount percentage (calculated)
  - Product URL (for affiliate link)

### 3. Image Generation Module
- Create Instagram-ready images (1080x1080px or 1080x1350px for posts)
- Include:
  - Product image
  - Product title
  - Price comparison (original vs. current)
  - Discount badge/percentage
  - Branding/watermark (optional)
  - Call-to-action text

### 4. Output Management
- Save generated images
- Store product data with internal IDs
- Export affiliate links mapping

## Technical Architecture

### Recommended Tech Stack

#### Option 1: Python (Recommended)
- **Web Scraping**: `requests` + `BeautifulSoup4` or `selenium` (if JS rendering needed)
- **Image Processing**: `Pillow` (PIL) for image manipulation
- **Data Management**: `pandas` for table handling, `sqlite3` or `json` for storage
- **Web Framework** (optional): `Flask` or `FastAPI` for web interface

#### Option 2: Node.js
- **Web Scraping**: `puppeteer` or `cheerio`
- **Image Processing**: `sharp` or `canvas`
- **Data Management**: `csv-parser`, `sqlite3` or `json`

### Project Structure
```
instagram-deal-generator/
├── src/
│   ├── __init__.py
│   ├── scraper.py          # Mercado Livre scraping logic
│   ├── image_generator.py  # Instagram image creation
│   ├── database.py         # Product data management
│   ├── utils.py            # Helper functions
│   └── config.py           # Configuration settings
├── input/
│   └── products.csv        # Input product links
├── output/
│   ├── images/             # Generated Instagram images
│   └── data/               # Product data JSON/DB
├── templates/
│   └── instagram_template.py  # Image template design
├── requirements.txt
├── README.md
└── main.py                 # Main execution script
```

## Workflow

### Step 1: Input Processing
1. Read product links from CSV/table
2. Assign internal ID to each product (starting from 1)
3. Check if product already processed (skip if exists)

### Step 2: Data Extraction
1. For each product link:
   - Fetch Mercado Livre product page
   - Extract:
     - Product image URL (main image)
     - Product title
     - Original price (if available)
     - Current price
     - Calculate discount percentage
   - Handle errors (404, network issues, etc.)

### Step 3: Image Generation
1. Download product image
2. Create Instagram canvas (1080x1080px or 1080x1350px)
3. Layout design:
   - Background/overlay
   - Product image (centered/resized)
   - Title text (truncated if too long)
   - Price comparison section
   - Discount badge
   - Optional: QR code for affiliate link
4. Apply styling (fonts, colors, shadows)
5. Export as PNG/JPG

### Step 4: Data Storage
1. Save product data with internal ID:
   - Internal ID
   - Original URL
   - Extracted data (title, prices, discount)
   - Generated image path
   - Timestamp

### Step 5: Output
1. Generated images in `output/images/`
2. Product database/JSON with affiliate link mapping
3. Summary report

## Implementation Details

### Mercado Livre Scraping
- **URL Pattern**: `https://produto.mercadolivre.com.br/MLB-XXXXXXXXX`
- **Key Elements to Extract**:
  - Image: `<img>` with class containing "ui-pdp-image"
  - Title: `<h1>` with class "ui-pdp-title"
  - Price: Elements with class containing "price" or "andes-money"
  - Original price: Look for "was" or "de" price indicators

### Image Design Considerations
- **Instagram Post Dimensions**: 
  - Square: 1080x1080px (1:1)
  - Portrait: 1080x1350px (4:5) - better for mobile
- **Text Readability**: 
  - High contrast text
  - Font size minimum 24px
  - Bold important information (discount, price)
- **Visual Hierarchy**:
  - Product image: 60-70% of canvas
  - Title: Top or bottom section
  - Price: Prominent, large font
  - Discount: Eye-catching badge

### Error Handling
- Invalid URLs
- Network timeouts
- Missing product data
- Image download failures
- Rate limiting (add delays between requests)

### Rate Limiting & Ethics
- Add delays between requests (2-5 seconds)
- Respect robots.txt
- Use proper User-Agent headers
- Consider Mercado Livre API if available

## Configuration Options

```python
# config.py example
INSTAGRAM_IMAGE_SIZE = (1080, 1080)  # or (1080, 1350)
IMAGE_QUALITY = 95
FONT_FAMILY = "Arial"  # or custom font path
COLORS = {
    "background": "#FFFFFF",
    "text": "#000000",
    "price_original": "#999999",
    "price_current": "#FF0000",
    "discount_badge": "#00FF00"
}
SCRAPING_DELAY = 3  # seconds between requests
```

## Future Enhancements
- Web UI for easier management
- Batch processing with progress bar
- Multiple template designs
- Auto-posting to Instagram (via API)
- Analytics tracking
- A/B testing different designs
- Support for multiple e-commerce platforms

## Dependencies (Python Example)

```
requests>=2.31.0
beautifulsoup4>=4.12.0
pillow>=10.0.0
pandas>=2.0.0
selenium>=4.15.0  # Optional, if JS rendering needed
```

## Getting Started Checklist
- [ ] Set up project structure
- [ ] Install dependencies
- [ ] Create Mercado Livre scraper
- [ ] Test product data extraction
- [ ] Design Instagram image template
- [ ] Implement image generation
- [ ] Create database/storage system
- [ ] Build main processing pipeline
- [ ] Add error handling
- [ ] Test with sample product links
- [ ] Create documentation

