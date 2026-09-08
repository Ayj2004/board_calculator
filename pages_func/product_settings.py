import streamlit as st
import pandas as pd
from database.crud import (
    get_all_exchange_rates, add_exchange_rate, update_exchange_rate, delete_exchange_rate,
    get_all_products, add_product, update_product_field,
    delete_product_with_images,
    get_all_accessories, add_accessory, update_accessory_field,
    delete_accessory_with_images,
    update_product_image_urls
)
from database.storage import upload_product_image, delete_storage_file, parse_storage_path_from_url

# -------------------------- 字段中英文映射配置 --------------------------
# key=数据库英文字段名，value=显示中文
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
# 反向映射：中文 → 英文
PRODUCT_FIELD_EN_CN = {v: k for k, v in PRODUCT_FIELD_CN.items()}

ACC_FIELD_CN = {
    "category": "配件品类",
    "product_name": "产品名称",
    "unit_price_eur": "欧元单价",
    "unit_weight": "单件重量(kg)",
    "spec": "规格",
    "remark": "备注"
}
ACC_FIELD_EN_CN = {v: k for k, v in ACC_FIELD_CN.items()}

EXCHANGE_FIELD_CN = {
    "currency": "币种代码",
    "currency_name": "币种中文名称",
    "rate": "汇率(1外币=人民币)",
    "currency_surcharge": "币种附加费",
    "is_active": "是否启用"
}


def page_settings():
    st.title("⚙️ 系统设置")
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "汇率设置",
        "长城板产品管理",
        "围栏板产品管理",
        "地板产品管理",
        "配件管理"
    ])

    # ========= TAB1 汇率设置 =========
    with tab1:
        st.subheader("新增汇率")
        with st.form("form_exchange"):
            c_code = st.text_input(EXCHANGE_FIELD_CN["currency"], "")
            c_name = st.text_input(EXCHANGE_FIELD_CN["currency_name"], "")
            rate = st.number_input(EXCHANGE_FIELD_CN["rate"], min_value=0.0001, value=None, step=0.0001)
            sur = st.number_input(EXCHANGE_FIELD_CN["currency_surcharge"], value=None, step=0.01)
            sub = st.form_submit_button("添加")
            if sub:
                try:
                    add_exchange_rate({
                        "currency": c_code.strip(),
                        "currency_name": c_name.strip(),
                        "rate": rate,
                        "currency_surcharge": sur if sur is not None else 0.0,
                        "is_active": True
                    })
                    st.success("添加成功，请刷新")
                except Exception as e:
                    st.error(f"失败:{e}")

        st.divider()
        st.subheader("汇率列表")
        data_ex = get_all_exchange_rates()
        if not data_ex:
            st.info("暂无汇率数据")
        else:
            df_ex = pd.DataFrame(data_ex)
            df_ex_show = df_ex.rename(columns=EXCHANGE_FIELD_CN)
            show_cols_ex = ["币种代码", "币种中文名称", "汇率(1外币=人民币)", "币种附加费", "是否启用"]
            st.dataframe(df_ex_show[show_cols_ex], use_container_width=True)
            for idx, row in df_ex.iterrows():
                rid = int(row["id"])
                col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 0.6])
                col1.write(row["currency"])
                col2.write(row["currency_name"])

                edit_rate_key = f"edit_ex_rate_{rid}"
                edit_sur_key = f"edit_ex_sur_{rid}"
                toggle_key = f"toggle_ex_{rid}"
                if edit_rate_key not in st.session_state:
                    st.session_state[edit_rate_key] = False
                if edit_sur_key not in st.session_state:
                    st.session_state[edit_sur_key] = False

                if st.session_state[edit_rate_key]:
                    new_r = col3.number_input(EXCHANGE_FIELD_CN["rate"], value=float(row["rate"]), key=f"val_r_{rid}")
                    ok, cancel = col3.columns([0.4, 0.4])
                    if ok.button("✓", key=f"ok_r_{rid}"):
                        update_exchange_rate(rid, "rate", new_r)
                        st.session_state[edit_rate_key] = False
                        st.rerun()
                    if cancel.button("✕", key=f"cx_r_{rid}"):
                        st.session_state[edit_rate_key] = False
                        st.rerun()
                else:
                    col3.button(f"{row['rate']}", on_click=lambda k=edit_rate_key: st.session_state.__setitem__(k, True), key=f"btn_r_{rid}")

                if st.session_state[edit_sur_key]:
                    new_s = col4.number_input(EXCHANGE_FIELD_CN["currency_surcharge"], value=float(row["currency_surcharge"]), key=f"val_s_{rid}")
                    ok2, cancel2 = col4.columns([0.4, 0.4])
                    if ok2.button("✓", key=f"ok_s_{rid}"):
                        update_exchange_rate(rid, "currency_surcharge", new_s)
                        st.session_state[edit_sur_key] = False
                        st.rerun()
                    if cancel2.button("✕", key=f"cx_s_{rid}"):
                        st.session_state[edit_sur_key] = False
                        st.rerun()
                else:
                    col4.button(f"{row['currency_surcharge']}", on_click=lambda k=edit_sur_key: st.session_state.__setitem__(k, True), key=f"btn_s_{rid}")

                act = col5.toggle(EXCHANGE_FIELD_CN["is_active"], value=bool(row["is_active"]), key=toggle_key)
                if act != bool(row["is_active"]):
                    update_exchange_rate(rid, "is_active", act)
                    st.rerun()
                if col6.button("🗑️删除", key=f"del_ex_{rid}"):
                    delete_exchange_rate(rid)
                    st.rerun()

    # ========= 产品通用渲染函数 =========
    def render_product_tab(table_name: str, tab_title: str, extra_fields: dict | None = None):
        st.subheader(f"新增{tab_title}产品")
        with st.expander("展开新增表单"):
            with st.form(f"form_{table_name}", clear_on_submit=True):
                pname = st.text_input(PRODUCT_FIELD_CN["product_name"], value="")
                sl = st.number_input(PRODUCT_FIELD_CN["single_length"], value=None, step=0.01)
                sw = st.number_input(PRODUCT_FIELD_CN["single_width"], value=None, step=0.001)
                sh = st.number_input(PRODUCT_FIELD_CN["single_height"], value=None, step=0.001)
                mw = st.number_input(PRODUCT_FIELD_CN["meter_weight"], value=None, step=0.01)
                tax = st.number_input(PRODUCT_FIELD_CN["tax_price_per_meter"], value=None, step=0.01)
                sur_per_m = st.number_input(PRODUCT_FIELD_CN["surcharge_per_meter"], value=None, step=0.01)
                min_o = st.number_input(PRODUCT_FIELD_CN["min_order_qty"], value=None, step=1)
                prq = st.number_input(PRODUCT_FIELD_CN["pallet_row_qty"], value=None, step=1)
                maxpp = st.number_input(PRODUCT_FIELD_CN["max_per_pallet"], value=None, step=1)
                pw = st.number_input(PRODUCT_FIELD_CN["pallet_weight"], value=None, step=0.1)
                remark = st.text_area(PRODUCT_FIELD_CN["remark"], value="")

                upload_new_images = st.file_uploader(
                    "产品图片（可多选，不上传则留空）",
                    type=["jpg", "jpeg", "png", "webp"],
                    accept_multiple_files=True,
                    key=f"new_prod_img_{table_name}"
                )

                form_data = {
                    "product_name": pname.strip() if pname else "",
                    "single_length": sl,
                    "single_width": sw,
                    "single_height": sh,
                    "meter_weight": mw,
                    "tax_price_per_meter": tax,
                    "surcharge_per_meter": sur_per_m if sur_per_m is not None else 1.00,
                    "min_order_qty": int(min_o) if min_o is not None else 0,
                    "pallet_row_qty": int(prq) if prq is not None else 0,
                    "max_per_pallet": int(maxpp) if maxpp is not None else 0,
                    "pallet_weight": pw,
                    "remark": remark.strip(),
                    "image_urls": []
                }
                if extra_fields:
                    form_data.update(extra_fields)
                    if "fence_layers" in extra_fields:
                        fl = st.number_input(PRODUCT_FIELD_CN["fence_layers"], value=None, step=1)
                        form_data["fence_layers"] = int(fl) if fl is not None else 0

                sub_p = st.form_submit_button("保存新增")
                if sub_p:
                    if not form_data["product_name"]:
                        st.error("产品名称不能为空！")
                        return
                    try:
                        resp_insert = add_product(table_name, form_data)
                        new_record_id = resp_insert.data[0]["id"]
                        new_img_urls = []
                        if upload_new_images:
                            for f in upload_new_images:
                                url = upload_product_image(table_name, new_record_id, f)
                                new_img_urls.append(url)
                        if len(new_img_urls) > 0:
                            update_product_image_urls(table_name, new_record_id, new_img_urls)
                        st.success("新增完成，刷新页面")
                    except Exception as e:
                        st.error(f"新增失败:{e}")

        st.divider()
        st.subheader(f"{tab_title}产品列表")
        prod_data = get_all_products(table_name)
        if not prod_data:
            st.info("暂无产品，请新增")
            return
        df_p = pd.DataFrame(prod_data)
        show_en_cols = ["id", "product_name", "single_length", "single_width", "single_height",
                        "meter_weight", "tax_price_per_meter", "surcharge_per_meter",
                        "min_order_qty", "pallet_row_qty", "max_per_pallet", "pallet_weight", "remark"]
        if table_name == "fence_boards":
            show_en_cols.insert(-1, "fence_layers")
        df_show = df_p[show_en_cols].rename(columns=PRODUCT_FIELD_CN)
        st.dataframe(df_show, use_container_width=True)
        st.warning("⚠️修改产品：选择产品ID，下方选择字段（中文）进行修改，确认更新写入数据库。")

        sel_id = st.number_input("选择要修改/删除的产品ID", min_value=1, value=1, key=f"sel_id_{table_name}")
        rec = next((x for x in prod_data if x["id"] == sel_id), None)
        if rec is None:
            st.info("该ID不存在")
            return

        st.divider()
        st.subheader("🖼️产品图片管理（可追加、删除单张图片）")
        current_urls = rec.get("image_urls") or []
        if len(current_urls) > 0:
            st.image(current_urls, width=220)
            for idx, img_url in enumerate(current_urls):
                if st.button(f"删除图片{idx + 1}", key=f"del_img_{table_name}_{sel_id}_{idx}"):
                    try:
                        fp = parse_storage_path_from_url(table_name, img_url)
                        delete_storage_file(table_name, fp)
                    except Exception as e:
                        st.warning(f"云端文件删除失败:{e}")
                    new_url_list = [u for i, u in enumerate(current_urls) if i != idx]
                    update_product_image_urls(table_name, sel_id, new_url_list)
                    st.rerun()
        upload_file = st.file_uploader("追加上传图片(jpg/png/webp)",
                                       type=["jpg", "jpeg", "png", "webp"],
                                       key=f"uploader_{table_name}_{sel_id}")
        if upload_file is not None:
            if st.button("确认追加这张图片", key=f"btn_upload_{table_name}_{sel_id}"):
                try:
                    new_url = upload_product_image(table_name, sel_id, upload_file)
                    new_url_list = current_urls + [new_url]
                    update_product_image_urls(table_name, sel_id, new_url_list)
                    st.success("图片上传成功，刷新页面预览")
                    st.rerun()
                except Exception as e:
                    st.error(f"上传失败：{str(e)}")

        edit_cn_options = [cn for en, cn in PRODUCT_FIELD_CN.items() if en not in ("image_urls",)]
        edit_cn = st.selectbox("选择需要修改的字段(中文)", edit_cn_options, key=f"edit_select_{table_name}_{sel_id}")
        edit_en = PRODUCT_FIELD_EN_CN[edit_cn]
        old_val = rec[edit_en]
        new_val = st.text_input(f"【{edit_cn}】原值: {old_val}", value=str(old_val), key=f"edit_text_{table_name}_{sel_id}")

        col_a, col_b = st.columns([1, 1])
        if col_a.button("✅确认更新写入数据库", key=f"btn_save_{table_name}_{sel_id}"):
            try:
                if isinstance(old_val, float):
                    nv = float(new_val)
                elif isinstance(old_val, int):
                    nv = int(new_val)
                else:
                    nv = new_val
                update_product_field(table_name, sel_id, edit_en, nv)
                st.success("更新成功，请刷新")
            except Exception as e:
                st.error(f"更新失败:{e}")
        if col_b.button("🗑️删除此产品(会同步删除全部产品图片，二次确认)", type="secondary", key=f"btn_del_{table_name}_{sel_id}"):
            delete_product_with_images(table_name, sel_id)
            st.rerun()

    with tab2:
        render_product_tab("great_wall_boards", "长城板")
    with tab3:
        render_product_tab("fence_boards", "围栏板", extra_fields={"fence_layers": 9})
    with tab4:
        render_product_tab("floor_boards", "地板")

    # ========= TAB5 配件管理 =========
    with tab5:
        sub_t1, sub_t2 = st.tabs(["围栏板配件", "地板配件"])

        def render_accessory_tab(table_name: str, cat_list: list):
            sel_cat = st.selectbox("配件品类", cat_list)
            with st.form(f"form_acc_{table_name}_{sel_cat}", clear_on_submit=True):
                pn = st.text_input(ACC_FIELD_CN["product_name"], value="")
                eur_price = st.number_input(ACC_FIELD_CN["unit_price_eur"], value=None, step=0.01)
                uw = st.number_input(ACC_FIELD_CN["unit_weight"], value=None, step=0.001)
                spec = st.text_input(ACC_FIELD_CN["spec"], value="")
                acc_new_imgs = st.file_uploader(
                    "配件图片（可多选，不上传留空）",
                    type=["jpg", "jpeg", "png", "webp"],
                    accept_multiple_files=True,
                    key=f"acc_new_img_{table_name}_{sel_cat}"
                )
                subm = st.form_submit_button("新增配件")
                if subm:
                    d = {
                        "category": sel_cat,
                        "product_name": pn.strip() if pn else "",
                        "unit_price_eur": eur_price,
                        "unit_weight": uw if (uw is not None and uw > 0) else None,
                        "spec": spec.strip(),
                        "remark": "",
                        "image_urls": []
                    }
                    if not d["product_name"]:
                        st.error("配件产品名称不能为空！")
                        return
                    try:
                        resp_ins = add_accessory(table_name, d)
                        aid_new = resp_ins.data[0]["id"]
                        img_urls = []
                        if acc_new_imgs:
                            for f in acc_new_imgs:
                                u = upload_product_image(table_name, aid_new, f)
                                img_urls.append(u)
                        if len(img_urls) > 0:
                            update_product_image_urls(table_name, aid_new, img_urls)
                        st.success("新增完成")
                    except Exception as e:
                        st.error(str(e))
            st.divider()
            acc_data = get_all_accessories(table_name, category=sel_cat)
            if acc_data:
                df_acc = pd.DataFrame(acc_data)
                show_acc_cols_en = ["id", "category", "product_name", "unit_price_eur", "unit_weight", "spec"]
                df_acc_show = df_acc[show_acc_cols_en].rename(columns=ACC_FIELD_CN)
                st.dataframe(df_acc_show, use_container_width=True)
                aid = st.number_input("配件ID修改/删除", min_value=1, value=1, key=f"aid_{table_name}_{sel_cat}")
                a_rec = next((x for x in acc_data if x["id"] == aid), None)
                if a_rec:
                    st.divider()
                    st.subheader("🖼️配件图片管理（可追加、删除单张图片）")
                    current_urls_acc = a_rec.get("image_urls") or []
                    if len(current_urls_acc) > 0:
                        st.image(current_urls_acc, width=220)
                        for idx, img_url in enumerate(current_urls_acc):
                            if st.button(f"删除图片{idx + 1}", key=f"del_img_acc_{table_name}_{aid}_{idx}"):
                                try:
                                    fp = parse_storage_path_from_url(table_name, img_url)
                                    delete_storage_file(table_name, fp)
                                except Exception as e:
                                    st.warning(f"云端文件删除失败:{e}")
                                new_url_list = [u for i, u in enumerate(current_urls_acc) if i != idx]
                                update_product_image_urls(table_name, aid, new_url_list)
                                st.rerun()
                    upload_file_acc = st.file_uploader("追加上传图片(jpg/png/webp)",
                                                       type=["jpg", "jpeg", "png", "webp"],
                                                       key=f"uploader_acc_{table_name}_{aid}")
                    if upload_file_acc is not None:
                        if st.button("确认追加这张图片", key=f"btn_upload_acc_{table_name}_{aid}"):
                            try:
                                new_url = upload_product_image(table_name, aid, upload_file_acc)
                                new_url_list = current_urls_acc + [new_url]
                                update_product_image_urls(table_name, aid, new_url_list)
                                st.success("图片上传成功，刷新页面预览")
                                st.rerun()
                            except Exception as e:
                                st.error(f"上传失败：{str(e)}")

                    acc_edit_cn = [cn for en, cn in ACC_FIELD_CN.items() if en not in ("category", "image_urls")]
                    fld_cn = st.selectbox("选择要修改的字段(中文)", acc_edit_cn, key=f"af_{table_name}_{sel_cat}")
                    fld_en = ACC_FIELD_EN_CN[fld_cn]
                    old_a = a_rec[fld_en]
                    new_a = st.text_input(f"【{fld_cn}】原值:{old_a}", value=str(old_a), key=f"av_{table_name}_{sel_cat}")
                    if st.button("✅更新配件", key=f"au_{table_name}_{sel_cat}"):
                        try:
                            if isinstance(old_a, float):
                                nav = float(new_a)
                            elif isinstance(old_a, int):
                                nav = int(new_a)
                            else:
                                nav = new_a
                            update_accessory_field(table_name, aid, fld_en, nav)
                            st.success("更新成功")
                        except Exception as e:
                            st.error(str(e))
                    if st.button("🗑️删除配件（同步删除全部配件图片）", key=f"adel_{table_name}_{sel_cat}"):
                        delete_accessory_with_images(table_name, aid)
                        st.rerun()

        with sub_t1:
            render_accessory_tab("fence_accessories", ["立柱", "侧条", "凹条", "凸条", "柱座", "柱帽", "膨胀丝"])
        with sub_t2:
            render_accessory_tab("floor_accessories", ["起始扣", "封边", "龙骨", "美固钉", "卡扣", "自攻丝"])


page_settings()
