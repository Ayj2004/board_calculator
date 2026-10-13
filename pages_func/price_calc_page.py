# -- coding: utf-8 --
"""价格计算页面"""
import math
import pandas as pd
import streamlit as st
from calculator.price_calc import (
    calc_wall_panel_by_area,
    calc_wall_panel_by_length,
    calc_fence,
    calc_floor,
    convert_currency,
    currency_symbol,
    gen_quote_text_wall,
    gen_quote_text_fence_single,
    gen_quote_text_floor,
    calc_accessory_weight
)
from config_default import WALL_PANEL_PRODUCTS


def _display_wall_panel_result(result: dict, currency: str, sym: str):
    st.subheader("📊 计算结果")
    col1, col2, col3 = st.columns(3)
    col1.metric("人民币单支价", f"¥ {result['unit_price_cny']:.2f}")
    col2.metric("欧元单支价", f"€ {result['unit_price_eur']:.2f}")
    col3.metric("美元单支价", f"$ {result['unit_price_usd']:.2f}")
    if currency == "CNY":
        unit_price_target = result["unit_price_cny"]
    elif currency == "EUR":
        unit_price_target = result["unit_price_eur"]
    else:
        unit_price_target = result["unit_price_usd"]
    # 【修改点】ceil → round四舍五入
    disp_qty = int(round(result["pieces_needed"]))
    disp_unit_price = round(unit_price_target, 2)
    disp_total = round(disp_unit_price * disp_qty, 2)
    input_val = (f"{result['input_area']} m²" if "input_area" in result
                 else f"{result['input_length']} m")
    df = pd.DataFrame([{
        "计算方式": result["method"],
        "输入值": input_val,
        "单支米数": f"{result['length_per_piece']} m",
        "所需数量（支）": f"{disp_qty}",
        f"单支价（{sym}）": f"{disp_unit_price:.2f}",
        f"总价（{sym}）": f"{disp_total:.2f}",
    }])
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption("📌 UI展示数量四舍五入；总价 = 页面展示2位小数单价 × 展示数量。")
    # 返回渲染数据，直接喂给报价
    return {
        "disp_qty": disp_qty,
        "disp_unit_price": disp_unit_price,
        "disp_total": disp_total,
        "input_label": input_val,
        "len_piece": result["length_per_piece"],
    }


# ===== 【修复版：表格、报价文字、总价三者完全对齐，逐行求和｜数量改为四舍五入】 =====
def _display_fence_result(result: dict, currency: str, cny_to_eur: float,
                          cny_to_usd: float, sym: str, config: dict, tol_qty: int, moq_fence: int):
    st.subheader("📊 计算结果")
    rows = []
    qty_map = {}
    weight_key_list = {"post", "side_strip", "groove_strip", "tongue_strip", "post_base", "post_cap"}
    # 拿到原始数据
    board9_raw = result["board_9"]
    board11_raw = result["board_11"]
    acc_items_raw = result["accessory_items"]
    # ========== 处理9层板（1.5米方案） ==========
    b9_qty = board9_raw["quantity"] + tol_qty
    if b9_qty < moq_fence:
        b9_qty = moq_fence
    disp_9 = int(round(b9_qty))
    unit9_cur = convert_currency(board9_raw["unit_price_eur"], currency, cny_to_eur, cny_to_usd)
    unit9_cur = round(unit9_cur, 2)
    sub9_cur = round(unit9_cur * disp_9, 2)
    # ========== 处理11层板（1.8米方案） ==========
    b11_qty = board11_raw["quantity"] + tol_qty
    if b11_qty < moq_fence:
        b11_qty = moq_fence
    disp_11 = int(round(b11_qty))
    unit11_cur = convert_currency(board11_raw["unit_price_eur"], currency, cny_to_eur, cny_to_usd)
    unit11_cur = round(unit11_cur, 2)
    sub11_cur = round(unit11_cur * disp_11, 2)
    # 配件行（配件不加容错，不加MOQ）
    accessory_lines = []
    acc_subtotal_list = []
    for it in acc_items_raw:
        unit_price = convert_currency(it["unit_price_eur"], currency, cny_to_eur, cny_to_usd)
        # 【修改点】配件数量四舍五入
        disp_qty = int(round(it["quantity"]))
        disp_unit_price = round(unit_price, 2)
        disp_line_total = round(disp_unit_price * disp_qty, 2)
        accessory_lines.append({
            "name": it["name"],
            "need_qty": disp_qty,
            "tol": 0,
            "total_qty": disp_qty,
            "unit": it["unit"],
            "unit_price": disp_unit_price,
            "subtotal": disp_line_total,
        })
        acc_subtotal_list.append(disp_line_total)
        ik = it.get("key")
        if ik and ik in weight_key_list:
            qty_map[ik] = it["quantity"]
    acc_sum = sum(acc_subtotal_list)
    # 构建报价用board行
    line_9 = {
        "name": board9_raw["name"],
        "need_qty": int(round(board9_raw["quantity"])),
        "tol": tol_qty,
        "total_qty": disp_9,
        "unit": board9_raw["unit"],
        "unit_price": unit9_cur,
        "subtotal": sub9_cur,
    }
    line_11 = {
        "name": board11_raw["name"],
        "need_qty": int(round(board11_raw["quantity"])),
        "tol": tol_qty,
        "total_qty": disp_11,
        "unit": board11_raw["unit"],
        "unit_price": unit11_cur,
        "subtotal": sub11_cur,
    }
    # ========= 明细表格渲染：主板叠加容错，配件不变 =========
    for item in result["table_items"]:
        up = convert_currency(item["unit_price_eur"], currency, cny_to_eur, cny_to_usd)
        if item["name"] == board9_raw["name"]:
            base_qty = item["quantity"] + tol_qty
            if base_qty < moq_fence:
                base_qty = moq_fence
            dq = int(round(base_qty))
        elif item["name"] == board11_raw["name"]:
            base_qty = item["quantity"] + tol_qty
            if base_qty < moq_fence:
                base_qty = moq_fence
            dq = int(round(base_qty))
        else:
            dq = int(round(item["quantity"]))
        dup = round(up, 2)
        dlt = round(dup * dq, 2)
        rows.append({
            "项目": item["name"],
            "数量": f"{dq}",
            "单位": item["unit"],
            f"单价（{sym}）": f"{dup:.2f}",
            f"总价（{sym}）": f"{dlt:.2f}",
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    # ✅【修复核心】总价 = 板材小计 + 配件逐行round之后的求和，不再复用上游accessory_total_eur
    total_9_all = sub9_cur + acc_sum
    total_11_all = sub11_cur + acc_sum
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.metric("1.5米围栏板（9层）整套总价", f"{sym} {total_9_all:.2f}")
    with col_p2:
        st.metric("1.8米围栏板（11层）整套总价", f"{sym} {total_11_all:.2f}")
    # 重量（维持原有逻辑，配件原始浮点重量 + ceil向上取整，不动）
    aw_cfg = config["accessory_weight"]
    weight_sum = (
        aw_cfg["post_weight_per_piece"] * qty_map.get("post", 0)
        + aw_cfg["side_strip_weight"] * qty_map.get("side_strip", 0)
        + aw_cfg["groove_strip_weight"] * qty_map.get("groove_strip", 0)
        + aw_cfg["tongue_strip_weight"] * qty_map.get("tongue_strip", 0)
        + aw_cfg["post_base_weight"] * qty_map.get("post_base", 0)
        + aw_cfg["post_cap_weight"] * qty_map.get("post_cap", 0)
    )
    acc_weight_kg = math.ceil(weight_sum)
    st.metric(label="📦 围栏配件总重量", value=f"{acc_weight_kg} kg")
    st.caption("📌 UI展示数量四舍五入；明细总价 = 页面展示2位小数单价 × 展示数量；整套合计为所有明细行求和；重量使用原始浮点数量计算并向上取整。")
    # 报价文本
    quote_15_text = gen_quote_text_fence_single(
        fence_length=result["fence_length"],
        height_name="1.5米高围栏（9层板方案）",
        board_line=line_9,
        accessory_line_list=accessory_lines,
        total_sum=total_9_all,
        sym=sym
    )
    quote_18_text = gen_quote_text_fence_single(
        fence_length=result["fence_length"],
        height_name="1.8米高围栏（11层板方案）",
        board_line=line_11,
        accessory_line_list=accessory_lines,
        total_sum=total_11_all,
        sym=sym
    )
    return {
        "quote_15": quote_15_text,
        "quote_18": quote_18_text,
        "total_15": total_9_all,
        "total_11": total_11_all,
        "fence_length": result["fence_length"],
    }


def _display_floor_result(result: dict, currency: str, cny_to_eur: float,
                          cny_to_usd: float, sym: str, tol_qty: int):
    st.subheader("📊 计算结果")
    rows = []
    quote_line_data = []
    total_sum_target = 0.0
    for item in result["items"]:
        unit_price = convert_currency(item["unit_price_eur"], currency, cny_to_eur, cny_to_usd)
        if item.get("total_mode") == "by_piece":
            qty_val = int(round(item["piece_count"]))
            qty_str = f"{qty_val}"
        else:
            qty_val = int(round(item["quantity"]))
            qty_str = f"{qty_val}"
        if item.get("total_mode") == "by_piece":
            qty_str += f"（约 {int(round(item['piece_count']))} 支）"
        disp_unit_price = round(unit_price, 2)
        disp_line_total = round(disp_unit_price * qty_val, 2)
        rows.append({
            "项目": item["name"],
            "数量": qty_str,
            "规格": item["spec"],
            "单位": item["unit"],
            f"单价（{sym}）": f"{disp_unit_price:.2f}",
            f"总价（{sym}）": f"{disp_line_total:.2f}",
        })
        # 容错只给WPC地板
        if item["name"] == "WPC地板":
            need_qty = qty_val - tol_qty
            line_tol = tol_qty
        else:
            need_qty = qty_val
            line_tol = 0
        quote_line_data.append({
            "name": item["name"],
            "need_qty": need_qty,
            "tol": line_tol,
            "total_qty": qty_val,
            "unit": item["unit"],
            "unit_price": disp_unit_price,
            "subtotal": disp_line_total,
        })
        total_sum_target += disp_line_total
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    # 核心修改：不再读取上游 result["total_eur"]，改用逐行累加的合计
    st.subheader(f"💰 总价：{sym} {total_sum_target:.2f}")
    st.caption("📌 UI展示数量四舍五入；明细总价 = 页面展示2位小数单价 × 展示数量；整套合计为所有明细行求和。")
    return {
        "line_list": quote_line_data,
        "total_sum": total_sum_target,
        "area": result["area"],
    }




def page_price_calc():
    config = st.session_state["config"]
    st.header("💰 价格计算")
    col_cur, _ = st.columns([1, 3])
    with col_cur:
        currency = st.selectbox(
            "选择显示币种",
            options=["EUR", "USD", "CNY"],
            format_func=lambda x: {"EUR": "欧元 €", "USD": "美元 $", "CNY": "人民币 ¥"}[x],
            key="price_currency",
        )
    cny_to_eur = config["exchange_rate"]["cny_to_eur"]
    cny_to_usd = config["exchange_rate"]["cny_to_usd"]
    sym = currency_symbol(currency)
    st.divider()
    wall_product_names = [p["name"] for p in WALL_PANEL_PRODUCTS]
    panel_type = st.selectbox(
        "选择板材类型",
        options=wall_product_names + ["围栏板", "地板"],
        key="price_panel_type",
    )
    quote_text = ""
    quote_15_text = ""
    quote_18_text = ""
    if panel_type in wall_product_names:
        product = next(p for p in WALL_PANEL_PRODUCTS if p["name"] == panel_type)
        wp_cfg = config[product["price_key"]]
        moq_wall = wp_cfg["moq_pieces"]
        calc_method = st.selectbox(
            "计算方式",
            options=["按面积计算", "按长度计算"],
            key="wp_calc_method",
        )
        if calc_method == "按面积计算":
            col1, col2, col3 = st.columns(3)
            with col1:
                area = st.number_input(
                    "面积（平方米）", min_value=0.0, value=10.0, step=1.0, key="wp_area"
                )
            with col2:
                length_per_piece = st.number_input(
                    "单支米数", min_value=0.1,
                    value=float(wp_cfg["default_length_per_piece"]),
                    step=0.1, key="wp_length",
                    help="单支板材的长度（米），仅按面积计算时用于价格计算"
                )
            with col3:
                tolerance_pieces_wall = st.number_input("容错支数", min_value=0, value=5, step=1, key="wp_tol_area")
            if st.button("计算", type="primary", key="wp_area_calc"):
                result = calc_wall_panel_by_area(
                    area_sqm=area,
                    product_price_config=wp_cfg,
                    actual_length_per_piece=length_per_piece,
                    cny_to_eur=cny_to_eur,
                    cny_to_usd=cny_to_usd,
                )
                result["pieces_needed"] += tolerance_pieces_wall
                original_pieces = result["pieces_needed"]
                if original_pieces < moq_wall:
                    st.warning(f"⚠️计算得到需要 {original_pieces:.0f} 支，小于最小起订量{moq_wall}支，已自动使用MOQ最小起订量")
                    result["pieces_needed"] = moq_wall
                render_data = _display_wall_panel_result(result, currency, sym)
                raw_need = render_data["disp_qty"] - tolerance_pieces_wall
                quote_text = gen_quote_text_wall(
                    input_label=render_data["input_label"],
                    len_piece=render_data["len_piece"],
                    product_name=product["name"],
                    raw_need_qty=raw_need,
                    tolerance_qty=tolerance_pieces_wall,
                    total_qty=render_data["disp_qty"],
                    disp_unit_price=render_data["disp_unit_price"],
                    disp_total=render_data["disp_total"],
                    sym=sym
                )
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                length = st.number_input(
                    "长度（米）", min_value=0.0, value=10.0, step=1.0, key="wp_length_input"
                )
            with col2:
                length_per_piece = st.number_input(
                    "单支米数（仅用于计算单支价，不影响数量）",
                    min_value=0.1,
                    value=float(wp_cfg["default_length_per_piece"]),
                    step=0.1, key="wp_len_piece",
                )
            with col3:
                tolerance_pieces_wall_len = st.number_input("容错支数", min_value=0, value=5, step=1, key="wp_tol_len")
            if st.button("计算", type="primary", key="wp_length_calc"):
                result = calc_wall_panel_by_length(
                    length_m=length,
                    product_price_config=wp_cfg,
                    actual_length_per_piece=length_per_piece,
                    cny_to_eur=cny_to_eur,
                    cny_to_usd=cny_to_usd,
                )
                result["pieces_needed"] += tolerance_pieces_wall_len
                original_pieces = result["pieces_needed"]
                if original_pieces < moq_wall:
                    st.warning(f"⚠️计算得到需要 {original_pieces:.0f} 支，小于最小起订量{moq_wall}支，已自动使用MOQ最小起订量")
                    result["pieces_needed"] = moq_wall
                render_data = _display_wall_panel_result(result, currency, sym)
                raw_need = render_data["disp_qty"] - tolerance_pieces_wall_len
                quote_text = gen_quote_text_wall(
                    input_label=render_data["input_label"],
                    len_piece=render_data["len_piece"],
                    product_name=product["name"],
                    raw_need_qty=raw_need,
                    tolerance_qty=tolerance_pieces_wall_len,
                    total_qty=render_data["disp_qty"],
                    disp_unit_price=render_data["disp_unit_price"],
                    disp_total=render_data["disp_total"],
                    sym=sym
                )
    elif panel_type == "围栏板":
        st.info("💡 围栏板原始配置存储欧元价格；可切换显示CNY / USD；非常规尺寸价格另算。")
        fp_cfg = config["fence_price"]
        moq_fence = fp_cfg["moq_pieces"]
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            fence_length = st.number_input(
                "围栏长度（米）", min_value=0.0, value=10.0, step=1.0, key="fence_length"
            )
        with col_f2:
            tolerance_pieces_fence = st.number_input("围栏板主板容错片数", min_value=0, value=5, step=1, key="fence_tol")
        if st.button("计算", type="primary", key="fence_calc"):
            result = calc_fence(fence_length, config["fence_price"], cny_to_eur, cny_to_usd)
            render_data = _display_fence_result(
                result, currency, cny_to_eur, cny_to_usd, sym, config, tolerance_pieces_fence, moq_fence
            )
            st.session_state["last_fence_length"] = fence_length
            quote_15_text = render_data["quote_15"]
            quote_18_text = render_data["quote_18"]
    elif panel_type == "地板":
        st.info("💡 地板原始配置存储欧元价格；可切换显示CNY / USD；龙骨和封边为标准2.9米尺寸，定制价格另算。")
        fl_cfg = config["floor_price"]
        moq_floor = fl_cfg["moq_pieces"]
        col_fl1, col_fl2 = st.columns(2)
        with col_fl1:
            floor_area = st.number_input(
                "地板面积（平方米）", min_value=0.0, value=10.0, step=1.0, key="floor_area"
            )
        with col_fl2:
            tolerance_pieces_floor = st.number_input("地板主板容错支数", min_value=0, value=5, step=1, key="floor_tol")
        if st.button("计算", type="primary", key="floor_calc"):
            result = calc_floor(floor_area, config["floor_price"], cny_to_eur, cny_to_usd)
            for it in result["items"]:
                if it["name"] == "WPC地板":
                    it["quantity"] += tolerance_pieces_floor
                    ori_qty = it["quantity"]
                    if ori_qty < moq_floor:
                        st.warning(f"⚠️WPC地板计算得到 {ori_qty:.0f}支，小于最小起订{moq_floor}支，已自动使用MOQ最小起订量")
                        it["quantity"] = moq_floor
                        it["total_eur"] = it["quantity"] * it["unit_price_eur"]
            total_eur_new = 0.0
            for it in result["items"]:
                total_eur_new += it["total_eur"]
            result["total_eur"] = total_eur_new
            render_data = _display_floor_result(result, currency, cny_to_eur, cny_to_usd, sym, tolerance_pieces_floor)
            quote_text = gen_quote_text_floor(
                area=render_data["area"],
                product_name="WPC地板",
                line_list=render_data["line_list"],
                total_sum=render_data["total_sum"],
                sym=sym
            )
    # ===== 修改报价模板渲染：围栏输出两个独立文本框 =====
    if quote_text:
        st.divider()
        st.subheader("📝 报价模板")
        st.text_area("可直接复制发给客户", value=quote_text, height=220)
    if quote_15_text and quote_18_text:
        st.divider()
        st.subheader("📝 围栏两套方案报价模板")
        st.markdown("方案A：1.5米高（9层板）")
        st.text_area("方案A", value=quote_15_text, height=220)
        st.markdown("方案B：1.8米高（11层板）")
        st.text_area("方案B", value=quote_18_text, height=220)


page_price_calc()
