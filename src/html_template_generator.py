"""
HTML Template-based image generator using Selenium
"""

import os
import time
import requests
import re
from typing import Dict, Optional
from pathlib import Path


def generate_from_html_template(product_data: Dict, output_path: str, temp_image_dir: str = "temp") -> bool:
    """
    Generate Instagram image from HTML template using Selenium.
    
    Args:
        product_data: Dictionary with product information
        output_path: Path to save generated image
        temp_image_dir: Directory for temporary files
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if Selenium is available
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from webdriver_manager.chrome import ChromeDriverManager
            SELENIUM_AVAILABLE = True
        except ImportError:
            print("Selenium not available. Using Pillow fallback for image generation...")
            # Fallback to Pillow-based generation
            return generate_with_pillow_fallback(product_data, output_path, temp_image_dir)
        
        # Ensure directories exist
        os.makedirs(temp_image_dir, exist_ok=True)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Get template path
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "template.html")
        if not os.path.exists(template_path):
            print(f"Template not found: {template_path}")
            return False
        
        # Read template
        with open(template_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Prepare product data
        title = product_data.get('title', 'Produto')
        image_url = product_data.get('image_url', '')
        current_price = product_data.get('current_price', 0.0)
        currency = product_data.get('currency', 'R$')
        
        # Format price
        from src.utils import format_price
        price_text = format_price(current_price, currency)
        # Extract just the number part (remove R$)
        price_number = price_text.replace(currency, '').strip()
        
        # Download product image and convert to base64 (more reliable)
        image_base64 = None
        if image_url:
            print(f"  Downloading product image: {image_url[:80]}...")
            product_image_path = download_image_for_html(image_url, temp_image_dir)
            if product_image_path and os.path.exists(product_image_path):
                # Convert image to base64
                import base64
                with open(product_image_path, 'rb') as img_file:
                    img_data = img_file.read()
                    # Detect image type
                    if product_image_path.lower().endswith('.png'):
                        mime_type = 'image/png'
                    elif product_image_path.lower().endswith('.webp'):
                        mime_type = 'image/webp'
                    else:
                        mime_type = 'image/jpeg'
                    
                    image_base64 = base64.b64encode(img_data).decode('utf-8')
                    image_data_url = f"data:{mime_type};base64,{image_base64}"
                    print(f"  [OK] Image downloaded and converted to base64")
            else:
                print(f"  [WARN] Could not download product image")
        
        # Replace template placeholders
        # Replace badge text (keep "ACHADO DO DIA")
        html_content = re.sub(
            r'<span><!-- DATA -->ACHADO DO DIA</span>',
            '<span>ACHADO DO DIA</span>',
            html_content
        )
        
        # Replace currency
        html_content = re.sub(
            r'<div class="currency"><!-- DATA -->R\$</div>',
            f'<div class="currency">{currency}</div>',
            html_content
        )
        
        # Replace price (note: price is now in .price class, not separate)
        html_content = re.sub(
            r'<div class="price"><!-- DATA -->99,90</div>',
            f'<div class="price">{price_number}</div>',
            html_content
        )
        
        # Replace product name
        # Truncate title if too long (max ~50 chars for better display)
        display_title = title[:50] + ('...' if len(title) > 50 else '')
        html_content = re.sub(
            r'<div class="productName"><!-- DATA -->Nome do Produto Aqui</div>',
            f'<div class="productName">{display_title}</div>',
            html_content
        )
        
        # Keep CTA text as is
        html_content = re.sub(
            r'<div class="cta"><!-- DATA -->Vale muito a pena</div>',
            '<div class="cta">Vale muito a pena</div>',
            html_content
        )
        
        # Ensure ribbon is inside post (fix positioning if needed)
        # The ribbon should already be inside .post, but let's make sure
        if '<div class="ribbon">' in html_content:
            # Verify ribbon is inside post div
            if not re.search(r'<div class="post"[^>]*>[\s\S]*?<div class="ribbon">', html_content):
                # If ribbon is outside, move it inside
                ribbon_match = re.search(r'<div class="ribbon">[^<]*</div>', html_content)
                if ribbon_match:
                    ribbon_html = ribbon_match.group(0)
                    html_content = re.sub(r'<div class="ribbon">[^<]*</div>', '', html_content)
                    # Insert after opening post div
                    html_content = re.sub(
                        r'(<div class="post"[^>]*>[\s\S]*?<div class="glow"></div>\s*<div class="noise"></div>)',
                        f'\\1\n    {ribbon_html}',
                        html_content
                    )
        
        # Replace product image with base64 data URL
        if image_data_url:
            # Replace the img tag in the product div with base64 image
            html_content = re.sub(
                r'(<div class="product">\s*<!-- DATA: substitua pela sua imagem \(png/jpg/webp\) -->\s*)<img[^>]*src="[^"]*"[^>]*>',
                f'\\1<img src="{image_data_url}" alt="Produto" crossorigin="anonymous" />',
                html_content,
                flags=re.DOTALL
            )
            print(f"  [OK] Image embedded in HTML template")
        else:
            print(f"  [WARN] No image to embed, using placeholder")
        
        # Load and embed logo (Clicou Economizou)
        logo_data_url = None
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
        logo_paths = [
            os.path.join(assets_dir, "logo.png"),
            os.path.join(assets_dir, "logo.jpg"),
            os.path.join(assets_dir, "logo.jpeg"),
        ]
        
        for logo_path in logo_paths:
            if os.path.exists(logo_path):
                try:
                    import base64
                    with open(logo_path, 'rb') as logo_file:
                        logo_data = logo_file.read()
                        # Detect image type
                        if logo_path.lower().endswith('.png'):
                            logo_mime = 'image/png'
                        else:
                            logo_mime = 'image/jpeg'
                        
                        logo_base64 = base64.b64encode(logo_data).decode('utf-8')
                        logo_data_url = f"data:{logo_mime};base64,{logo_base64}"
                        print(f"  [OK] Logo loaded and embedded: {os.path.basename(logo_path)}")
                        break
                except Exception as e:
                    print(f"  [WARN] Could not load logo: {str(e)}")
        
        # Replace logo src with base64 data URL
        if logo_data_url:
            html_content = re.sub(
                r'<div class="logo-container">\s*<img class="logo"[^>]*src="[^"]*"[^>]*>\s*</div>',
                f'<div class="logo-container"><img class="logo" src="{logo_data_url}" alt="Clicou Economizou" /></div>',
                html_content,
                flags=re.DOTALL
            )
        else:
            # Hide logo if not found
            html_content = re.sub(
                r'<div class="logo-container">\s*<img class="logo"[^>]*>\s*</div>',
                '<!-- Logo not found -->',
                html_content,
                flags=re.DOTALL
            )
            print(f"  [WARN] Logo not found in assets folder, hiding logo element")
        
        # Save temporary HTML file
        temp_html_path = os.path.join(temp_image_dir, f"temp_template_{int(time.time())}.html")
        with open(temp_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')  # Use new headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1200,1200')
        chrome_options.add_argument('--force-device-scale-factor=1')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-background-networking')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-breakpad')
        chrome_options.add_argument('--disable-component-extensions-with-background-pages')
        chrome_options.add_argument('--disable-features=TranslateUI')
        chrome_options.add_argument('--disable-ipc-flooding-protection')
        chrome_options.add_argument('--enable-features=NetworkService,NetworkServiceInProcess')
        chrome_options.add_argument('--force-color-profile=srgb')
        chrome_options.add_argument('--metrics-recording-only')
        chrome_options.add_argument('--mute-audio')
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--disable-sync')
        
        # Try to find Chrome binary in common locations (for Docker/Render)
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
                print(f"  Found Chrome binary at: {chrome_binary}")
                break
        
        if chrome_binary:
            chrome_options.binary_location = chrome_binary
        
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
        except Exception as e:
            print(f"  [ERROR] Failed to create Chrome driver: {str(e)}")
            raise
        
        try:
            # Load HTML file
            abs_html_path = os.path.abspath(temp_html_path)
            file_url = f"file:///{abs_html_path.replace(os.sep, '/')}"
            driver.get(file_url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "post"))
            )
            
            # Wait a bit more for images and fonts to load
            time.sleep(3)  # Give more time for fonts and images
            
            # Find the post element
            post_element = driver.find_element(By.ID, "post")
            
            # Execute JavaScript to ensure post is exactly 1080x1080 and centered
            driver.execute_script("""
                var post = document.getElementById('post');
                post.style.width = '1080px';
                post.style.height = '1080px';
                post.style.margin = '0 auto';
                post.style.padding = '0';
                post.style.position = 'relative';
                document.body.style.margin = '0';
                document.body.style.padding = '20px';
                document.body.style.display = 'flex';
                document.body.style.justifyContent = 'center';
                document.body.style.alignItems = 'center';
                document.body.style.minHeight = '100vh';
            """)
            
            # Wait a bit for style changes and rendering
            time.sleep(1)
            
            # Take screenshot of just the post element (this captures exactly 1080x1080)
            screenshot_path = output_path.replace('.jpg', '_temp.png')
            post_element.screenshot(screenshot_path)
            
            # Open and verify the screenshot
            from PIL import Image as PILImage
            img = PILImage.open(screenshot_path)
            
            # Verify size
            if img.size != (1080, 1080):
                print(f"  [WARN] Screenshot size is {img.size}, resizing to 1080x1080")
                img = img.resize((1080, 1080), PILImage.Resampling.LANCZOS)
            
            # Convert to RGB if needed (remove alpha channel)
            if img.mode == 'RGBA':
                # Create white background
                rgb_img = PILImage.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])
                img = rgb_img
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save as JPEG
            img.save(output_path, 'JPEG', quality=95)
            print(f"  [OK] Image saved: {output_path} ({img.size[0]}x{img.size[1]})")
            
            # Clean up temporary screenshot
            try:
                os.remove(screenshot_path)
            except:
                pass
            
            # Clean up temporary files
            try:
                os.remove(screenshot_path)
                os.remove(temp_html_path)
            except:
                pass
            
            return True
            
        finally:
            driver.quit()
    
    except Exception as e:
        print(f"Error generating from HTML template: {str(e)}")
        print("Falling back to Pillow-based generation...")
        import traceback
        traceback.print_exc()
        # Fallback to Pillow when Selenium fails (e.g., in cloud services)
        return generate_with_pillow_fallback(product_data, output_path, temp_image_dir)


def generate_with_pillow_fallback(product_data: Dict, output_path: str, temp_image_dir: str = "temp") -> bool:
    """
    Fallback image generation using Pillow (when Selenium is not available).
    Recreates the template design using Pillow to match template.html style.
    """
    try:
        print(f"  [FALLBACK] Starting Pillow-based image generation...")
        print(f"  [FALLBACK] Output path: {output_path}")
        print(f"  [FALLBACK] Product data: title={product_data.get('title', 'N/A')[:30]}, price={product_data.get('current_price', 0)}")
        
        from PIL import Image, ImageDraw
        from src.config import INSTAGRAM_IMAGE_SIZE
        from src.utils import format_price
        from src.image_generator import load_product_image, rounded_rectangle, draw_star, load_font_bold
        import os
        
        width, height = INSTAGRAM_IMAGE_SIZE
        print(f"  [FALLBACK] Image size: {width}x{height}")
        
        # Background matching template.html
        img = Image.new('RGB', (width, height), color="#F4F4F6")
        draw = ImageDraw.Draw(img)
        
        # Load product data
        title = product_data.get('title', 'Produto')
        image_url = product_data.get('image_url', '')
        current_price = product_data.get('current_price', 0.0)
        currency = product_data.get('currency', 'R$')
        
        # Format price
        price_text = format_price(current_price, currency)
        price_number = price_text.replace(currency, '').strip()
        print(f"  [FALLBACK] Price formatted: {price_text}")
        
        # Download and load product image
        product_img = None
        if image_url:
            print(f"  [FALLBACK] Loading product image from: {image_url[:80]}...")
            product_img = load_product_image(image_url, temp_image_dir)
            if product_img:
                print(f"  [FALLBACK] Product image loaded: {product_img.size}")
            else:
                print(f"  [FALLBACK] WARNING: Product image not loaded")
        else:
            print(f"  [FALLBACK] WARNING: No image URL provided")
        
        # 1. Ribbon "⚡ Oferta Relâmpago" (top left, rotated)
        # Simplified ribbon - yellow/orange banner
        ribbon_y = 160
        ribbon_points = [
            (-40, ribbon_y),
            (360, ribbon_y - 20),
            (360, ribbon_y + 30),
            (-40, ribbon_y + 50)
        ]
        draw.polygon(ribbon_points, fill="#FFCC00")
        draw.polygon(ribbon_points, outline="#000000", width=2)
        
        # Ribbon text - use font loader from image_generator
        font_ribbon = load_font_bold(30)
        draw.text((10, ribbon_y + 10), "⚡ OFERTA RELÂMPAGO", fill="#000000", font=font_ribbon)
        
        # 2. Badge "ACHADO DO DIA" (top left)
        badge_x, badge_y = 70, 70
        badge_width, badge_height = 350, 60
        rounded_rectangle(
            draw,
            [(badge_x, badge_y), (badge_x + badge_width, badge_y + badge_height)],
            radius=14,
            fill="#0F1014"
        )
        
        # Star icon (yellow square)
        star_size = 26
        star_x, star_y = badge_x + 16, badge_y + 17
        draw.rectangle(
            [(star_x, star_y), (star_x + star_size, star_y + star_size)],
            fill="#FFD400"
        )
        # Star symbol
        draw_star(draw, star_x + star_size//2, star_y + star_size//2, star_size//2, "#0F1014")
        
        # Badge text
        font_badge = load_font_bold(32)
        badge_text = "ACHADO DO DIA"
        bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
        text_x = star_x + star_size + 14
        text_y = badge_y + (badge_height - (bbox[3] - bbox[1])) // 2
        draw.text((text_x, text_y), badge_text, fill="#FFFFFF", font=font_badge)
        
        # 3. Product card (white, rounded) - matching template
        card_x, card_y = 60, 200
        card_width, card_height = 600, 600
        rounded_rectangle(
            draw,
            [(card_x, card_y), (card_x + card_width, card_y + card_height)],
            radius=40,
            fill="#FFFFFF"
        )
        
        # Product image inside card - fill the card much better without stretching
        if product_img:
            padding = 5  # Minimal padding to maximize image size
            max_img_width = card_width - (padding * 2)
            max_img_height = card_height - (padding * 2)
            # Calculate aspect ratios
            img_aspect = product_img.width / product_img.height
            card_aspect = max_img_width / max_img_height
            
            # Resize to fill available space while maintaining aspect ratio
            if img_aspect > card_aspect:
                # Image is wider - fit to width
                new_width = max_img_width
                new_height = int(max_img_width / img_aspect)
            else:
                # Image is taller - fit to height
                new_height = max_img_height
                new_width = int(max_img_height * img_aspect)
            
            product_img = product_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            img_x = card_x + (card_width - product_img.width) // 2
            img_y = card_y + (card_height - product_img.height) // 2
            img.paste(product_img, (img_x, img_y))
        
        # 4. Price panel (green, right side) - matching template
        price_x, price_y = 680, 220
        price_width, price_height = 380, 260
        rounded_rectangle(
            draw,
            [(price_x, price_y), (price_x + price_width, price_y + price_height)],
            radius=26,
            fill="#19B45A"
        )
        
        # Currency and price - use font loader
        font_currency = load_font_bold(44)
        font_price = load_font_bold(110)
        
        currency_x, currency_y = price_x + 34, price_y + 34
        draw.text((currency_x, currency_y), currency, fill="#FFFFFF", font=font_currency)
        price_text_x, price_text_y = price_x + 34, currency_y + 50
        draw.text((price_text_x, price_text_y), price_number, fill="#FFFFFF", font=font_price)
        
        # 5. Product name box (above CTA)
        product_name_x, product_name_y = 85, 840
        product_name_width, product_name_height = 600, 80
        # Truncate title if too long
        display_title = title[:50] + ('...' if len(title) > 50 else '')
        rounded_rectangle(
            draw,
            [(product_name_x, product_name_y), (product_name_x + product_name_width, product_name_y + product_name_height)],
            radius=22,
            fill="#FFFFFF"
        )
        
        font_product_name = load_font_bold(28)
        bbox_name = draw.textbbox((0, 0), display_title, font=font_product_name)
        # Handle text wrapping if needed
        name_text_x = product_name_x + 32
        name_text_y = product_name_y + (product_name_height - (bbox_name[3] - bbox_name[1])) // 2
        draw.text((name_text_x, name_text_y), display_title, fill="#121317", font=font_product_name)
        
        # 6. CTA "Vale muito a pena" (bottom left)
        cta_x, cta_y = 85, 920
        cta_width, cta_height = 300, 60
        rounded_rectangle(
            draw,
            [(cta_x, cta_y), (cta_x + cta_width, cta_y + cta_height)],
            radius=22,
            fill="#1A1B20"
        )
        
        font_cta = load_font_bold(34)
        cta_text = "Vale muito a pena"
        bbox = draw.textbbox((0, 0), cta_text, font=font_cta)
        cta_text_x = cta_x + (cta_width - (bbox[2] - bbox[0])) // 2
        cta_text_y = cta_y + (cta_height - (bbox[3] - bbox[1])) // 2
        draw.text((cta_text_x, cta_text_y), cta_text, fill="#FFFFFF", font=font_cta)
        
        # 7. Logo "Clicou Economizou" (bottom right)
        logo_paths = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "logo.png"),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "logo.jpg"),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "logo.jpeg"),
        ]
        
        logo_img = None
        for logo_path in logo_paths:
            if os.path.exists(logo_path):
                try:
                    logo_img = Image.open(logo_path)
                    print(f"  [FALLBACK] Logo loaded: {os.path.basename(logo_path)}")
                    break
                except Exception as e:
                    print(f"  [FALLBACK] Could not load logo: {str(e)}")
        
        if logo_img:
            # Resize logo to fit (height: 80px, maintain aspect ratio)
            logo_height = 80
            logo_aspect = logo_img.width / logo_img.height
            logo_width = int(logo_height * logo_aspect)
            logo_img = logo_img.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
            
            # Position in bottom right
            logo_x = width - logo_width - 50
            logo_y = height - logo_height - 50
            img.paste(logo_img, (logo_x, logo_y), logo_img if logo_img.mode == 'RGBA' else None)
        
        # Save image
        output_dir = os.path.dirname(output_path)
        print(f"  [FALLBACK] Creating output directory: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"  [FALLBACK] Saving image to: {output_path}")
        img.save(output_path, 'JPEG', quality=95)
        
        # Verify file was created
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"  [OK] Image generated with Pillow fallback: {output_path} ({file_size} bytes)")
            return True
        else:
            print(f"  [FAIL] Image file was not created at {output_path}")
            return False
        
    except Exception as e:
        print(f"  [FAIL] Error in Pillow fallback: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def download_image_for_html(image_url: str, temp_dir: str) -> Optional[str]:
    """
    Download product image to local file for HTML template.
    
    Args:
        image_url: URL of the product image
        temp_dir: Directory to save the image
        
    Returns:
        Path to downloaded image or None if failed
    """
    try:
        if not image_url:
            print("  [WARN] No image URL provided")
            return None
        
        os.makedirs(temp_dir, exist_ok=True)
        
        # Clean URL (remove query parameters that might cause issues)
        clean_url = image_url.split('?')[0]
        
        # Get filename from URL or generate one
        filename = os.path.basename(clean_url)
        if not filename or '.' not in filename:
            # Try to detect extension from URL
            if '.webp' in clean_url.lower():
                ext = '.webp'
            elif '.png' in clean_url.lower():
                ext = '.png'
            else:
                ext = '.jpg'
            filename = f"product_{int(time.time())}{ext}"
        else:
            # Ensure filename has valid extension
            if not any(filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                filename = filename.rsplit('.', 1)[0] + '.jpg'
        
        file_path = os.path.join(temp_dir, filename)
        
        # Download image with proper headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://www.mercadolivre.com.br/',
        }
        
        print(f"  Downloading from: {clean_url[:100]}...")
        response = requests.get(clean_url, headers=headers, timeout=15, stream=True, allow_redirects=True)
        response.raise_for_status()
        
        # Check content type
        content_type = response.headers.get('Content-Type', '')
        if 'image' not in content_type.lower():
            print(f"  [WARN] Response is not an image: {content_type}")
        
        # Save file
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # Verify file was created and has content
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            print(f"  [OK] Image saved: {file_path} ({os.path.getsize(file_path)} bytes)")
            return file_path
        else:
            print(f"  [FAIL] Image file is empty or not created")
            return None
    
    except requests.exceptions.RequestException as e:
        print(f"  [FAIL] Network error downloading image: {str(e)}")
        return None
    except Exception as e:
        print(f"  [FAIL] Error downloading image: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

