import sys
sys.stdout.reconfigure(encoding='utf-8')
from product_analytics import run_full_import
from product_db import get_all_products

result = run_full_import()
print("Import Result:", result)

products = get_all_products()
print(f"\nTotal products in DB: {len(products)}")
for p in products:
    print(f"{p['ma_hang']} | {p['ten_hang']} | Cost: {p['gia_von']} | Price: {p['gia_ban']} | Qty: {p['ton_kho']}")
