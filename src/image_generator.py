"""
Instagram image generator for product deals
Using exact templates from design references
"""

from PIL import Image, ImageDraw, ImageFont
import os
import platform
import requests
from io import BytesIO
from typing import Dict, Optional, List
from src.config import (
    INSTAGRAM_IMAGE_SIZE, IMAGE_QUALITY, COLORS, PADDING,
    IMAGE_PADDING, ELEMENT_GAP, PRODUCT_IMAGE_HEIGHT_RATIO,
    FONT_SIZE_TITLE, FONT_SIZE_BANNER, FONT_SIZE_PRICE_ORIGINAL, 
    FONT_SIZE_PRICE_CURRENT, FONT_SIZE_PRICE_CURRENCY, FONT_SIZE_DISCOUNT,
    FONT_SIZE_CTA, FONT_SIZE_BRANDING, MAX_TITLE_LINES, TITLE_MAX_LENGTH,
    BANNER_HEIGHT, BRANDING_HEIGHT
)
from src.utils import truncate_text, format_price, calculate_discount_percentage
from src.scraper import download_image, USER_AGENT, REQUEST_TIMEOUT


def rounded_rectangle(draw: ImageDraw.Draw, xy: list, radius: int, fill: str = None, outline: str = None, width: int = 1):
    """Draw rounded rectangle (compatible with older Pillow versions)."""
    # Handle both formats: [(x1, y1), (x2, y2)] or (x1, y1, x2, y2)
    if isinstance(xy, list) and len(xy) == 2:
        # Format: [(x1, y1), (x2, y2)]
        x1, y1 = xy[0]
        x2, y2 = xy[1]
        xy_tuple = (x1, y1, x2, y2)
    else:
        # Format: (x1, y1, x2, y2)
        xy_tuple = xy
    
    try:
        # Try new Pillow method first (Pillow 9.2.0+)
        if fill:
            draw.rounded_rectangle(xy_tuple, radius=radius, fill=fill)
        if outline:
            draw.rounded_rectangle(xy_tuple, radius=radius, outline=outline, width=width)
    except AttributeError:
        # Fallback: draw regular rectangle for older Pillow versions
        if fill:
            draw.rectangle(xy_tuple, fill=fill)
        if outline:
            draw.rectangle(xy_tuple, outline=outline, width=width)


def remove_background_simple(img: Image.Image) -> Image.Image:
    """
    Simple background removal - removes white/light backgrounds.
    Returns image with transparent background.
    """
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Convert to RGBA
    img_rgba = img.convert('RGBA')
    data = img_rgba.getdata()
    
    new_data = []
    for item in data:
        # If pixel is white/light (threshold), make it transparent
        r, g, b = item[0], item[1], item[2]
        # Calculate brightness
        brightness = (r + g + b) / 3
        
        # Threshold for white/light background removal
        if brightness > 240:  # Very light/white
            new_data.append((255, 255, 255, 0))  # Transparent
        elif brightness > 220:  # Light gray - partial transparency
            alpha = int(255 * (1 - (brightness - 220) / 20))
            new_data.append((r, g, b, alpha))
        else:
            new_data.append(item)
    
    img_rgba.putdata(new_data)
    return img_rgba


def generate_instagram_image(product_data: Dict, output_path: str, temp_image_dir: str = "temp", template_type: str = "achado") -> bool:
    """
    Generate Instagram-ready image using HTML template.
    
    Args:
        product_data: Dictionary with product information
        output_path: Path to save generated image
        temp_image_dir: Directory for temporary downloaded images
        template_type: Type of template to use (not used, always uses HTML template)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Always use HTML template
        from src.html_template_generator import generate_from_html_template
        return generate_from_html_template(product_data, output_path, temp_image_dir)
    
    except Exception as e:
        print(f"Error generating image: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def generate_achado_template(product_data: Dict, output_path: str, temp_image_dir: str) -> bool:
    """
    Generate "ACHADO DO DIA" template - light background, product centered.
    """
    width, height = INSTAGRAM_IMAGE_SIZE
    
    # Light grey background with texture
    img = Image.new('RGB', (width, height), color="#F5F5F5")
    draw = ImageDraw.Draw(img)
    
    # Add subtle diagonal texture
    for i in range(0, width + height, 20):
        draw.line([(i, 0), (i - height, height)], fill="#E8E8E8", width=1)
    
    # Load fonts
    font_banner = load_font_bold(42)
    font_price_currency = load_font_bold(28)
    font_price_amount = load_font_bold(64)
    font_bottom_banner = load_font_bold(32)
    
    current_y = 0
    
    # 1. Top Banner - "ACHADO DO DIA" with yellow star
    banner_height = 90
    draw.rectangle(
        [(0, current_y), (width, current_y + banner_height)],
        fill=COLORS['banner_bg']
    )
    
    # Yellow star icon (simplified as text/emoji or shape)
    star_x = 40
    star_y = current_y + (banner_height - 30) // 2
    # Draw star shape
    star_size = 25
    draw_star(draw, star_x, star_y, star_size, COLORS['discount_badge_bg'])
    
    # Banner text
    banner_text = "ACHADO DO DIA"
    bbox = draw.textbbox((0, 0), banner_text, font=font_banner)
    text_width = bbox[2] - bbox[0]
    text_x = (width - text_width) // 2
    text_y = current_y + (banner_height - (bbox[3] - bbox[1])) // 2
    draw.text((text_x, text_y), banner_text, fill=COLORS['banner_text'], font=font_banner)
    
    current_y += banner_height + 30
    
    # 2. Product Image (centered, prominent)
    image_url = product_data.get('image_url')
    product_img = None
    img_y = current_y
    
    if image_url:
        product_img = load_product_image(image_url, temp_image_dir)
        if product_img:
            # Resize to fit
            max_width = width - (PADDING * 2)
            max_height = int(height * 0.5)
            product_img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Center image
            x_offset = (width - product_img.width) // 2
            y_offset = img_y
            
            # Paste image (with shadow effect if possible)
            try:
                shadow_offset = 5
                shadow_img = Image.new('RGBA', (product_img.width + shadow_offset * 2, product_img.height + shadow_offset * 2), (0, 0, 0, 30))
                img.paste(shadow_img, (x_offset - shadow_offset, y_offset + shadow_offset), shadow_img)
            except:
                pass
            
            # Convert to RGB if needed for pasting
            if product_img.mode == 'RGBA':
                # Create white background for transparency
                bg = Image.new('RGB', product_img.size, (245, 245, 245))
                bg.paste(product_img, mask=product_img.split()[3])
                product_img = bg
            
            img.paste(product_img, (x_offset, y_offset))
            
            img_y += product_img.height + 20
    
    # 3. Price Tag (green, to the right of product or below)
    current_price = product_data.get('current_price')
    if current_price:
        price_text = format_price(current_price, product_data.get('currency', 'R$'))
        currency_part = 'R$'
        amount_part = price_text.replace('R$', '').strip()
        
        # Green price tag (irregular shape)
        tag_x = width - 200
        tag_y = img_y - 100 if product_img else current_y + 50
        
        # Draw green tag with fold effect
        tag_width = 180
        tag_height = 100
        
        # Main tag body (rounded rectangle)
        rounded_rectangle(
            draw,
            [(tag_x, tag_y), (tag_x + tag_width, tag_y + tag_height)],
            radius=8,
            fill=COLORS['price_current']
        )
        
        # Fold effect (small triangle)
        fold_points = [
            (tag_x + tag_width - 20, tag_y),
            (tag_x + tag_width, tag_y),
            (tag_x + tag_width - 10, tag_y + 15)
        ]
        draw.polygon(fold_points, fill="#008800")
        
        # Price text on tag
        currency_bbox = draw.textbbox((0, 0), currency_part, font=font_price_currency)
        currency_x = tag_x + 15
        currency_y = tag_y + 10
        draw.text((currency_x, currency_y), currency_part, fill=COLORS['text_white'], font=font_price_currency)
        
        amount_bbox = draw.textbbox((0, 0), amount_part, font=font_price_amount)
        amount_x = tag_x + 15
        amount_y = currency_y + (currency_bbox[3] - currency_bbox[1]) + 5
        draw.text((amount_x, amount_y), amount_part, fill=COLORS['text_white'], font=font_price_amount)
    
    # 4. Bottom Banner - "Vale muito a pena"
    bottom_banner_y = height - 80
    bottom_banner_height = 60
    draw.rectangle(
        [(0, bottom_banner_y), (width, bottom_banner_y + bottom_banner_height)],
        fill=COLORS['banner_bg']
    )
    
    bottom_text = "Vale muito a pena"
    bbox = draw.textbbox((0, 0), bottom_text, font=font_bottom_banner)
    text_width = bbox[2] - bbox[0]
    text_x = (width - text_width) // 2
    text_y = bottom_banner_y + (bottom_banner_height - (bbox[3] - bbox[1])) // 2
    draw.text((text_x, text_y), bottom_text, fill=COLORS['banner_text'], font=font_bottom_banner)
    
    # 5. Decorative dots in corners
    draw_decorative_dots(draw, width, height)
    
    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, 'JPEG', quality=IMAGE_QUALITY)
    return True


def wrap_text(draw: ImageDraw.Draw, text: str, font, max_width: int) -> List[str]:
    """Wrap text to fit within max_width."""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        text_width = bbox[2] - bbox[0]
        
        if text_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines if lines else [text]


def generate_relampago_template(product_data: Dict, output_path: str, temp_image_dir: str) -> bool:
    """
    Generate "OFERTA RELÂMPAGO" template - like Adidas template:
    - Pink banner on top with "OFERTA RELÂMPAGO"
    - Product title above product
    - Product centered
    - Price below product in black banner
    - "CLICOU ECONOMIZOU" logo at bottom
    """
    width, height = INSTAGRAM_IMAGE_SIZE
    
    # Light background (like Adidas example)
    img = Image.new('RGB', (width, height), color="#F5F5F5")
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    font_banner = load_font_bold(42)
    font_title = load_font_bold(48)
    font_price = load_font_bold(64)
    font_branding = load_font_bold(24)
    
    current_y = 0
    
    # 1. Top Banner - "OFERTA RELÂMPAGO" (pink banner like Adidas)
    banner_height = 90
    banner_color = "#FFB6C1"  # Light pink
    
    draw.rectangle(
        [(0, current_y), (width, current_y + banner_height)],
        fill=banner_color
    )
    
    # Flame icon
    flame_x = 30
    flame_y = current_y + 25
    draw_flame_icon(draw, flame_x, flame_y, 30, "#FF6600")
    
    # Banner text "OFERTA RELÂMPAGO" in red
    banner_text = "OFERTA RELÂMPAGO"
    bbox = draw.textbbox((0, 0), banner_text, font=font_banner)
    text_x = flame_x + 50
    text_y = current_y + (banner_height - (bbox[3] - bbox[1])) // 2
    draw.text((text_x, text_y), banner_text, fill="#FF0000", font=font_banner)
    
    current_y += banner_height + 30
    
    # 2. Product Title (above product, like "ADIDAS FEMININO")
    title = product_data.get('title', 'Produto')
    title = truncate_text(title, 60)  # Limit title length
    
    # Wrap title if needed
    title_lines = wrap_text(draw, title, font_title, width - (PADDING * 2))
    title_lines = title_lines[:2]  # Max 2 lines
    
    title_y = current_y
    for line in title_lines:
        bbox = draw.textbbox((0, 0), line, font=font_title)
        text_width = bbox[2] - bbox[0]
        text_x = (width - text_width) // 2
        draw.text((text_x, title_y), line, fill="#000000", font=font_title)
        title_y += (bbox[3] - bbox[1]) + 10
    
    current_y = title_y + 40
    
    # 3. Product Image (centered, prominent)
    image_url = product_data.get('image_url')
    product_img = None
    img_y = current_y
    
    if image_url:
        product_img = load_product_image(image_url, temp_image_dir)
        if product_img:
            # Remove background
            product_img = remove_background_simple(product_img)
            
            # Resize to fit (large, centered)
            max_width = int(width * 0.65)
            max_height = int(height * 0.45)
            product_img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Center position
            img_x = (width - product_img.width) // 2
            img_y = current_y
            
            # Paste with shadow
            shadow_offset = 15
            shadow_img = Image.new('RGBA', (product_img.width + shadow_offset * 2, product_img.height + shadow_offset * 2), (0, 0, 0, 60))
            try:
                img.paste(shadow_img, (img_x - shadow_offset, img_y + shadow_offset), shadow_img)
            except:
                pass
            
            # Paste product image
            if product_img.mode == 'RGBA':
                img.paste(product_img, (img_x, img_y), product_img.split()[3])
            else:
                img.paste(product_img, (img_x, img_y))
            
            current_y = img_y + product_img.height + 30
    
    # 4. Price Banner (below product, black banner like example)
    current_price = product_data.get('current_price')
    if current_price:
        price_text = format_price(current_price, product_data.get('currency', 'R$'))
        price_display = f"Por: {price_text}"
        
        # Black banner at bottom
        price_banner_y = height - 100
        price_banner_height = 80
        price_banner_width = width
        
        draw.rectangle(
            [(0, price_banner_y), (price_banner_width, price_banner_y + price_banner_height)],
            fill="#000000"
        )
        
        # Price text centered
        price_bbox = draw.textbbox((0, 0), price_display, font=font_price)
        price_text_x = (width - (price_bbox[2] - price_bbox[0])) // 2
        price_text_y = price_banner_y + (price_banner_height - (price_bbox[3] - price_bbox[1])) // 2
        draw.text((price_text_x, price_text_y), price_display, fill=COLORS['text_white'], font=font_price)
    
    # 5. Branding - "CLICOU ECONOMIZOU" logo (bottom center, smaller)
    branding_y = height - 45
    branding_x = (width - 280) // 2
    
    # Green link icon with arrow
    draw_link_icon(draw, branding_x, branding_y, 22, COLORS['price_current'])
    
    # Branding text
    text_x = branding_x + 30
    text_y = branding_y - 3
    
    # "CLICOU" in white
    clicou_text = "CLICOU"
    bbox = draw.textbbox((0, 0), clicou_text, font=font_branding)
    draw.text((text_x, text_y), clicou_text, fill=COLORS['text_white'], font=font_branding)
    
    # "ECONOMIZOU" in green
    economizou_text = "ECONOMIZOU"
    bbox2 = draw.textbbox((0, 0), economizou_text, font=font_branding)
    draw.text((text_x, text_y + (bbox[3] - bbox[1]) + 2), economizou_text, fill=COLORS['price_current'], font=font_branding)
    
    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, 'JPEG', quality=IMAGE_QUALITY)
    return True


def draw_star(draw: ImageDraw.Draw, x: int, y: int, size: int, color: str):
    """Draw a 5-pointed star."""
    import math
    points = []
    for i in range(10):
        angle = math.pi / 2 + (i * math.pi / 5)
        r = size if i % 2 == 0 else size / 2
        px = x + r * math.cos(angle)
        py = y + r * math.sin(angle)
        points.append((px, py))
    draw.polygon(points, fill=color)


def draw_flame_icon(draw: ImageDraw.Draw, x: int, y: int, size: int, color: str):
    """Draw a simplified flame icon."""
    # Flame shape (simplified as teardrop)
    points = [
        (x, y + size),
        (x + size // 2, y),
        (x + size, y + size // 3),
        (x + size * 0.7, y + size)
    ]
    draw.polygon(points, fill=color)


def draw_arrow_right(draw: ImageDraw.Draw, x: int, y: int, size: int, color: str):
    """Draw a right-pointing arrow."""
    points = [
        (x, y),
        (x + size, y + size // 2),
        (x, y + size)
    ]
    draw.polygon(points, fill=color)


def draw_clock_icon(draw: ImageDraw.Draw, x: int, y: int, size: int, color: str):
    """Draw a simplified clock icon."""
    # Clock circle
    draw.ellipse([(x, y), (x + size, y + size)], outline=color, width=2)
    # Clock hands
    center_x, center_y = x + size // 2, y + size // 2
    draw.line([(center_x, center_y), (center_x, center_y - size // 3)], fill=color, width=2)
    draw.line([(center_x, center_y), (center_x + size // 4, center_y)], fill=color, width=2)


def draw_link_icon(draw: ImageDraw.Draw, x: int, y: int, size: int, color: str):
    """Draw a link icon with arrow."""
    # Two interlocking circles
    circle1 = [(x, y), (x + size, y + size)]
    circle2 = [(x + size // 2, y), (x + size * 1.5, y + size)]
    draw.ellipse(circle1, outline=color, width=3)
    draw.ellipse(circle2, outline=color, width=3)
    # Arrow on right
    arrow_x = x + size * 1.3
    arrow_y = y + size // 2
    points = [
        (arrow_x, arrow_y),
        (arrow_x + size // 3, arrow_y - size // 6),
        (arrow_x + size // 3, arrow_y + size // 6)
    ]
    draw.polygon(points, fill=color)


def draw_decorative_dots(draw: ImageDraw.Draw, width: int, height: int):
    """Draw decorative dots in corners."""
    dot_size = 8
    dot_spacing = 15
    
    # Top left
    for i in range(3):
        for j in range(3):
            x = PADDING + (i * dot_spacing)
            y = 120 + (j * dot_spacing)
            color = COLORS['price_current'] if (i + j) % 2 == 0 else COLORS['text_white']
            draw.rectangle([(x, y), (x + dot_size, y + dot_size)], fill=color)
    
    # Top right
    for i in range(3):
        for j in range(3):
            x = width - PADDING - dot_size - (i * dot_spacing)
            y = 120 + (j * dot_spacing)
            color = COLORS['price_current'] if (i + j) % 2 == 0 else COLORS['text_white']
            draw.rectangle([(x, y), (x + dot_size, y + dot_size)], fill=color)


def load_product_image(image_url: str, temp_dir: str) -> Optional[Image.Image]:
    """Download and load product image."""
    os.makedirs(temp_dir, exist_ok=True)
    
    filename = os.path.basename(image_url.split('?')[0])
    if not filename or '.' not in filename:
        filename = 'product_image.jpg'
    
    temp_path = os.path.join(temp_dir, filename)
    
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
    }
    
    try:
        response = requests.get(image_url, headers=headers, timeout=REQUEST_TIMEOUT, stream=True)
        response.raise_for_status()
        
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        img = Image.open(temp_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        return img
    
    except Exception as e:
        print(f"Error loading product image: {str(e)}")
        return None


def load_font(size: int):
    """Load regular font with fallback options."""
    font_paths = get_font_paths()
    
    for font_path in font_paths:
        try:
            if os.path.exists(font_path):
                return ImageFont.truetype(font_path, size)
        except:
            continue
    
    try:
        return ImageFont.truetype("arial.ttf", size)
    except:
        return ImageFont.load_default()


def load_font_bold(size: int):
    """Load bold font with fallback options."""
    font_paths = get_font_paths(bold=True)
    
    for font_path in font_paths:
        try:
            if os.path.exists(font_path):
                return ImageFont.truetype(font_path, size)
        except:
            continue
    
    return load_font(size)


def get_font_paths(bold: bool = False):
    """Get font paths based on OS."""
    if platform.system() == "Windows":
        if bold:
            return [
                "C:/Windows/Fonts/arialbd.ttf",
                "C:/Windows/Fonts/calibrib.ttf",
                "C:/Windows/Fonts/arial.ttf",
            ]
        return [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "C:/Windows/Fonts/tahoma.ttf",
        ]
    elif platform.system() == "Darwin":  # macOS
        if bold:
            return [
                "/Library/Fonts/Arial Bold.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
            ]
        return [
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf",
        ]
    else:  # Linux
        if bold:
            return [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            ]
        return [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
