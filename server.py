"""
Flask server for web interface
"""

from flask import Flask, render_template, request, jsonify, send_file, send_from_directory, Response
from flask_cors import CORS
import os
import json
from src.config import INPUT_CSV, OUTPUT_IMAGES_DIR
from src.utils import parse_product_links, ensure_directory
from src.scraper import scrape_product
from src.image_generator import generate_instagram_image
import re

app = Flask(__name__)
CORS(app)

# Serve static files
@app.route('/')
def index():
    return send_file('web_interface.html')

@app.route('/images/<filename>')
def serve_image(filename):
    """Serve generated images."""
    try:
        return send_from_directory(OUTPUT_IMAGES_DIR, filename)
    except:
        return jsonify({'error': 'Image not found'}), 404

@app.route('/api/test', methods=['GET'])
def test():
    """Test endpoint."""
    return jsonify({
        'status': 'ok',
        'csv_exists': os.path.exists(INPUT_CSV),
        'images_dir_exists': os.path.exists(OUTPUT_IMAGES_DIR),
        'images_count': len([f for f in os.listdir(OUTPUT_IMAGES_DIR) if f.endswith('.jpg')]) if os.path.exists(OUTPUT_IMAGES_DIR) else 0
    })

@app.route('/api/csv', methods=['GET'])
def get_csv():
    """Get current CSV content."""
    try:
        if os.path.exists(INPUT_CSV):
            with open(INPUT_CSV, 'r', encoding='utf-8') as f:
                return f.read()
        return 'url\n'
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/csv', methods=['POST'])
def update_csv():
    """Update CSV file."""
    try:
        data = request.json
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Read existing CSV
        lines = []
        if os.path.exists(INPUT_CSV):
            with open(INPUT_CSV, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        
        # Add new URL if not exists
        if url + '\n' not in lines:
            # Check if header exists
            if not lines or 'url' not in lines[0].lower():
                lines.insert(0, 'url\n')
            lines.append(url + '\n')
        
        # Write back
        with open(INPUT_CSV, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        return jsonify({'success': True, 'message': 'URL adicionada com sucesso'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate', methods=['POST'])
def generate():
    """Generate image for product."""
    try:
        data = request.json
        product_url = data.get('product_url', '').strip()
        affiliate_link = data.get('affiliate_link', '').strip()
        
        if not product_url:
            return jsonify({'error': 'Product URL is required'}), 400
        
        print(f"[API] Scraping product: {product_url}")
        
        # Scrape product
        product_data = scrape_product(product_url)
        if not product_data:
            print("[API] Failed to scrape product data")
            return jsonify({'error': 'Failed to scrape product data. Verifique se o link está correto e tente novamente.'}), 500
        
        print(f"[API] Product scraped: {product_data.get('title', 'N/A')[:50]}")
        
        # Update affiliate link
        product_data['affiliate_link'] = affiliate_link
        
        # Generate image
        # Find next available ID
        try:
            products = parse_product_links(INPUT_CSV)
            next_id = len(products) + 1
        except:
            next_id = 1
        
        image_filename = f"product_{next_id}.jpg"
        # Use absolute path
        image_path = os.path.abspath(os.path.join(OUTPUT_IMAGES_DIR, image_filename))
        
        # Ensure directory exists
        ensure_directory(OUTPUT_IMAGES_DIR)
        
        print(f"[API] Generating image: {image_path}")
        print(f"[API] Product data: title={product_data.get('title')}, price={product_data.get('current_price')}")
        
        if generate_instagram_image(product_data, image_path):
            print(f"[API] Image generated successfully: {image_path}")
            # Wait a bit to ensure file is written
            import time
            time.sleep(0.5)
            
            if os.path.exists(image_path):
                file_size = os.path.getsize(image_path)
                print(f"[API] Image file exists, size: {file_size} bytes")
                try:
                    # Try to send file
                    return send_file(
                        image_path, 
                        mimetype='image/jpeg',
                        as_attachment=False,
                        download_name=image_filename
                    )
                except Exception as e:
                    print(f"[API] Error sending file: {str(e)}")
                    # Fallback: read and send as response
                    with open(image_path, 'rb') as f:
                        image_data = f.read()
                    return Response(
                        image_data,
                        mimetype='image/jpeg',
                        headers={'Content-Disposition': f'inline; filename={image_filename}'}
                    )
            else:
                print(f"[API] ERROR: Image file does not exist at {image_path}")
                return jsonify({'error': f'Image file was not created at {image_path}'}), 500
        else:
            print("[API] Failed to generate image - function returned False")
            return jsonify({'error': 'Failed to generate image. Verifique se o produto tem título e preço válidos.'}), 500
            
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        print(f"[API] Error: {error_msg}")
        return jsonify({'error': f'Erro ao gerar imagem: {error_msg}'}), 500

@app.route('/api/affiliate-link', methods=['POST'])
def generate_affiliate_link():
    """Generate affiliate link from product URL and social code."""
    try:
        data = request.json
        product_url = data.get('product_url', '').strip()
        social_code = data.get('social_code', '').strip()
        
        if not product_url or not social_code:
            return jsonify({'error': 'Product URL and social code are required'}), 400
        
        # Extract product ID
        product_id = extract_product_id(product_url)
        if not product_id:
            return jsonify({'error': 'Could not extract product ID from URL'}), 400
        
        # Generate affiliate link
        affiliate_link = generate_affiliate_link_from_social(product_url, social_code, product_id)
        
        return jsonify({'affiliate_link': affiliate_link})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def extract_product_id(url):
    """Extract product ID from Mercado Livre URL."""
    # Try multiple patterns
    patterns = [
        r'MLB-(\d+)',  # MLB-4049279695
        r'MLB(\d+)',   # MLB4049279695
        r'/p/MLB-?(\d+)',  # /p/MLB4049279695
        r'produto\.mercadolivre\.com\.br/MLB-?(\d+)',  # produto.mercadolivre.com.br/MLB-4049279695
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            # Extract just the number part
            product_number = match.group(1) if match.lastindex else match.group(0).replace('MLB', '').replace('-', '')
            # Return in format MLB-XXXXXXXXX
            return f"MLB-{product_number}"
    
    return None

def generate_affiliate_link_from_social(product_url, social_code, product_id):
    """
    Generate affiliate link by combining social code with product.
    
    Mercado Livre affiliate pattern:
    - Social code base: https://www.mercadolivre.com.br/social/USERNAME?params...
    - Product link: https://produto.mercadolivre.com.br/MLB-XXXXX-...
    - Affiliate link: Combine both, typically redirecting through social code
    """
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
    
    # Parse social code URL
    social_parsed = urlparse(social_code)
    social_params = parse_qs(social_parsed.query)
    
    # Clean product ID (remove MLB- prefix variations)
    clean_product_id = product_id.replace('MLB-', '').replace('MLB', '')
    
    # Mercado Livre pattern: add product reference to social code
    # The ref parameter in social code is the tracking, we keep it
    # Add product ID as mlm parameter or in the ref
    social_params['mlm'] = [clean_product_id]
    
    # Rebuild URL
    new_query = urlencode(social_params, doseq=True)
    affiliate_link = urlunparse((
        social_parsed.scheme,
        social_parsed.netloc,
        social_parsed.path,
        social_parsed.params,
        new_query,
        social_parsed.fragment
    ))
    
    return affiliate_link

if __name__ == '__main__':
    # Ensure directories exist
    ensure_directory(OUTPUT_IMAGES_DIR)
    ensure_directory(os.path.dirname(INPUT_CSV))
    
    # Get local IP address
    import socket
    def get_local_ip():
        try:
            # Connect to a remote address to get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "localhost"
    
    local_ip = get_local_ip()
    # Use PORT from environment (for cloud services) or default to 5000
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    
    print("=" * 60)
    print("Servidor Web Iniciado!")
    print("=" * 60)
    print(f"Acesse localmente: http://localhost:{port}")
    print(f"Acesse na rede: http://{local_ip}:{port}")
    print("=" * 60)
    if port == 5000:
        print("Para acessar de outros dispositivos na mesma rede:")
        print(f"  - Use o IP: {local_ip}:{port}")
        print("  - Certifique-se de que o firewall permite conexões na porta 5000")
    print("=" * 60)
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)

