from .client import get_supabase
import pandas as pd

# ❗删掉这一行：sb = get_supabase()

# ========== exchange_rates 汇率 ==========
def get_all_exchange_rates(active_only=False):
    sb = get_supabase()
    q = sb.table("exchange_rates").select("*")
    if active_only:
        q = q.eq("is_active", True)
    resp = q.order("currency").execute()
    return resp.data

def add_exchange_rate(data: dict):
    sb = get_supabase()
    return sb.table("exchange_rates").insert(data).execute()

def update_exchange_rate(record_id: int, field: str, value):
    sb = get_supabase()
    return sb.table("exchange_rates").update({field: value, "updated_at": "now()"}).eq("id", record_id).execute()

def delete_exchange_rate(record_id: int):
    sb = get_supabase()
    return sb.table("exchange_rates").delete().eq("id", record_id).execute()

# ========== 通用产品CRUD 长城板/围栏板/地板 ==========
def get_all_products(table_name: str):
    sb = get_supabase()
    resp = sb.table(table_name).select("*").order("id").execute()
    return resp.data

def get_product_by_id(table_name: str, record_id: int):
    sb = get_supabase()
    resp = sb.table(table_name).select("*").eq("id", record_id).execute()
    return resp.data[0] if resp.data else None

def add_product(table_name: str, data: dict):
    sb = get_supabase()
    return sb.table(table_name).insert(data).execute()

def update_product_field(table_name: str, record_id: int, field: str, value):
    sb = get_supabase()
    return sb.table(table_name).update({field: value, "updated_at":"now()"}).eq("id", record_id).execute()

def delete_product(table_name: str, record_id: int):
    sb = get_supabase()
    return sb.table(table_name).delete().eq("id", record_id).execute()

# ========== 配件CRUD ==========
def get_all_accessories(table_name: str, category: str | None = None):
    sb = get_supabase()
    q = sb.table(table_name).select("*")
    if category:
        q = q.eq("category", category)
    resp = q.order("category,id").execute()
    return resp.data

def add_accessory(table_name: str, data: dict):
    sb = get_supabase()
    return sb.table(table_name).insert(data).execute()

def update_accessory_field(table_name: str, record_id: int, field: str, value):
    sb = get_supabase()
    return sb.table(table_name).update({field: value, "updated_at":"now()"}).eq("id", record_id).execute()

def delete_accessory(table_name: str, record_id: int):
    sb = get_supabase()
    return sb.table(table_name).delete().eq("id", record_id).execute()

def get_first_accessory_by_cat(table_name: str, cat: str):
    arr = get_all_accessories(table_name, category=cat)
    return arr[0] if arr else None

# ========== product_advantages 产品优势 ==========
def get_all_advantages(category: str | None = None):
    sb = get_supabase()
    q = sb.table("product_advantages").select("*")
    if category:
        q = q.eq("category", category)
    resp = q.order("sort_order,id").execute()
    return resp.data

def add_advantage(data: dict):
    sb = get_supabase()
    return sb.table("product_advantages").insert(data).execute()

def update_advantage_field(record_id:int, field:str, value):
    sb = get_supabase()
    return sb.table("product_advantages").update({field:value, "updated_at":"now()"}).eq("id", record_id).execute()

def delete_advantage(record_id:int):
    sb = get_supabase()
    return sb.table("product_advantages").delete().eq("id", record_id).execute()

def update_product_image_urls(table_name:str, record_id:int, url_list:list):
    """更新产品image_urls数组"""
    sb = get_supabase()
    return sb.table(table_name).update({
        "image_urls": url_list,
        "updated_at":"now()"
    }).eq("id", record_id).execute()

from database.storage import delete_storage_file, parse_storage_path_from_url

def delete_product_with_images(table_name: str, record_id:int):
    """删除产品，先删除storage全部图片，再删除数据库行"""
    sb = get_supabase()
    resp = sb.table(table_name).select("image_urls").eq("id",record_id).execute()
    if resp.data and len(resp.data)>0:
        url_list = resp.data[0].get("image_urls") or []
        for url in url_list:
            try:
                fp = parse_storage_path_from_url(table_name, url)
                delete_storage_file(table_name, fp)
            except Exception:
                pass
    # 删除数据库记录
    return sb.table(table_name).delete().eq("id",record_id).execute()

def delete_accessory_with_images(table_name: str, record_id:int):
    """删除配件，先删除storage全部图片，再删除数据库行"""
    sb = get_supabase()
    resp = sb.table(table_name).select("image_urls").eq("id",record_id).execute()
    if resp.data and len(resp.data)>0:
        url_list = resp.data[0].get("image_urls") or []
        for url in url_list:
            try:
                fp = parse_storage_path_from_url(table_name, url)
                delete_storage_file(table_name, fp)
            except Exception:
                pass
    return sb.table(table_name).delete().eq("id",record_id).execute()
