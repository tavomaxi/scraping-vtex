#!/usr/bin/env python3
"""
Portsaid Catalog Scraper - v3.0 FINAL (Precios y Descuentos Corregidos)
"""

import requests
import json
import time
import csv
import sys
from datetime import datetime
from pathlib import Path


def get_product_prices(product):
    """Extrae los precios correctos del producto."""
    items = product.get('items', [])
    if not items:
        return 0, 0
    
    item = items[0]
    sellers = item.get('sellers', [])
    
    if not sellers:
        return 0, 0
    
    seller = sellers[0]
    offer = seller.get('commertialOffer', {})
    
    # Precio de venta (con descuento aplicado)
    selling_price = offer.get('Price', 0)
    
    # Precio de lista (sin descuento)
    list_price = offer.get('ListPrice', 0)
    
    # Si ListPrice es 0 o igual al selling, intentar con PriceWithoutDiscount
    if list_price == 0 or list_price == selling_price:
        list_price = offer.get('PriceWithoutDiscount', selling_price)
    
    # Fallback: usar priceRange si no hay precios
    if list_price == 0 or selling_price == 0:
        price_range = product.get('priceRange', {})
        list_price = price_range.get('listPrice', {}).get('highPrice', 0)
        selling_price = price_range.get('sellingPrice', {}).get('highPrice', 0)
    
    return list_price, selling_price


def main():
    print("="*60)
    print("PORTSAID CATALOG SCRAPER - v3.0")
    print("="*60)
    
    base_url = "https://www.portsaid.com.ar"
    api_endpoint = "/api/io/_v/api/intelligent-search/product_search"
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    
    print(f"Output: {output_dir.absolute()}")
    
    # Extraer productos
    all_products = []
    page = 1
    
    while True:
        url = f"{base_url}{api_endpoint}?page={page}"
        print(f"Page {page}...")
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            products = data.get('products', [])
            if not products:
                break
            
            all_products.extend(products)
            print(f"  +{len(products)} = {len(all_products)}")
            
            page += 1
            time.sleep(0.3)
            
        except Exception as e:
            print(f"Error: {e}")
            break
    
    print(f"\nTotal: {len(all_products)} products")
    
    # Procesar
    processed = []
    discount_count = 0
    
    for p in all_products:
        try:
            list_price, selling_price = get_product_prices(p)
            
            # Calcular descuento
            discount = 0
            if list_price > 0 and selling_price > 0 and list_price > selling_price:
                discount = round((1 - selling_price / list_price) * 100, 0)
                discount_count += 1
            
            # Imagen
            items = p.get('items', [])
            img = items[0]['images'][0]['imageUrl'] if items and items[0].get('images') else ''
            
            # Categoria
            categories = p.get('categories', [])
            category = categories[0].replace('/', ' > ').strip(' >') if categories else ''
            
            processed.append({
                'ID': p.get('productId', ''),
                'Nombre': p.get('productName', ''),
                'Marca': p.get('brand', ''),
                'Categoria': category,
                'Precio Lista': list_price,
                'Precio Venta': selling_price,
                'Descuento %': int(discount),
                'URL Imagen': img,
                'URL Producto': f"{base_url}{p.get('link', '')}"
            })
        except:
            continue
    
    print(f"Processed: {len(processed)}")
    print(f"With discount: {discount_count}")
    
    # Guardar CSV
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_path = output_dir / f"portsaid_catalogo_{timestamp}.csv"
    
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        if processed:
            writer = csv.DictWriter(f, fieldnames=processed[0].keys())
            writer.writeheader()
            writer.writerows(processed)
    
    print(f"Saved: {csv_path}")
    print("="*60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
