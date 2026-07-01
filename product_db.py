import sqlite3
from datetime import datetime
from config import DATABASE_PATH
from database import get_db, init_db as init_finance_db


def get_db_conn():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_product_db():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ma_hang TEXT NOT NULL,
            ten_hang TEXT NOT NULL DEFAULT '',
            thuong_hieu TEXT DEFAULT '',
            nhom_hang_cap1 TEXT DEFAULT '',
            nhom_hang_cap2 TEXT DEFAULT '',
            nhom_hang_cap3 TEXT DEFAULT '',
            gia_ban REAL DEFAULT 0,
            gia_von REAL DEFAULT 0,
            ton_kho INTEGER DEFAULT 0,
            vi_tri TEXT DEFAULT '',
            gia_ban_le REAL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS sales_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ma_hang TEXT NOT NULL,
            ten_hang TEXT DEFAULT '',
            thoi_gian TEXT NOT NULL,
            sl_ban INTEGER DEFAULT 0,
            gia_ban REAL DEFAULT 0,
            thanh_tien REAL DEFAULT 0,
            gia_von REAL DEFAULT 0,
            loi_nhuan REAL DEFAULT 0,
            ten_khach_hang TEXT DEFAULT '',
            ma_kh TEXT DEFAULT '',
            sl_tra INTEGER DEFAULT 0,
            gt_tra REAL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS inventory_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ma_hang TEXT NOT NULL,
            ten_hang TEXT DEFAULT '',
            ngay_nhap TEXT NOT NULL,
            so_luong INTEGER DEFAULT 0,
            gia_von_dv REAL DEFAULT 0,
            thanh_tien REAL DEFAULT 0,
            nha_cung_cap TEXT DEFAULT '',
            so_invoice TEXT DEFAULT '',
            ghi_chu TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS import_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_file TEXT NOT NULL,
            imported_at TEXT NOT NULL DEFAULT (datetime('now')),
            product_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'success',
            message TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS product_plan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ma_hang TEXT NOT NULL,
            ten_hang TEXT DEFAULT '',
            chi_phi_sx REAL DEFAULT 0,
            gia_ban_ke_hoach REAL DEFAULT 0,
            margin_muc_tieu REAL DEFAULT 0,
            sl_can_ban INTEGER DEFAULT 0,
            von_can_thu_hoi REAL DEFAULT 0,
            ghi_chu TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()


# ============== PRODUCTS CRUD ==============

def upsert_product(data):
    conn = get_db_conn()
    existing = conn.execute(
        "SELECT id FROM products WHERE ma_hang = ?", (data["ma_hang"],)
    ).fetchone()
    now = datetime.now().isoformat()
    if existing:
        conn.execute("""
            UPDATE products SET ten_hang=?, thuong_hieu=?, nhom_hang_cap1=?,
            nhom_hang_cap2=?, nhom_hang_cap3=?, gia_ban=?, gia_von=?,
            ton_kho=?, vi_tri=?, gia_ban_le=?, updated_at=?
            WHERE ma_hang=?
        """, (
            data.get("ten_hang", ""), data.get("thuong_hieu", ""),
            data.get("nhom_hang_cap1", ""), data.get("nhom_hang_cap2", ""),
            data.get("nhom_hang_cap3", ""), data.get("gia_ban", 0),
            data.get("gia_von", 0), data.get("ton_kho", 0),
            data.get("vi_tri", ""), data.get("gia_ban_le", 0),
            now, data["ma_hang"]
        ))
        conn.commit()
        conn.close()
        return existing["id"]
    else:
        cur = conn.execute("""
            INSERT INTO products (ma_hang, ten_hang, thuong_hieu, nhom_hang_cap1,
                nhom_hang_cap2, nhom_hang_cap3, gia_ban, gia_von,
                ton_kho, vi_tri, gia_ban_le)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            data["ma_hang"], data.get("ten_hang", ""), data.get("thuong_hieu", ""),
            data.get("nhom_hang_cap1", ""), data.get("nhom_hang_cap2", ""),
            data.get("nhom_hang_cap3", ""), data.get("gia_ban", 0),
            data.get("gia_von", 0), data.get("ton_kho", 0),
            data.get("vi_tri", ""), data.get("gia_ban_le", 0)
        ))
        conn.commit()
        aid = cur.lastrowid
        conn.close()
        return aid


def get_all_products():
    conn = get_db_conn()
    rows = conn.execute("SELECT * FROM products ORDER BY ten_hang").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_product_by_ma(ma_hang):
    conn = get_db_conn()
    row = conn.execute("SELECT * FROM products WHERE ma_hang = ?", (ma_hang,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_product_summary_stats():
    conn = get_db_conn()
    total_sp = conn.execute("SELECT COUNT(*) as c FROM products").fetchone()["c"]
    total_ton_kho = conn.execute("SELECT COALESCE(SUM(ton_kho),0) as c FROM products").fetchone()["c"]
    total_gia_von = conn.execute("SELECT COALESCE(SUM(gia_von * ton_kho),0) as c FROM products").fetchone()["c"]
    total_gia_ban = conn.execute("SELECT COALESCE(SUM(gia_ban * ton_kho),0) as c FROM products").fetchone()["c"]
    conn.close()
    return {
        "total_products": total_sp,
        "total_inventory_qty": total_ton_kho,
        "total_inventory_cost": total_gia_von,
        "total_inventory_value": total_gia_ban,
    }


def get_products_by_nhom(nhom_level=1):
    col = {1: "nhom_hang_cap1", 2: "nhom_hang_cap2", 3: "nhom_hang_cap3"}[nhom_level]
    conn = get_db_conn()
    rows = conn.execute(
        f"SELECT {col} as nhom, COUNT(*) as so_sp, SUM(ton_kho) as tong_ton, "
        f"COALESCE(SUM(gia_von * ton_kho),0) as tong_gia_tri "
        f"FROM products GROUP BY {col} ORDER BY tong_gia_tri DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ============== SALES CRUD ==============

def insert_sales(row_data):
    conn = get_db_conn()
    conn.execute("""
        INSERT INTO sales_history (ma_hang, ten_hang, thoi_gian, sl_ban,
            gia_ban, thanh_tien, gia_von, loi_nhuan, ten_khach_hang,
            ma_kh, sl_tra, gt_tra)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        row_data.get("ma_hang"), row_data.get("ten_hang", ""),
        row_data.get("thoi_gian"), row_data.get("sl_ban", 0),
        row_data.get("gia_ban", 0), row_data.get("thanh_tien", 0),
        row_data.get("gia_von", 0), row_data.get("loi_nhuan", 0),
        row_data.get("ten_khach_hang", ""), row_data.get("ma_kh", ""),
        row_data.get("sl_tra", 0), row_data.get("gt_tra", 0)
    ))
    conn.commit()
    conn.close()


def get_sales_summary():
    conn = get_db_conn()
    total_ban = conn.execute("SELECT COALESCE(SUM(sl_ban),0) as c FROM sales_history").fetchone()["c"]
    total_tra = conn.execute("SELECT COALESCE(SUM(sl_tra),0) as c FROM sales_history").fetchone()["c"]
    total_doanh_thu = conn.execute("SELECT COALESCE(SUM(thanh_tien),0) as c FROM sales_history").fetchone()["c"]
    total_loi_nhuan = conn.execute("SELECT COALESCE(SUM(loi_nhuan),0) as c FROM sales_history").fetchone()["c"]
    conn.close()
    return {
        "total_sold": total_ban,
        "total_returned": total_tra,
        "total_revenue": total_doanh_thu,
        "total_profit": total_loi_nhuan,
    }


def get_top_selling_products(limit=10):
    conn = get_db_conn()
    rows = conn.execute("""
        SELECT ma_hang, ten_hang,
            SUM(sl_ban) as sl_ban, SUM(thanh_tien) as doanh_thu,
            SUM(loi_nhuan) as loi_nhuan, SUM(sl_tra) as sl_tra
        FROM sales_history
        GROUP BY ma_hang
        ORDER BY SUM(thanh_tien) DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ============== INVENTORY / IMPORT CRUD ==============

def insert_import(row_data):
    conn = get_db_conn()
    conn.execute("""
        INSERT INTO inventory_history (ma_hang, ten_hang, ngay_nhap, so_luong,
            gia_von_dv, thanh_tien, nha_cung_cap, so_invoice, ghi_chu)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (
        row_data.get("ma_hang"), row_data.get("ten_hang", ""),
        row_data.get("ngay_nhap"), row_data.get("so_luong", 0),
        row_data.get("gia_von_dv", 0), row_data.get("thanh_tien", 0),
        row_data.get("nha_cung_cap", ""), row_data.get("so_invoice", ""),
        row_data.get("ghi_chu", "")
    ))
    conn.commit()
    conn.close()


# ============== IMPORT LOG ==============

def log_import(source_file, product_count, status="success", message=""):
    conn = get_db_conn()
    conn.execute(
        "INSERT INTO import_log (source_file, product_count, status, message) VALUES (?,?,?,?)",
        (source_file, product_count, status, message)
    )
    conn.commit()
    conn.close()


def get_import_logs(limit=10):
    conn = get_db_conn()
    rows = conn.execute("SELECT * FROM import_log ORDER BY imported_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ============== PRODUCT PLAN ==============

def upsert_product_plan(data):
    conn = get_db_conn()
    existing = conn.execute(
        "SELECT id FROM product_plan WHERE ma_hang = ?", (data["ma_hang"],)
    ).fetchone()
    if existing:
        conn.execute("""
            UPDATE product_plan SET ten_hang=?, chi_phi_sx=?, gia_ban_ke_hoach=?,
            margin_muc_tieu=?, sl_can_ban=?, von_can_thu_hoi=?, ghi_chu=?
            WHERE ma_hang=?
        """, (
            data.get("ten_hang", ""), data.get("chi_phi_sx", 0),
            data.get("gia_ban_ke_hoach", 0), data.get("margin_muc_tieu", 0),
            data.get("sl_can_ban", 0), data.get("von_can_thu_hoi", 0),
            data.get("ghi_chu", ""), data["ma_hang"]
        ))
    else:
        conn.execute("""
            INSERT INTO product_plan (ma_hang, ten_hang, chi_phi_sx,
                gia_ban_ke_hoach, margin_muc_tieu, sl_can_ban, von_can_thu_hoi, ghi_chu)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            data["ma_hang"], data.get("ten_hang", ""), data.get("chi_phi_sx", 0),
            data.get("gia_ban_ke_hoach", 0), data.get("margin_muc_tieu", 0),
            data.get("sl_can_ban", 0), data.get("von_can_thu_hoi", 0),
            data.get("ghi_chu", "")
        ))
    conn.commit()
    conn.close()


def get_all_plans():
    conn = get_db_conn()
    rows = conn.execute("SELECT * FROM product_plan").fetchall()
    conn.close()
    return [dict(r) for r in rows]
