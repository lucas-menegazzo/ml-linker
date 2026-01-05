# Usage Guide

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Prepare Product Links

Edit `input/products.csv` and add Mercado Livre product URLs, one per line:

```csv
url
https://produto.mercadolivre.com.br/MLB-1234567890
https://produto.mercadolivre.com.br/MLB-0987654321
```

**Note**: The CSV can have a header row (recommended) or just URLs. The script will automatically detect the URL column.

### 3. Run the Generator

```bash
python main.py
```

### 4. Find Your Results

- **Generated Images**: `output/images/product_1.jpg`, `product_2.jpg`, etc.
- **Product Data**: `output/data/products.json` (contains all product information and affiliate links)

## How It Works

1. **Reads** product links from `input/products.csv`
2. **Assigns** internal IDs (1, 2, 3, ...) to each product
3. **Scrapes** product data from Mercado Livre:
   - Product image
   - Title
   - Original price
   - Current price
   - Calculates discount percentage
4. **Generates** Instagram-ready images (1080x1080px) with:
   - Product image
   - Title
   - Price comparison
   - Discount badge
5. **Saves** everything with tracking for future runs

## Features

- ✅ **Automatic ID Assignment**: Each product gets a unique internal ID
- ✅ **Skip Already Processed**: Won't re-process products you've already done
- ✅ **Error Handling**: Continues processing even if some products fail
- ✅ **Rate Limiting**: Respects Mercado Livre servers with delays
- ✅ **Progress Tracking**: Shows progress as it processes

## Configuration

Edit `src/config.py` to customize:

- **Image Size**: Change `INSTAGRAM_IMAGE_SIZE` (default: 1080x1080)
- **Colors**: Modify `COLORS` dictionary
- **Fonts**: Adjust font sizes
- **Scraping Delay**: Change `SCRAPING_DELAY` (default: 3 seconds)

## Troubleshooting

### "No products found in CSV file!"
- Make sure `input/products.csv` exists
- Check that URLs are in the CSV
- Verify URLs contain "mercadolivre.com.br"

### "Failed to scrape product data" or "No product found"

**Common Issue**: Mercado Livre pages are JavaScript-rendered, so the basic HTML scraper might not work for all URLs.

**Solutions**:

1. **Try the URL again** - Sometimes it works on retry
2. **Use Selenium** (recommended for reliable scraping):
   ```bash
   pip install selenium webdriver-manager
   ```
   The scraper will automatically use Selenium as a fallback if available.

3. **Check the URL format**:
   - Standard format: `https://produto.mercadolivre.com.br/MLB-XXXXXXXXX`
   - Alternative: `https://www.mercadolivre.com.br/.../p/MLBXXXXXXXXX`
   - Both should work, but `/p/` URLs might need Selenium

4. **Verify the product exists** - Make sure the URL is accessible in your browser

5. **Check your internet connection** - Network issues can cause failures

### Images not generating
- Check that Pillow is installed correctly
- Verify product images are downloading (check `temp/` folder)
- Look for error messages in the console

### Font issues
- The script tries to use system fonts automatically
- If fonts look wrong, you can modify `load_font()` in `src/image_generator.py`

## Example Output

After running, you'll have:

```
output/
├── images/
│   ├── product_1.jpg
│   ├── product_2.jpg
│   └── product_3.jpg
└── data/
    └── products.json
```

The `products.json` file contains:
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
      "scraped_at": "2024-01-01T12:00:00"
    }
  ]
}
```

## Adding Affiliate Links

The product URL is stored as the affiliate link by default. To use custom affiliate links:

1. Edit `src/database.py`
2. Modify the `save_product()` function to replace the URL with your affiliate link format
3. Or manually edit `output/data/products.json` after processing

## Tips

- Process products in batches (10-20 at a time) to avoid rate limiting
- Check generated images before posting to ensure quality
- Keep the `products.json` file backed up - it tracks what you've processed
- Delete products from JSON if you want to re-process them

