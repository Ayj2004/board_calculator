import uuid
from database.client import get_supabase

# =========全部使用【英文半角短横线 -】=========
TABLE_BUCKET_MAP = {
    "great_wall_boards": "great-wall-boards",
    "fence_boards": "fence-boards",
    "floor_boards": "floor-boards",
    "fence_accessories": "fence-accessories",
    "floor_accessories": "floor-accessories"
}

def upload_product_image(table_name: str, product_id: int, st_upload_file):
    """
    上传streamlit file_uploader的UploadedFile对象到Supabase Storage
    :param table_name: 数据库表名
    :param product_id: 产品id
    :param st_upload_file: streamlit file_uploader返回的UploadedFile
    :return: 公开图片url
    """
    sb = get_supabase()
    bucket = TABLE_BUCKET_MAP[table_name]
    filename = st_upload_file.name
    ext = filename.split(".")[-1]
    file_path = f"{product_id}/{uuid.uuid4().hex}.{ext}"
    # 读取二进制字节
    file_bytes = st_upload_file.read()
    sb.storage.from_(bucket).upload(
        path=file_path,
        file=file_bytes,
        file_options={"content-type": st_upload_file.type}
    )
    public_url = sb.storage.from_(bucket).get_public_url(file_path)
    return public_url

def delete_storage_file(table_name: str, public_url: str):
    """删除storage里面的图片文件"""
    sb = get_supabase()
    bucket = TABLE_BUCKET_MAP[table_name]
    prefix = f"/storage/v1/object/public/{bucket}/"
    file_path = public_url.split(prefix)[-1]
    sb.storage.from_(bucket).remove([file_path])

def parse_storage_path_from_url(table_name: str, public_url: str):
    """从公开url解析出storage内部文件路径"""
    sb = get_supabase()
    bucket = TABLE_BUCKET_MAP[table_name]
    prefix = f"/storage/v1/object/public/{bucket}/"
    return public_url.split(prefix)[-1]
