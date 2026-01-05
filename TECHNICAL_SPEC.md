# Technical Specification - Instagram Deal Generator

## Data Flow

```
CSV Input → Product Parser → Scraper → Data Extractor → Image Generator → Output
                ↓                ↓            ↓              ↓
            Internal ID      Mercado Livre  Product Data   Instagram Image
            Assignment        Web Page       Storage        (1080x1080px)
```

## Component Specifications

### 1. Product Link Parser (`src/utils.py`)

**Function**: `parse_product_links(csv_path)`
- Input: Path to CSV file
- Output: List of dictionaries with `{'id': int, 'url': str}`
- Logic:
  ```python
  - Read CSV using pandas
  - Assign sequential IDs starting from 1
  - Validate URLs (must contain 'mercadolivre.com.br')
  - Return list of product entries
  ```

### 2. Mercado Livre Scraper (`src/scraper.py`)

**Function**: `scrape_product(url)`
- Input: Mercado Livre product URL
- Output: Dictionary with product data
- Returns:
  ```python
  {
      'url': str,
      'title': str,
      'image_url': str,
      'original_price': float,
      'current_price': float,
      'discount_percentage': float,
      'currency': str  # 'R$'
  }
  ```

**Implementation Details**:
- Use `requests` to fetch HTML
- Parse with `BeautifulSoup4`
- Selectors (may need adjustment based on actual HTML):
  - Title: `h1.ui-pdp-title` or `h1[class*="title"]`
  - Image: `img[class*="ui-pdp-image"]` or `img[data-zoom]`
  - Price: Elements with `class*="price"` or `class*="andes-money"`
  - Original price: Look for strikethrough text or "de" prefix

**Error Handling**:
- Try-except for network errors
- Return `None` if product not found
- Log errors for debugging

### 3. Image Generator (`src/image_generator.py`)

**Function**: `generate_instagram_image(product_data, output_path)`
- Input: Product data dictionary, output file path
- Output: Saves image file, returns path

**Layout Design**:
```
┌─────────────────────────┐
│                         │
│    [Product Image]      │  ← 60% of canvas
│      (centered)         │
│                         │
├─────────────────────────┤
│  Product Title          │  ← 20% of canvas
│  (truncated if long)    │
├─────────────────────────┤
│  R$ 99,90               │  ← 20% of canvas
│  ~~R$ 149,90~~          │
│  [🔥 33% OFF]           │
└─────────────────────────┘
```

**Implementation Steps**:
1. Create canvas (1080x1080px) with white background
2. Download product image
3. Resize product image to fit (maintain aspect ratio)
4. Add product image to canvas (centered, top section)
5. Add title text (bottom section, wrapped if needed)
6. Add price section:
   - Original price (strikethrough, gray)
   - Current price (large, red/bold)
   - Discount badge (colored background, white text)
7. Add optional watermark/branding
8. Save as high-quality PNG/JPG

**Pillow Code Structure**:
```python
from PIL import Image, ImageDraw, ImageFont

# Create canvas
img = Image.new('RGB', (1080, 1080), color='white')
draw = ImageDraw.Draw(img)

# Load and paste product image
product_img = Image.open(product_image_path)
# Resize and paste logic

# Add text
font_title = ImageFont.truetype("arial.ttf", 48)
draw.text((x, y), title, fill='black', font=font_title)

# Add price
# ... price rendering logic

img.save(output_path, quality=95)
```

### 4. Database/Storage (`src/database.py`)

**Function**: `save_product(product_id, product_data, image_path)`
- Store in JSON file or SQLite database
- Structure:
  ```json
  {
    "products": [
      {
        "internal_id": 1,
        "url": "https://...",
        "title": "Product Name",
        "original_price": 149.90,
        "current_price": 99.90,
        "discount_percentage": 33.33,
        "image_path": "output/images/product_1.jpg",
        "scraped_at": "2024-01-01T12:00:00",
        "affiliate_link": "https://..." // if available
      }
    ]
  }
  ```

**Function**: `load_products()`
- Load existing products to avoid re-processing

### 5. Main Pipeline (`main.py`)

**Workflow**:
```python
1. Load configuration
2. Parse product links from CSV
3. Load existing products (to skip already processed)
4. For each product:
   a. Check if already processed → skip
   b. Scrape product data
   c. If successful:
      - Generate Instagram image
      - Save product data
      - Log success
   d. If failed:
      - Log error
      - Continue to next product
   e. Wait (delay to respect rate limits)
5. Generate summary report
6. Exit
```

## Mercado Livre Specific Notes

### URL Patterns
- Product: `https://produto.mercadolivre.com.br/MLB-XXXXXXXXX`
- Alternative: `https://www.mercadolivre.com.br/...`

### HTML Structure (Research Required)
- Mercado Livre uses dynamic content (React/Vue)
- May need `selenium` for JavaScript rendering
- Or use API endpoints if available
- Check network tab in browser DevTools for API calls

### Rate Limiting
- Add 3-5 second delay between requests
- Use proper User-Agent header
- Consider rotating User-Agents if needed
- Monitor for 429 (Too Many Requests) responses

## Image Design Specifications

### Dimensions
- **Square Post**: 1080x1080px (recommended for feed)
- **Portrait Post**: 1080x1350px (better engagement, mobile-friendly)

### Typography
- **Title**: 36-48px, bold, max 2 lines (truncate with "...")
- **Original Price**: 32px, strikethrough, gray (#999999)
- **Current Price**: 56-64px, bold, red (#FF0000) or green (#00AA00)
- **Discount Badge**: 40px, bold, white text on colored background

### Colors
- Background: White (#FFFFFF) or light gradient
- Text: Black (#000000) or dark gray (#333333)
- Price: Red for deals (#FF0000) or green (#00AA00)
- Discount badge: Red (#FF0000) or orange (#FF6600)

### Spacing
- Padding: 40px on all sides
- Gap between elements: 20-30px
- Product image padding: 20px

## Error Scenarios & Handling

| Scenario | Handling |
|----------|----------|
| Invalid URL | Skip, log error |
| Product not found (404) | Skip, log error |
| Network timeout | Retry once, then skip |
| Missing price data | Use placeholder or skip |
| Image download fails | Use placeholder image or skip |
| Image too small | Upscale or use as-is |
| Title too long | Truncate with "..." |

## Testing Strategy

1. **Unit Tests**:
   - URL validation
   - Price calculation
   - Image generation with mock data
   - Text truncation logic

2. **Integration Tests**:
   - Full pipeline with 1-2 sample products
   - Error handling scenarios

3. **Manual Testing**:
   - Test with real Mercado Livre products
   - Verify image quality
   - Check Instagram upload compatibility

## Performance Considerations

- **Parallel Processing**: Use `concurrent.futures` for multiple products (with rate limiting)
- **Caching**: Cache downloaded images to avoid re-downloading
- **Batch Processing**: Process in batches of 10-20 products
- **Progress Tracking**: Show progress bar for long operations

## Security & Legal

- **Terms of Service**: Review Mercado Livre's ToS for scraping
- **Affiliate Links**: Ensure proper affiliate program enrollment
- **Data Privacy**: Don't store unnecessary user data
- **Rate Limiting**: Always respect server resources

