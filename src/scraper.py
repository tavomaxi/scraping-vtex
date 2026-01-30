#!/usr/bin/env python3
"""
Portsaid Catalog Scraper - Versión GitHub Actions
Simplificado y robusto para ejecución en CI/CD
"""

import requests
import json
import time
import os
import sys
from datetime import datetime
from pathlib import Path


def main():
    """Función principal del scraper."""
    print("="*60)
    print("PORTSAID CATALOG SCRAPER - GitHub Actions")
    print("="*60)
    
    # Configuración
    base_url = "https://www.portsaid.com.ar"
    api_endpoint = "/api/io/_v/api/intelligent-search/product_search"
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    
    print(f"Output directory: {output_dir.absolute()}")
    print(f"Starting extraction...")
    
    # Extraer productos
    all_products = []
    page = 1
    max_pages = 50  # Límite de seguridad
    
    try:
        while page <= max_pages:
            url = f"{base_url}{api_endpoint}?page={page}"
            print(f"Fetching page {page}...")
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            products = data.get('products', [])
            if not products:
                print(f"No more products at page {page}")
                break
            
            all_products.extend(products)
            print(f"  Page {page}: {len(products)} products (Total: {len(all_products)})")
            
            page += 1
            time.sleep(0.5)  # Pausa entre requests
        
        print(f"\nExtraction complete: {len(all_products)} products")
        
        # Procesar productos
        processed = []
        for product in all_products:
            try:
                price_range = product.get('priceRange', {})
                selling_price = price_range.get('sellingPrice', {}).get('highPrice', 0)
                list_price = price_range.get('listPrice', {}).get('highPrice', 0)
                
                categories = product.get('categories', [])
                category = categories[0] if categories else ''
                
                items = product.get('items', [])
                main_image = ''
                if items:
                    images = items[0].get('images', [])
                    if images:
                        main_image = images[0].get('imageUrl', '')
                
                processed.append({
                    'ID': product.get('productId', ''),
                    'Nombre': product.get('productName', ''),
                    'Marca': product.get('brand', ''),
                    'Categoría': category.replace('/', ' > ').strip(' >'),
                    'Precio Lista': list_price,
                    'Precio Venta': selling_price,
                    'Descuento %': round((1 - selling_price/list_price) * 100, 0) if list_price > 0 else 0,
                    'URL Imagen': main_image,
                    'URL Producto': f"{base_url}{product.get('link', '')}",
                    'Descripcion': product.get('description', '')[:300]
                })
            except Exception as e:
                print(f"  Warning: Error processing product: {e}")
                continue
        
        print(f"Processed: {len(processed)} products")
        
        # Guardar como JSON (formato intermedio)
        json_path = output_dir / "products.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(processed, f, ensure_ascii=False, indent=2)
        print(f"Saved JSON: {json_path}")
        
        # Guardar como CSV
        try:
            import csv
            csv_path = output_dir / f"portsaid_catalogo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                if processed:
                    writer = csv.DictWriter(f, fieldnames=processed[0].keys())
                    writer.writeheader()
                    writer.writerows(processed)
            print(f"Saved CSV: {csv_path}")
        except Exception as e:
            print(f"Warning: Could not save CSV: {e}")
        
        print("="*60)
        print("SUCCESS: Scraper completed successfully!")
        print("="*60)
        return 0
        
    except requests.RequestException as e:
        print(f"ERROR: Network error: {e}")
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
