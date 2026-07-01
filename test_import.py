import sys
import json
sys.stdout.reconfigure(encoding='utf-8')
from product_reader import read_products_from_call
products, err = read_products_from_call()
if err:
    print("Error:", err)
else:
    print(f"Loaded {len(products)} products:")
    for p in products:
        print(p)
