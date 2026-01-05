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
            print("Selenium not available. Install with: pip install selenium webdriver-manager")
            return False
        
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
        
        # Save temporary HTML file
        temp_html_path = os.path.join(temp_image_dir, f"temp_template_{int(time.time())}.html")
        with open(temp_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1200,1200')  # Larger window to capture everything
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--force-device-scale-factor=1')
        
        # Create driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
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

