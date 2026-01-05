# Instagram Deal Post Generator

Automated tool to generate Instagram-ready posts from Mercado Livre product deals with affiliate links.

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
   **Note**: Selenium is required for reliable scraping of Mercado Livre pages (they use JavaScript rendering).
   If installation fails, make sure you have Chrome browser installed.

2. **Prepare Product Links**
   - Add Mercado Livre product URLs to `input/products.csv`
   - One URL per line (CSV format with header)

3. **Run the Generator**
   ```bash
   python main.py
   ```

4. **Find Results**
   - Generated images: `output/images/product_1.jpg`, `product_2.jpg`, etc.
   - Product data: `output/data/products.json`

## ✨ Features

- ✅ **Automatic product data extraction** from Mercado Livre
- ✅ **Internal ID system** (1, 2, 3, ...) for tracking
- ✅ **Instagram-optimized image generation** (1080x1080px)
- ✅ **Price comparison and discount calculation**
- ✅ **Affiliate link tracking** in JSON database
- ✅ **Skip already processed** products
- ✅ **Error handling** and progress tracking

## 📁 Project Structure

```
instagram-deal-generator/
├── src/
│   ├── config.py          # Configuration settings
│   ├── scraper.py         # Mercado Livre scraper
│   ├── image_generator.py # Instagram image creator
│   ├── database.py        # Product data storage
│   └── utils.py           # Helper functions
├── input/
│   └── products.csv       # Your product URLs
├── output/
│   ├── images/            # Generated Instagram images
│   └── data/              # Product database (JSON)
├── main.py                # Main execution script
└── requirements.txt       # Python dependencies
```

## ⚙️ Configuration

Edit `src/config.py` to customize:
- **Image dimensions**: `INSTAGRAM_IMAGE_SIZE` (default: 1080x1080)
- **Colors**: Modify `COLORS` dictionary
- **Font sizes**: Adjust font size constants
- **Scraping delays**: `SCRAPING_DELAY` (default: 3 seconds)

## 📖 Documentation

- **PLAN.md**: Detailed project architecture and planning
- **TECHNICAL_SPEC.md**: Technical implementation details
- **USAGE.md**: Complete usage guide and troubleshooting

## ⚠️ Important Notes

- **Respect Mercado Livre's terms of service** when scraping
- **Rate limiting**: Built-in delays prevent overwhelming servers
- **Affiliate links**: Ensure proper Mercado Livre affiliate program enrollment
- **Legal compliance**: Review local laws regarding web scraping

## 🐛 Troubleshooting

See `USAGE.md` for detailed troubleshooting guide. Common issues:
- CSV file not found → Check `input/products.csv` exists
- Scraping fails → Verify URLs are valid and internet connection works
- Font issues → Script auto-detects system fonts, works on Windows/Mac/Linux

## 📝 Example

Input CSV:
```csv
url
https://produto.mercadolivre.com.br/MLB-1234567890
```

Output:
- `output/images/product_1.jpg` - Instagram-ready image
- Product data in `output/data/products.json` with all details

