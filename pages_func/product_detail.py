import streamlit as st
import pandas as pd
from database.crud import get_all_products, get_all_accessories
# 字段中英文映射（和settings.py保持一致）
PRODUCT_FIELD_CN = {
    "product_name": "产品名称",
    "single_length": "单支长度/m",
    "single_width": "单支宽度/m",
    "single_height": "单支高度/m",
    "meter_weight": "米重(kg)",
    "tax_price_per_meter": "含税价/米(人民币)",
    "surcharge_per_meter": "每米附加费(人民币)",
    "min_order_qty": "起订量(支)",
    "pallet_row_qty": "托盘一排数量",
    "max_per_pallet": "拼箱一托最多数量(支)",
    "pallet_weight": "托盘重量(kg)",
    "fence_layers": "围栏板层数",
    "remark": "备注"
}
ACC_FIELD_CN = {
    "category": "配件品类",
    "product_name": "产品名称",
    "unit_price_eur": "欧元单价",
    "unit_weight": "单件重量(kg)",
    "spec": "规格",
    "remark": "备注"
}
def page_product_detail():
    st.title("📦产品详情查看")
    cat_sel = st.selectbox("选择产品大类", ["长城板", "围栏板", "地板", "围栏板配件", "地板配件"])
    table_map = {
        "长城板": ("great_wall_boards", False),
        "围栏板": ("fence_boards", False),
        "地板": ("floor_boards", False),
        "围栏板配件": ("fence_accessories", True),
        "地板配件": ("floor_accessories", True)
    }
    tbl_name, is_acc = table_map[cat_sel]
    if is_acc:
        data = get_all_accessories(tbl_name)
        field_map = ACC_FIELD_CN
    else:
        data = get_all_products(tbl_name)
        field_map = PRODUCT_FIELD_CN
    if not data:
        st.info("该分类暂无产品数据，请前往设置页添加")
        return
    name_list = [x["product_name"] for x in data]
    sel_name = st.selectbox("选择产品", name_list)
    rec = next(x for x in data if x["product_name"] == sel_name)
    st.subheader(f"{rec['product_name']}")
    # ========== 修改图片排版：多图横向自动排列 + 点击预览 ==========
    img_urls = rec.get("image_urls", [])
    if isinstance(img_urls, list) and len(img_urls) > 0:
        # 按3列布局图片
        cols = st.columns(min(3, len(img_urls)))
        for idx, img in enumerate(img_urls):
            with cols[idx % 3]:
                # 使用st.image自带点击放大预览功能
                st.image(img, width="stretch")
    else:
        st.info("🖼️ 暂无产品图片")
    st.divider()
    st.subheader("📋产品基本参数")
    # 组装中文参数表格
    param_rows = []
    for en_key, raw_value in rec.items():
        # 跳过id、时间、图片url字段
        if en_key in ("id", "created_at", "updated_at", "image_urls"):
            continue
        cn_label = field_map.get(en_key, en_key)
        # 关键修复：统一转字符串，None转为空字符串，防止一列混合float/str触发pyarrow报错
        if raw_value is None:
            show_val = ""
        else:
            show_val = str(raw_value)
        param_rows.append({"参数名称": cn_label, "参数值": show_val})
    df_param = pd.DataFrame(param_rows)
    st.dataframe(
        df_param,
        use_container_width=True,
        hide_index=True
    )
page_product_detail()
