from product_db import (
    get_db_conn, get_all_products, get_product_summary_stats,
    get_products_by_nhom, get_sales_summary, get_top_selling_products,
    get_import_logs, get_all_plans, init_product_db
)
from product_reader import import_all_from_call


def get_full_product_report():
    """Báo cáo tổng hợp đầy đủ cho dashboard."""
    stats = get_product_summary_stats()
    sales = get_sales_summary()
    products = get_all_products()

    margins = []
    for p in products:
        if p["gia_ban"] and p["gia_ban"] > 0:
            margin = round((p["gia_ban"] - p["gia_von"]) / p["gia_ban"] * 100, 2)
        else:
            margin = 0
        margins.append({
            "ma_hang": p["ma_hang"],
            "ten_hang": p["ten_hang"],
            "nhom_hang": p["nhom_hang_cap1"],
            "gia_ban": p["gia_ban"],
            "gia_von": p["gia_von"],
            "ton_kho": p["ton_kho"],
            "gia_tri_ton": p["gia_von"] * p["ton_kho"],
            "bien_lai": margin,
        })

    margins_sorted = sorted(margins, key=lambda x: x["bien_lai"], reverse=True)
    top_margin = margins_sorted[:10]
    low_margin = [m for m in margins_sorted if m["bien_lai"] < 0]

    nhom_hang = get_products_by_nhom(1)
    top_selling = get_top_selling_products(10)

    return {
        "stats": stats,
        "sales": sales,
        "margins": {
            "top": top_margin,
            "low": low_margin,
            "all": margins,
        },
        "nhom_hang": nhom_hang,
        "top_selling": top_selling,
        "import_logs": get_import_logs(),
    }


def get_inventory_report():
    """Báo cáo tồn kho chi tiết."""
    products = get_all_products()
    nhom_hang = get_products_by_nhom(1)

    inventory_data = []
    for p in products:
        if p["ton_kho"] > 0:
            inventory_data.append({
                "ma_hang": p["ma_hang"],
                "ten_hang": p["ten_hang"],
                "nhom_hang": p["nhom_hang_cap1"],
                "ton_kho": p["ton_kho"],
                "gia_von": p["gia_von"],
                "gia_tri_ton": p["gia_von"] * p["ton_kho"],
                "gia_ban": p["gia_ban"],
            })

    inventory_data.sort(key=lambda x: x["gia_tri_ton"], reverse=True)

    stats = {
        "total_qty": sum(p["ton_kho"] for p in products),
        "total_value": sum(p["gia_von"] * p["ton_kho"] for p in products),
        "total_selling_value": sum(p["gia_ban"] * p["ton_kho"] for p in products),
    }

    return {
        "stats": stats,
        "products": inventory_data,
        "nhom_hang": nhom_hang,
    }


def get_profit_report():
    """Báo cáo lợi nhuận chi tiết."""
    products = get_all_products()
    sales = get_sales_summary()

    profit_data = []
    for p in products:
        if p["gia_ban"] > 0:
            loi_nhuan_sp = p["gia_ban"] - p["gia_von"]
            ty_suat = round(loi_nhuan_sp / p["gia_ban"] * 100, 2) if p["gia_ban"] > 0 else 0
            profit_data.append({
                "ma_hang": p["ma_hang"],
                "ten_hang": p["ten_hang"],
                "gia_ban": p["gia_ban"],
                "gia_von": p["gia_von"],
                "loi_nhuan_sp": loi_nhuan_sp,
                "ty_suat": ty_suat,
                "ton_kho": p["ton_kho"],
                "gia_tri_ton_kho": p["gia_von"] * p["ton_kho"],
            })

    profit_data.sort(key=lambda x: x["loi_nhuan_sp"], reverse=True)

    return {
        "sales_summary": sales,
        "products": profit_data,
        "top_profit": profit_data[:10],
        "low_margin": [p for p in profit_data if p["ty_suat"] < 0],
    }


def run_full_import():
    """Chạy import toàn bộ từ file Excel."""
    init_product_db()
    result = import_all_from_call()
    return result
