# -*- coding: utf-8 -*-
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
)


def _display_wall_panel_result(result: dict, currency: str, sym: str):
    st.subheader("📊 计算结果")
    col1, col2, col3 = st.columns(3)
    col1.metric("人民币单支价", f"¥ {result['unit_price_cny']:.2f}")
    col2.metric("欧元单支价", f"€ {result['unit_price_eur']:.2f}")
    col3.metric("美元单支价", f"$ {result['unit_price_usd']:.2f}")
    if currency == "CNY":
        unit_price_target = result["unit_price_cny"]
        total_target = result["pieces_needed"] * unit_price_target
    elif currency == "EUR":
        unit_price_target = result["unit_price_eur"]
        total_target = result["pieces_needed"] * unit_price_target
    else:
        unit_price_target = result["unit_price_usd"]
        total_target = result["pieces_needed"] * unit_price_target
    input_val = (f"{result['input_area']} m²" if "input_area" in result
                 else f"{result['input_length']} m")
    df = pd.DataFrame([{
        "计算方式": result["method"],
        "输入值": input_val,
        "单支米数": f"{result['length_per_piece']} m",
        "所需数量（支）": f"{round(result['pieces_needed'])}",
        f"单支价（{sym}）": f"{unit_price_target:.2f}",
        f"总价（{sym}）": f"{total_target:.2f}",
    }])
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption("📌 UI展示数量四舍五入；单价、总价均保留2位小数，底层计算保留完整高精度，与Excel逻辑一致。")


def _display_fence_result(result: dict, currency: str, cny_to_eur: float,
                          cny_to_usd: float, sym: str, config: dict):
    st.subheader("📊 计算结果")
    rows = []
    qty_map = {}
    weight_key_list = {"post", "side_strip", "groove_strip", "tongue_strip", "post_base", "post_cap"}
    price_9layer_board_eur = 0.0
    price_11layer_board_eur = 0.0
    accessories_total_eur = 0.0
    for item in result["items"]:
        unit_price = convert_currency(item["unit_price_eur"], currency, cny_to_eur, cny_to_usd)
        total = convert_currency(item["total_eur"], currency, cny_to_eur, cny_to_usd)
        raw_qty = item["quantity"]
        disp_qty = round(raw_qty)
        if item["name"] == "1.5米高围栏板（9层）":
            price_9layer_board_eur = item["total_eur"]
        elif item["name"] == "1.8米高围栏板（11层）":
            price_11layer_board_eur = item["total_eur"]
        else:
            accessories_total_eur += item["total_eur"]
        item_key = item.get("key")
        if item_key is not None and item_key in weight_key_list:
            qty_map[item_key] = raw_qty
        rows.append({
            "项目": item["name"],
            "数量": f"{disp_qty}",
            "单位": item["unit"],
            f"单价（{sym}）": f"{unit_price:.2f}",
            f"总价（{sym}）": f"{total:.2f}",
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    total_9_all_eur = price_9layer_board_eur + accessories_total_eur
    total_11_all_eur = price_11layer_board_eur + accessories_total_eur
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        p9 = convert_currency(total_9_all_eur, currency, cny_to_eur, cny_to_usd)
        st.metric("1.5米围栏板（9层）分项总价", f"{sym} {p9:.2f}")
    with col_p2:
        p11 = convert_currency(total_11_all_eur, currency, cny_to_eur, cny_to_usd)
        st.metric("1.8米围栏板（11层）分项总价", f"{sym} {p11:.2f}")
    aw = config["accessory_weight"]
    q_post = qty_map.get("post", 0)
    q_side_strip = qty_map.get("side_strip", 0)
    q_groove_strip = qty_map.get("groove_strip", 0)
    q_tongue_strip = qty_map.get("tongue_strip", 0)
    q_post_base = qty_map.get("post_base", 0)
    q_post_cap = qty_map.get("post_cap", 0)
    weight_sum = (
            aw["post_weight_per_piece"] * q_post
            + aw["side_strip_weight"] * q_side_strip
            + aw["groove_strip_weight"] * q_groove_strip
            + aw["tongue_strip_weight"] * q_tongue_strip
            + aw["post_base_weight"] * q_post_base
            + aw["post_cap_weight"] * q_post_cap
    )
    acc_weight_kg = math.ceil(weight_sum)
    st.metric(label="📦 围栏配件总重量", value=f"{acc_weight_kg} kg")
    st.caption("📌 UI展示数量做四舍五入；重量计算使用底层原始浮点数量，复刻Excel CEILING向上取整逻辑。")


def _display_floor_result(result: dict, currency: str, cny_to_eur: float,
                          cny_to_usd: float, sym: str):
    st.subheader("📊 计算结果")
    rows = []
    for item in result["items"]:
        unit_price = convert_currency(item["unit_price_eur"], currency, cny_to_eur, cny_to_usd)
        total = convert_currency(item["total_eur"], currency, cny_to_eur, cny_to_usd)
        qty_val = round(item["quantity"])
        qty_str = f"{qty_val}"
        if item.get("total_mode") == "by_piece":
            qty_str += f"（约 {round(item['piece_count'])} 支）"
        rows.append({
            "项目": item["name"],
            "数量": qty_str,
            "规格": item["spec"],
            "单位": item["unit"],
            f"单价（{sym}）": f"{unit_price:.2f}",
            f"总价（{sym}）": f"{total:.2f}",
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    total_target = convert_currency(result["total_eur"], currency, cny_to_eur, cny_to_usd)
    st.subheader(f"💰 总价：{sym} {total_target:.2f}")
    st.caption("📌 UI展示数量四舍五入；单价、总价均保留2位小数，底层计算保留完整高精度。")


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
    panel_type = st.selectbox(
        "选择板材类型",
        options=["二代共挤四代长城板", "围栏板", "地板"],
        key="price_panel_type",
    )
    if panel_type == "二代共挤四代长城板":
        wp_cfg = config["wall_panel_price"]
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
                    length_per_piece=length_per_piece,
                    price_per_meter_cny=wp_cfg["price_per_meter_cny"],
                    cny_to_eur=cny_to_eur,
                    cny_to_usd=cny_to_usd,
                    panel_width_m=wp_cfg["panel_width_m"],
                    eur_extra_fee=wp_cfg["eur_extra_fee"],
                    cny_extra_per_meter=wp_cfg["cny_extra_per_meter"],
                )
                result["pieces_needed"] += tolerance_pieces_wall
                original_pieces = result["pieces_needed"]
                if original_pieces < moq_wall:
                    st.warning(f"⚠️计算得到需要 {original_pieces:.0f} 支，小于最小起订量{moq_wall}支，已自动使用MOQ最小起订量")
                    result["pieces_needed"] = moq_wall
                _display_wall_panel_result(result, currency, sym)
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
                    price_per_meter_cny=wp_cfg["price_per_meter_cny"],
                    cny_to_eur=cny_to_eur,
                    cny_to_usd=cny_to_usd,
                    length_per_piece=length_per_piece,
                    panel_width_m=wp_cfg["panel_width_m"],
                    eur_extra_fee=wp_cfg["eur_extra_fee"],
                    cny_extra_per_meter=wp_cfg["cny_extra_per_meter"],
                    extra_pieces=wp_cfg["length_calc_extra_pieces"],
                )
                result["pieces_needed"] += tolerance_pieces_wall_len
                original_pieces = result["pieces_needed"]
                if original_pieces < moq_wall:
                    st.warning(f"⚠️计算得到需要 {original_pieces:.0f} 支，小于最小起订量{moq_wall}支，已自动使用MOQ最小起订量")
                    result["pieces_needed"] = moq_wall
                _display_wall_panel_result(result, currency, sym)
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
            for it in result["items"]:
                if it["name"] in ("1.5米高围栏板（9层）", "1.8米高围栏板（11层）"):
                    it["quantity"] += tolerance_pieces_fence
            for it in result["items"]:
                if it["name"] in ("1.5米高围栏板（9层）", "1.8米高围栏板（11层）"):
                    ori_qty = it["quantity"]
                    if ori_qty < moq_fence:
                        st.warning(f"⚠️[{it['name']}] 计算数量 {ori_qty:.0f}，小于最小起订{moq_fence}，已自动使用MOQ")
                        it["quantity"] = moq_fence
                    it["total_eur"] = it["quantity"] * it["unit_price_eur"]
            total_eur_new = 0.0
            for it in result["items"]:
                total_eur_new += it["total_eur"]
            result["total_eur"] = total_eur_new
            _display_fence_result(result, currency, cny_to_eur, cny_to_usd, sym, config)
            st.session_state["last_fence_length"] = fence_length
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
            _display_floor_result(result, currency, cny_to_eur, cny_to_usd, sym)


page_price_calc()
