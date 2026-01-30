#!/usr/bin/env python3
"""
Portsaid Catalog Scraper
"""

import requests
import json
import time
import csv
import sys
from datetime import datetime
from pathlib import Path


def main():
    print("="*60)
    print("PORTSAID CATALOG SCRAPER")
    print("="*60)
    
    base_url = "https://www.portsaid.com.ar"
    api_endpoint = "/api/io/_v/api/intelligent-search/product_search"
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    
    print(f"Output directory: {output_dir.absolute()}")
    
    # Extraer productos
    all_products = []
    page = 1
    
    while True:
        url = f"{base_url}{api_endpoint}?page={page}"
        print(f"Fetching page {page}...")
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            products = data.get('products', [])
            if not products:
                print(f"No more products at page {page}")
                break
            
            all_products.extend(products)
            print(f"  Got {len(products)} products (Total: {len(all_products)})")
            
            page += 1
            time.sleep(0.3)
            
        except Exception as e:
            print(f"Error on page {page}: {e}")
            break
    
    print(f"\nTotal extracted: {len(all_products)} products")
    
    # Procesar
    processed = []
    for p in all_products:
        try:
            price_range = p.get('priceRange', {})
            selling = price_range.get('sellingPrice', {}).get('highPrice', 0)
            listing = price_range.get('listPrice', {}).get('highPrice', 0)
            
            items = p.get('items', [])
            img = ''
            if items and items[0].get('images'):
                img = items[0]['images'][0].get('imageUrl', '')
            
            categories = p.get('categories', [])
            category = categories[0].replace('/', ' > ').strip(' >') if categories else ''
            
            processed.append({
                'ID': p.get('productId', ''),
                'Nombre': p.get('productName', ''),
                'Marca': p.get('brand', ''),
                'Categoria': category,
                'Precio Lista': listing,
                'Precio Venta': selling,
                'Descuento': round((1 - selling/listing) * 100, 0) if listing > 0 else 0,
                'URL Imagen': img,
                'URL Producto': f"{base_url}{p.get('link', '')}",
                'Descripcion': p.get('description', '')[:200]
            })
        except Exception as e:
            continue
    
    # Guardar CSV
    csv_path = output_dir / f"portsaid_catalogo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        if processed:
            writer = csv.DictWriter(f, fieldnames=processed[0].keys())
            writer.writeheader()
            writer.writerows(processed)
    
    print(f"\nSaved: {csv_path}")
    print(f"Total products: {len(processed)}")
    print("="*60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
