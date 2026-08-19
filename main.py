# -*- coding: utf-8 -*-
"""
WPC 板材计算器 —— Streamlit + Supabase版本
app_config改为key‑value行式存储，不再单条jsonb大字段
全局单套配置
修改点：保存仅更新变更字段，保存后重新从DB加载配置保证UI与数据库完全一致
"""


import copy
import json


import streamlit as st
import pandas as pd
from supabase import create_client, Client


# 导入本地模块
import sys
sys.path.insert(0, sys.path[0])
from config_default import DEFAULT_CONFIG
from calculator.price_calc import (
    calc_wall_panel_by_area,
    calc_wall_panel_by_length,
    calc_fence,
    calc_floor,
    calc_accessory_weight,
    convert_currency,
    currency_symbol,
)
from calculator.package_calc import calc_package


# ===================== Supabase 客户端初始化 =====================
from postgrest.exceptions import APIError



@st.cache_resource(show_spinner="连接Supabase...")
def get_supabase_client() -> Client:
    """初始化supabase客户端，cache_resource只实例化一次"""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)



def dict_to_kv_rows(d: dict, prefix: str = "") -> list[dict]:
    """
    嵌套字典转为扁平key‑value行
    {"a":{"b":1}} → [{"key":"a.b","value":1}]
    """
    rows = []
    for k, v in d.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            rows.extend(dict_to_kv_rows(v, full_key))
        else:
            rows.append({"key": full_key, "value": v})
    return rows



def kv_rows_to_dict(rows: list[dict]) -> dict:
    """
    数据库扁平key‑value列表还原为嵌套字典
    [{"key":"a.b","value":1}] → {"a":{"b":1}}
    """
    root = {}
    for row in rows:
        key_str = row["key"]
        val = row["value"]
        parts = key_str.split(".")
        node = root
        for part in parts[:-1]:
            if part not in node:
                node[part] = {}
            node = node[part]
        last = parts[-1]
        node[last] = val
    return root



def diff_nested_dict(old: dict, new: dict, prefix: str = "") -> list[str]:
    """
    递归对比两个嵌套dict，返回发生变更的扁平key路径列表
    diff_nested_dict({"a":{"b":1}}, {"a":{"b":2}}) → ["a.b"]
    """
    changed_keys = []
    for k in set(list(old.keys()) + list(new.keys())):
        full_key = f"{prefix}.{k}" if prefix else k
        old_val = old.get(k)
        new_val = new.get(k)
        if isinstance(old_val, dict) and isinstance(new_val, dict):
            changed_keys.extend(diff_nested_dict(old_val, new_val, full_key))
        else:
            if old_val != new_val:
                changed_keys.append(full_key)
    return changed_keys



def extract_kv_by_keys(full_dict: dict, target_keys: list[str]) -> list[dict]:
    """
    从完整嵌套dict，只提取target_keys指定的key‑value行
    """
    all_rows = dict_to_kv_rows(full_dict)
    return [r for r in all_rows if r["key"] in target_keys]



def load_config_supabase() -> dict:
    """从supabase加载配置；无数据返回DEFAULT_CONFIG，首次自动初始化全部行"""
    try:
        supabase = get_supabase_client()
        resp = supabase.table("app_config").select("key,value").execute()
        rows = resp.data or []
        if len(rows) == 0:
            # 数据库为空，写入默认配置
            default_cfg = copy.deepcopy(DEFAULT_CONFIG)
            save_config_supabase(default_cfg)
            return default_cfg
        # 从kv行还原嵌套dict
        user_cfg = kv_rows_to_dict(rows)
        base = copy.deepcopy(DEFAULT_CONFIG)
        return _deep_merge(base, user_cfg)
    except APIError as e:
        st.warning(f"⚠️ Supabase读取失败，使用本地出厂配置：{e}")
        return copy.deepcopy(DEFAULT_CONFIG)



def save_config_supabase(cfg: dict):
    """【全量保存】把嵌套dict展开为全部kv行，批量upsert到app_config（用于恢复出厂）"""
    supabase = get_supabase_client()
    kv_list = dict_to_kv_rows(cfg)
    resp = supabase.table("app_config").upsert(kv_list).execute()
    return resp



def save_changed_config_supabase(old_cfg: dict, new_cfg: dict):
    """【增量保存】仅对比新旧配置，只把变更字段upsert入库，不变更key不操作数据库"""
    changed_key_list = diff_nested_dict(old_cfg, new_cfg)
    if not changed_key_list:
        return None, "no_change"
    changed_kv = extract_kv_by_keys(new_cfg, changed_key_list)
    supabase = get_supabase_client()
    resp = supabase.table("app_config").upsert(changed_kv).execute()
    return resp, "ok"



def reset_config_supabase() -> dict:
    """恢复出厂默认：直接把DEFAULT_CONFIG全部写入数据库，覆盖全部key"""
    default = copy.deepcopy(DEFAULT_CONFIG)
    save_config_supabase(default)
    return default



def _deep_merge(base: dict, override: dict) -> dict:
    """深度合并字典，override键覆盖base；base会被原地修改，请传入deepcopy副本"""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base



# ============================================================
# 页面：价格计算（完全原样，无改动）
# ============================================================
def page_price_calc(config: dict):
    """价格计算页面"""
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


        calc_method = st.selectbox(
            "计算方式",
            options=["按面积计算", "按长度计算"],
            key="wp_calc_method",
        )


        if calc_method == "按面积计算":
            col1, col2 = st.columns(2)
            with col1:
                area = st.number_input(
                    "面积（平方米）", min_value=0.0, value=10.0, step=1.0, key="wp_area"
                )
            with col2:
                length_per_piece = st.number_input(
                    "单支米数", min_value=0.1,
                    value=float(wp_cfg["default_length_per_piece"]),
                    step=0.1, key="wp_length",
                    help="单支板材的长度（米），仅按面积计算时需要"
                )


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
                _display_wall_panel_result(result, currency, cny_to_eur, cny_to_usd, sym)


        else:
            col1, col2 = st.columns(2)
            with col1:
                length = st.number_input(
                    "长度（米）", min_value=0.0, value=10.0, step=1.0, key="wp_length_input"
                )
            with col2:
                length_per_piece = st.number_input(
                    "单支米数（用于计算单支价）",
                    min_value=0.1,
                    value=float(wp_cfg["default_length_per_piece"]),
                    step=0.1, key="wp_len_piece",
                )


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
                _display_wall_panel_result(result, currency, cny_to_eur, cny_to_usd, sym)


    elif panel_type == "围栏板":
        st.info("💡 围栏板所有单价均为带利润价格；非常规尺寸价格另算。")
        fence_length = st.number_input(
            "围栏长度（米）", min_value=0.0, value=10.0, step=1.0, key="fence_length"
        )


        if st.button("计算", type="primary", key="fence_calc"):
            result = calc_fence(fence_length, config["fence_price"], cny_to_eur, cny_to_usd)
            _display_fence_result(result, currency, cny_to_eur, cny_to_usd, sym)
            acc_result = calc_accessory_weight(
                fence_length, config["fence_price"], config["accessory_weight"]
            )
            st.subheader("📦 配件重量")
            st.metric("配件总重量", f"{acc_result['weight_kg']} kg")
            st.session_state["last_fence_length"] = fence_length


    elif panel_type == "地板":
        st.info("💡 地板均为带利润价格；龙骨和封边为标准2.9米尺寸，定制价格另算。")
        floor_area = st.number_input(
            "地板面积（平方米）", min_value=0.0, value=10.0, step=1.0, key="floor_area"
        )


        if st.button("计算", type="primary", key="floor_calc"):
            result = calc_floor(floor_area, config["floor_price"], cny_to_eur, cny_to_usd)
            _display_floor_result(result, currency, cny_to_eur, cny_to_usd, sym)



def _display_wall_panel_result(result: dict, currency: str, cny_to_eur: float,
                               cny_to_usd: float, sym: str):
    st.subheader("📊 计算结果")
    col1, col2, col3 = st.columns(3)
    col1.metric("人民币单支价", f"¥ {result['unit_price_cny']:.2f}")
    col2.metric("欧元单支价", f"€ {result['unit_price_eur']:.2f}")
    col3.metric("美元单支价", f"$ {result['unit_price_usd']:.2f}")


    unit_price_target = convert_currency(result["unit_price_eur"], currency, cny_to_eur, cny_to_usd)
    total_target = convert_currency(result["total_eur"], currency, cny_to_eur, cny_to_usd)


    input_val = (f"{result['input_area']} m²" if "input_area" in result
                 else f"{result['input_length']} m")


    df = pd.DataFrame([{
        "计算方式": result["method"],
        "输入值": input_val,
        "单支米数": f"{result['length_per_piece']} m",
        "所需数量（支）": f"{result['pieces_needed']:.2f}",
        f"单支价（{sym}）": f"{unit_price_target:.2f}",
        f"总价（{sym}）": f"{total_target:.2f}",
    }])
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption("📌 支数与总价展示均四舍五入，内部计算按精确值进行，与Excel逻辑一致。")



def _display_fence_result(result: dict, currency: str, cny_to_eur: float,
                          cny_to_usd: float, sym: str):
    st.subheader("📊 计算结果")
    st.metric("所需立柱数", f"{result['post_count']:.2f} 根")


    rows = []
    for item in result["items"]:
        unit_price = convert_currency(item["unit_price_eur"], currency, cny_to_eur, cny_to_usd)
        total = convert_currency(item["total_eur"], currency, cny_to_eur, cny_to_usd)
        rows.append({
            "项目": item["name"],
            "数量": f"{item['quantity']:.2f}",
            "单位": item["unit"],
            f"单价（{sym}）": f"{unit_price:.2f}",
            f"总价（{sym}）": f"{total:.2f}",
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


    total_target = convert_currency(result["total_eur"], currency, cny_to_eur, cny_to_usd)
    st.subheader(f"💰 总价：{sym} {total_target:.2f}")
    st.caption("📌 数量与总价展示均四舍五入，内部计算按精确值进行。")



def _display_floor_result(result: dict, currency: str, cny_to_eur: float,
                          cny_to_usd: float, sym: str):
    st.subheader("📊 计算结果")


    rows = []
    for item in result["items"]:
        unit_price = convert_currency(item["unit_price_eur"], currency, cny_to_eur, cny_to_usd)
        total = convert_currency(item["total_eur"], currency, cny_to_eur, cny_to_usd)
        qty_str = f"{item['quantity']:.2f}"
        if item.get("total_mode") == "by_piece":
            qty_str += f"（约 {item['piece_count']:.2f} 支）"
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
    st.caption("📌 数量与总价展示均四舍五入，内部计算按精确值进行。")



# ============================================================
# 页面：包装计算（原样无改动）
# ============================================================
def page_package_calc(config: dict):
    st.header("📦 包装计算")


    panel_type = st.selectbox(
        "选择板材类型",
        options=["二代共挤四代长城板", "围栏板", "地板"],
        key="pkg_panel_type",
    )


    type_key_map = {
        "二代共挤四代长城板": "wall_panel",
        "围栏板": "fence",
        "地板": "floor",
    }
    pkg_cfg = config["package"][type_key_map[panel_type]]


    col1, col2, col3 = st.columns(3)
    with col1:
        pieces = st.number_input(
            "数量（支）", min_value=1, value=100, step=1,
            key=f"pkg_pieces_{panel_type}",
        )
    with col2:
        length_per_piece = st.number_input(
            "单支长度（米）",
            min_value=0.1,
            value=float(pkg_cfg["default_length_per_piece"]),
            step=0.1,
            key=f"pkg_length_{panel_type}",
            help=f"该板材默认 {pkg_cfg['default_length_per_piece']} 米，可修改",
        )
    with col3:
        weight_per_meter = st.number_input(
            "米重（KG/米）",
            min_value=0.01,
            value=float(pkg_cfg["default_weight_per_meter"]),
            step=0.01,
            key=f"pkg_weight_{panel_type}",
            help=f"该板材默认 {pkg_cfg['default_weight_per_meter']} KG/米，可修改",
        )


    if st.button("计算包装", type="primary", key="pkg_calc"):
        result = calc_package(pieces, length_per_piece, weight_per_meter, pkg_cfg)
        _display_package_result(result)


    st.divider()


    st.subheader("🔧 配件重量计算")
    st.caption("配件重量依赖围栏板的立柱、侧条、凹条、凸条、柱座、柱帽数量")
    default_fence_len = st.session_state.get("last_fence_length", 10.0)
    fence_length = st.number_input(
        "围栏长度（米）", min_value=0.0, value=float(default_fence_len),
        step=1.0, key="acc_fence_length",
    )
    if st.button("计算配件重量", key="acc_calc"):
        acc_result = calc_accessory_weight(
            fence_length, config["fence_price"], config["accessory_weight"]
        )
        col_a, col_b = st.columns(2)
        col_a.metric("立柱数", f"{acc_result['post_count']:.2f}")
        col_b.metric("配件总重量", f"{acc_result['weight_kg']} kg")
        st.caption(f"原始计算值（未取整）：{acc_result['raw_weight']:.2f} kg → 向上取整为 {acc_result['weight_kg']} kg")



def _display_package_result(result: dict):
    st.subheader("📊 计算结果")
    st.info(f"计算模式：{result['mode']}")


    col1, col2, col3 = st.columns(3)
    col1.metric("包装长度", f"{result['pkg_length']:.3f} m")
    col2.metric("包装宽度", f"{result['pkg_width']:.3f} m")
    col3.metric("包装高度", f"{result['pkg_height']:.3f} m")


    col4, col5, col6 = st.columns(3)
    col4.metric("单托盘体积", f"{result['single_pallet_volume']:.4f} m³")
    col5.metric("托盘数量", f"{result['pallet_count']} 个")
    col6.metric("包装总方数", f"{result['total_cbm']} m³")


    st.metric("包装总重量", f"{result['total_weight_kg']} kg")


    df = pd.DataFrame([{
        "板材数量（支）": result["pieces"],
        "单支长度（m）": result["length_per_piece"],
        "米重（KG/m）": result["weight_per_meter"],
        "包装长（m）": round(result["pkg_length"], 3),
        "包装宽（m）": round(result["pkg_width"], 3),
        "包装高（m）": round(result["pkg_height"], 3),
        "单托盘体积（m³）": round(result["single_pallet_volume"], 4),
        "托盘数": result["pallet_count"],
        "总方数（m³）": result["total_cbm"],
        "总重量（KG）": result["total_weight_kg"],
    }])
    st.dataframe(df, use_container_width=True, hide_index=True)



# ============================================================
# 页面：设置（修改保存逻辑：增量更新；保存后重读DB保证UI和DB一致）
# ============================================================
def page_settings(original_config: dict) -> dict:
    st.header("⚙️ 设置")
    modified = copy.deepcopy(original_config)
    rev = st.session_state["settings_revision"]


    st.subheader("💱 汇率设置")
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        modified["exchange_rate"]["cny_to_eur"] = st.number_input(
            "人民币兑欧元（CNY/EUR）",
            min_value=0.01, value=float(modified["exchange_rate"]["cny_to_eur"]),
            step=0.01, key=f"set_eur_rev{rev}",
        )
    with col_r2:
        modified["exchange_rate"]["cny_to_usd"] = st.number_input(
            "人民币兑美元（CNY/USD）",
            min_value=0.01, value=float(modified["exchange_rate"]["cny_to_usd"]),
            step=0.01, key=f"set_usd_rev{rev}",
        )


    st.divider()
    st.subheader("🏗️ 二代共挤四代长城板 —— 价格参数")
    wp = modified["wall_panel_price"]
    col_w1, col_w2, col_w3 = st.columns(3)
    with col_w1:
        wp["price_per_meter_cny"] = st.number_input(
            "含税单价（元/米）", min_value=0.0,
            value=float(wp["price_per_meter_cny"]), step=0.01, key="set_wp_price",
        )
        wp["default_length_per_piece"] = st.number_input(
            "默认单支米数", min_value=0.1,
            value=float(wp["default_length_per_piece"]), step=0.1, key="set_wp_len",
        )
    with col_w2:
        wp["panel_width_m"] = st.number_input(
            "板材宽度（米）", min_value=0.01,
            value=float(wp["panel_width_m"]), step=0.01, key="set_wp_width",
        )
        wp["eur_extra_fee"] = st.number_input(
            "欧元额外加价（€/支）", min_value=0.0,
            value=float(wp["eur_extra_fee"]), step=0.01, key="set_wp_eur_extra",
        )
    with col_w3:
        wp["cny_extra_per_meter"] = st.number_input(
            "人民币每米加价（元）", min_value=0.0,
            value=float(wp["cny_extra_per_meter"]), step=0.1, key="set_wp_cny_extra",
        )
        wp["length_calc_extra_pieces"] = st.number_input(
            "按长度计算余量（支）", min_value=0,
            value=int(wp["length_calc_extra_pieces"]), step=1, key="set_wp_extra_pcs",
        )


    st.divider()
    st.subheader("🚧 围栏板 —— 配件单价（欧元）")
    fp = modified["fence_price"]
    fence_items = [
        ("post", "立柱"),
        ("fence_board_9", "围栏板(9片/段)"),
        ("fence_board_11", "围栏板(11片/段)"),
        ("side_strip", "侧条"),
        ("groove_strip", "凹条"),
        ("tongue_strip", "凸条"),
        ("post_base", "柱座"),
        ("post_cap", "柱帽"),
        ("expansion_bolt", "膨胀丝"),
    ]
    cols = st.columns(3)
    for idx, (key, label) in enumerate(fence_items):
        with cols[idx % 3]:
            fp[key]["unit_price_eur"] = st.number_input(
                f"{label}（€）", min_value=0.0,
                value=float(fp[key]["unit_price_eur"]), step=0.01,
                key=f"set_fence_{key}",
            )
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        fp["section_length_m"] = st.number_input(
            "每段长度（米）", min_value=0.1,
            value=float(fp["section_length_m"]), step=0.1, key="set_fence_sec",
        )
    with col_f2:
        fp["boards_per_section_9"] = st.number_input(
            "每段板数(9片方案)", min_value=1,
            value=int(fp["boards_per_section_9"]), step=1, key="set_fence_b9",
        )
    with col_f3:
        fp["boards_per_section_11"] = st.number_input(
            "每段板数(11片方案)", min_value=1,
            value=int(fp["boards_per_section_11"]), step=1, key="set_fence_b11",
        )
    fp["bolts_per_post"] = st.number_input(
        "每根立柱膨胀丝数", min_value=1,
        value=int(fp["bolts_per_post"]), step=1, key="set_fence_bolts",
    )


    st.divider()
    st.subheader("🪵 地板 —— 配件单价（欧元）及参数")
    flp = modified["floor_price"]
    col_fl1, col_fl2, col_fl3 = st.columns(3)
    with col_fl1:
        flp["wpc_floor"]["unit_price_eur"] = st.number_input(
            "WPC地板单价（€/支）", min_value=0.0,
            value=float(flp["wpc_floor"]["unit_price_eur"]), step=0.01, key="set_fl_wpc",
        )
        flp["wpc_floor"]["area_per_piece"] = st.number_input(
            "WPC地板单支面积（m²）", min_value=0.01,
            value=float(flp["wpc_floor"]["area_per_piece"]), step=0.001, key="set_fl_area",
        )
        flp["keel"]["unit_price_eur"] = st.number_input(
            "龙骨单价（€/支）", min_value=0.0,
            value=float(flp["keel"]["unit_price_eur"]), step=0.01, key="set_fl_keel",
        )
        flp["keel"]["length_multiplier"] = st.number_input(
            "龙骨长度系数（×面积）", min_value=0.1,
            value=float(flp["keel"]["length_multiplier"]), step=0.1, key="set_fl_keel_m",
        )
    with col_fl2:
        flp["nail"]["unit_price_eur"] = st.number_input(
            "美固钉单价（€/个）", min_value=0.0,
            value=float(flp["nail"]["unit_price_eur"]), step=0.01, key="set_fl_nail",
        )
        flp["nail"]["count_per_sqm"] = st.number_input(
            "美固钉每平米数量", min_value=1,
            value=int(flp["nail"]["count_per_sqm"]), step=1, key="set_fl_nail_c",
        )
        flp["clip"]["unit_price_eur"] = st.number_input(
            "卡扣单价（€/个）", min_value=0.0,
            value=float(flp["clip"]["unit_price_eur"]), step=0.01, key="set_fl_clip",
        )
        flp["clip"]["count_per_sqm"] = st.number_input(
            "卡扣每平米数量", min_value=1,
            value=int(flp["clip"]["count_per_sqm"]), step=1, key="set_fl_clip_c",
        )
    with col_fl3:
        flp["self_tapping_screw"]["unit_price_eur"] = st.number_input(
            "自攻丝单价（€/个）", min_value=0.0,
            value=float(flp["self_tapping_screw"]["unit_price_eur"]), step=0.01, key="set_fl_screw",
        )
        flp["self_tapping_screw"]["count_per_sqm"] = st.number_input(
            "自攻丝每平米数量", min_value=1,
            value=int(flp["self_tapping_screw"]["count_per_sqm"]), step=1, key="set_fl_screw_c",
        )
        flp["starter_clip"]["unit_price_eur"] = st.number_input(
            "起始扣单价（€/个）", min_value=0.0,
            value=float(flp["starter_clip"]["unit_price_eur"]), step=0.01, key="set_fl_start",
        )
        flp["edge_band"]["unit_price_eur"] = st.number_input(
            "封边单价（€/支）", min_value=0.0,
            value=float(flp["edge_band"]["unit_price_eur"]), step=0.01, key="set_fl_edge",
        )


    st.divider()
    st.subheader("📦 包装参数")
    pkg_tab1, pkg_tab2, pkg_tab3 = st.tabs(["长城板", "围栏板", "地板"])
    pkg_type_map = {"长城板": "wall_panel", "围栏板": "fence", "地板": "floor"}
    for tab_name, tab in zip(["长城板", "围栏板", "地板"], [pkg_tab1, pkg_tab2, pkg_tab3]):
        with tab:
            pc = modified["package"][pkg_type_map[tab_name]]
            c1, c2, c3 = st.columns(3)
            with c1:
                pc["default_length_per_piece"] = st.number_input(
                    "默认单支长度（m）", min_value=0.1,
                    value=float(pc["default_length_per_piece"]), step=0.1,
                    key=f"set_pkg_len_{tab_name}",
                )
                pc["default_weight_per_meter"] = st.number_input(
                    "默认米重（KG/m）", min_value=0.01,
                    value=float(pc["default_weight_per_meter"]), step=0.01,
                    key=f"set_pkg_wt_{tab_name}",
                )
                pc["width_m"] = st.number_input(
                    "包装宽度（m）", min_value=0.01,
                    value=float(pc["width_m"]), step=0.01,
                    key=f"set_pkg_w_{tab_name}",
                )
            with c2:
                pc["length_extra_m"] = st.number_input(
                    "长度余量（m）", min_value=0.0,
                    value=float(pc["length_extra_m"]), step=0.01,
                    key=f"set_pkg_le_{tab_name}",
                )
                pc["height_base_m"] = st.number_input(
                    "高度基数（m）", min_value=0.0,
                    value=float(pc["height_base_m"]), step=0.01,
                    key=f"set_pkg_hb_{tab_name}",
                )
                pc["height_divisor"] = st.number_input(
                    "高度除数", min_value=1,
                    value=int(pc["height_divisor"]), step=1,
                    key=f"set_pkg_hd_{tab_name}",
                )
            with c3:
                pc["height_coeff"] = st.number_input(
                    "高度系数", min_value=0.001,
                    value=float(pc["height_coeff"]), step=0.001,
                    key=f"set_pkg_hc_{tab_name}",
                )
                pc["pallet_capacity"] = st.number_input(
                    "每托盘容量（支）", min_value=1,
                    value=int(pc["pallet_capacity"]), step=1,
                    key=f"set_pkg_pc_{tab_name}",
                )
                pc["packing_weight_kg"] = st.number_input(
                    "每托盘包装重（KG）", min_value=0,
                    value=int(pc["packing_weight_kg"]), step=1,
                    key=f"set_pkg_pw_{tab_name}",
                )
            if tab_name == "围栏板":
                pc["over_height_pieces"] = st.number_input(
                    "180支以上高度计算用支数（Excel固定为182）",
                    min_value=1, value=int(pc.get("over_height_pieces", 182)),
                    step=1, key="set_pkg_oh_fence",
                )


    st.divider()
    st.subheader("🔧 配件重量参数（KG/件）")
    aw = modified["accessory_weight"]
    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1:
        aw["post_weight_per_piece"] = st.number_input(
            "立柱单重", min_value=0.0,
            value=float(aw["post_weight_per_piece"]), step=0.01, key="set_aw_post",
        )
        aw["side_strip_weight"] = st.number_input(
            "侧条单重", min_value=0.0,
            value=float(aw["side_strip_weight"]), step=0.01, key="set_aw_side",
        )
    with col_a2:
        aw["groove_strip_weight"] = st.number_input(
            "凹条单重", min_value=0.0,
            value=float(aw["groove_strip_weight"]), step=0.01, key="set_aw_groove",
        )
        aw["tongue_strip_weight"] = st.number_input(
            "凸条单重", min_value=0.0,
            value=float(aw["tongue_strip_weight"]), step=0.01, key="set_aw_tongue",
        )
    with col_a3:
        aw["post_base_weight"] = st.number_input(
            "柱座单重", min_value=0.0,
            value=float(aw["post_base_weight"]), step=0.01, key="set_aw_base",
        )
        aw["post_cap_weight"] = st.number_input(
            "柱帽单重", min_value=0.0,
            value=float(aw["post_cap_weight"]), step=0.01, key="set_aw_cap",
        )


    st.divider()
    col_save, col_reset = st.columns(2)
    with col_save:
        if st.button("💾 保存设置", type="primary", use_container_width=True, key="save_cfg"):
            resp, status = save_changed_config_supabase(original_config, modified)
            if status == "no_change":
                st.info("ℹ️ 没有检测到配置变更，无需保存")
            else:
                st.success("✅ 变更字段已增量保存到Supabase云端")
            # 重点：保存完成后，**重新从数据库拉取最新配置**，覆盖session_state，保证UI完全和DB一致
            st.session_state["config"] = load_config_supabase()
            st.rerun()
    with col_reset:
        if st.button("🔄 恢复出厂默认", use_container_width=True, key="reset_cfg"):
            reset_config_supabase()
            # 重读数据库
            st.session_state["config"] = load_config_supabase()
            # 版本号+1 → 所有设置页面key后缀变化，全部控件销毁重建
            st.session_state["settings_revision"] += 1
            st.success("✅ 已恢复出厂默认并写入云端")
            st.rerun()
    # 返回从DB重新加载后的配置（rerun实际不会走到这行）
    return st.session_state["config"]



# ============================================================
# 主入口
# ============================================================
def main():
    st.set_page_config(
        page_title="WPC 板材计算器",
        page_icon="📐",
        layout="wide",
    )


    if "config" not in st.session_state:
        with st.spinner("加载云端配置..."):
            st.session_state["config"] = load_config_supabase()


    # 新增：设置页面表单版本号，用于重置全部输入框
    if "settings_revision" not in st.session_state:
        st.session_state["settings_revision"] = 0


    config = st.session_state["config"]


    st.title("📐 WPC 板材计算器")
    st.caption("二代共挤四代长城板 / 围栏板 / 地板 —— 价格 & 包装计算")


    with st.sidebar:
        st.header("导航")
        page = st.selectbox(
            "选择页面",
            options=["价格计算", "包装计算", "设置"],
            label_visibility="collapsed",
            key="nav_page",
        )
        st.divider()
        st.caption(
            f"当前汇率：\n"
            f"1€ = {config['exchange_rate']['cny_to_eur']} 元\n"
            f"1$ = {config['exchange_rate']['cny_to_usd']} 元"
        )
        st.caption("☁️ 配置存储：Supabase云端 key‑value行存储（增量更新变更字段）")


    if page == "价格计算":
        page_price_calc(config)
    elif page == "包装计算":
        page_package_calc(config)
    elif page == "设置":
        st.session_state["config"] = page_settings(config)



if __name__ == "__main__":
    main()