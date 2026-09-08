# -*- coding: utf-8 -*-
"""设置页面"""
import streamlit as st
from common import editable_number_input
from config_default import DEFAULT_CONFIG


def page_settings():
    config = st.session_state["config"]
    st.header("⚙️ 设置")
    st.info("💡 修改输入框后右侧出现 ✔保存 / ✖撤销；↺按钮仅在非出厂默认值时出现，点击直接重置并保存云端")
    st.subheader("💱 汇率设置")
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        config = editable_number_input(
            flat_key="exchange_rate.cny_to_eur",
            db_value=config["exchange_rate"]["cny_to_eur"],
            default_value=DEFAULT_CONFIG["exchange_rate"]["cny_to_eur"],
            label="人民币兑欧元（CNY/EUR）",
            min_value=0.01, step=0.01
        )
    with col_r2:
        config = editable_number_input(
            flat_key="exchange_rate.cny_to_usd",
            db_value=config["exchange_rate"]["cny_to_usd"],
            default_value=DEFAULT_CONFIG["exchange_rate"]["cny_to_usd"],
            label="人民币兑美元（CNY/USD）",
            min_value=0.01, step=0.01
        )
    st.divider()
    st.subheader("🏗️ 二代共挤四代长城板 —— 价格参数")
    wp = config["wall_panel_price"]
    wp_def = DEFAULT_CONFIG["wall_panel_price"]
    col_w1, col_w2, col_w3 = st.columns(3)
    with col_w1:
        config = editable_number_input("wall_panel_price.price_per_meter_cny", wp["price_per_meter_cny"], wp_def["price_per_meter_cny"],
                                       "含税单价（元/米）", min_value=0.0, step=0.01)
        config = editable_number_input("wall_panel_price.default_length_per_piece", wp["default_length_per_piece"], wp_def["default_length_per_piece"],
                                       "默认单支米数", min_value=0.1, step=0.1)
    with col_w2:
        config = editable_number_input("wall_panel_price.panel_width_m", wp["panel_width_m"], wp_def["panel_width_m"],
                                       "板材宽度（米）", min_value=0.01, step=0.01)
        config = editable_number_input("wall_panel_price.eur_extra_fee", wp["eur_extra_fee"], wp_def["eur_extra_fee"],
                                       "欧元额外加价（€/支）", min_value=0.0, step=0.01)
    with col_w3:
        config = editable_number_input("wall_panel_price.cny_extra_per_meter", wp["cny_extra_per_meter"], wp_def["cny_extra_per_meter"],
                                       "人民币每米加价（元）", min_value=0.0, step=0.1)
        config = editable_number_input("wall_panel_price.length_calc_extra_pieces", wp["length_calc_extra_pieces"], wp_def["length_calc_extra_pieces"],
                                       "按长度计算余量（支）", min_value=0, step=1)
        config = editable_number_input("wall_panel_price.moq_pieces", wp["moq_pieces"], wp_def["moq_pieces"],
                                       "最小起订支数MOQ", min_value=1, step=1)
    st.divider()
    st.subheader("🚧 围栏板 —— 配件单价（欧元）【源存储为欧元，前端自动换算CNY/USD】")
    fp = config["fence_price"]
    fp_def = DEFAULT_CONFIG["fence_price"]
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
            fk = f"fence_price.{key}.unit_price_eur"
            config = editable_number_input(
                fk, fp[key]["unit_price_eur"], fp_def[key]["unit_price_eur"],
                f"{label}（€）", min_value=0.0, step=0.01
            )
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        config = editable_number_input("fence_price.section_length_m", fp["section_length_m"], fp_def["section_length_m"],
                                       "每段长度（米）", min_value=0.1, step=0.1)
    with col_f2:
        config = editable_number_input("fence_price.boards_per_section_9", fp["boards_per_section_9"], fp_def["boards_per_section_9"],
                                       "每段板数(9片方案)", min_value=1, step=1)
    with col_f3:
        config = editable_number_input("fence_price.boards_per_section_11", fp["boards_per_section_11"], fp_def["boards_per_section_11"],
                                       "每段板数(11片方案)", min_value=1, step=1)
    config = editable_number_input("fence_price.bolts_per_post", fp["bolts_per_post"], fp_def["bolts_per_post"],
                                   "每根立柱膨胀丝数", min_value=1, step=1)
    config = editable_number_input("fence_price.moq_pieces", fp["moq_pieces"], fp_def["moq_pieces"],
                                   "围栏主板最小起订MOQ", min_value=1, step=1)
    st.divider()
    st.subheader("🪵 地板 —— 配件单价（欧元）【源存储为欧元，前端自动换算CNY/USD】")
    flp = config["floor_price"]
    flp_def = DEFAULT_CONFIG["floor_price"]
    col_fl1, col_fl2, col_fl3 = st.columns(3)
    with col_fl1:
        config = editable_number_input("floor_price.wpc_floor.unit_price_eur", flp["wpc_floor"]["unit_price_eur"], flp_def["wpc_floor"]["unit_price_eur"],
                                       "WPC地板单价（€/支）", min_value=0.0, step=0.01)
        config = editable_number_input("floor_price.wpc_floor.area_per_piece", flp["wpc_floor"]["area_per_piece"], flp_def["wpc_floor"]["area_per_piece"],
                                       "WPC地板单支面积（m²）", min_value=0.01, step=0.001)
        config = editable_number_input("floor_price.keel.unit_price_eur", flp["keel"]["unit_price_eur"], flp_def["keel"]["unit_price_eur"],
                                       "龙骨单价（€/支）", min_value=0.0, step=0.01)
        config = editable_number_input("floor_price.keel.length_multiplier", flp["keel"]["length_multiplier"], flp_def["keel"]["length_multiplier"],
                                       "龙骨长度系数（×面积）", min_value=0.1, step=0.1)
    with col_fl2:
        config = editable_number_input("floor_price.nail.unit_price_eur", flp["nail"]["unit_price_eur"], flp_def["nail"]["unit_price_eur"],
                                       "美固钉单价（€/个）", min_value=0.0, step=0.01)
        config = editable_number_input("floor_price.nail.count_per_sqm", flp["nail"]["count_per_sqm"], flp_def["nail"]["count_per_sqm"],
                                       "美固钉每平米数量", min_value=1, step=1)
        config = editable_number_input("floor_price.clip.unit_price_eur", flp["clip"]["unit_price_eur"], flp_def["clip"]["unit_price_eur"],
                                       "卡扣单价（€/个）", min_value=0.0, step=0.01)
        config = editable_number_input("floor_price.clip.count_per_sqm", flp["clip"]["count_per_sqm"], flp_def["clip"]["count_per_sqm"],
                                       "卡扣每平米数量", min_value=1, step=1)
    with col_fl3:
        config = editable_number_input("floor_price.self_tapping_screw.unit_price_eur", flp["self_tapping_screw"]["unit_price_eur"], flp_def["self_tapping_screw"]["unit_price_eur"],
                                       "自攻丝单价（€/个）", min_value=0.0, step=0.01)
        config = editable_number_input("floor_price.self_tapping_screw.count_per_sqm", flp["self_tapping_screw"]["count_per_sqm"], flp_def["self_tapping_screw"]["count_per_sqm"],
                                       "自攻丝每平米数量", min_value=1, step=1)
        config = editable_number_input("floor_price.starter_clip.unit_price_eur", flp["starter_clip"]["unit_price_eur"], flp_def["starter_clip"]["unit_price_eur"],
                                       "起始扣单价（€/个）", min_value=0.0, step=0.01)
        config = editable_number_input("floor_price.edge_band.unit_price_eur", flp["edge_band"]["unit_price_eur"], flp_def["edge_band"]["unit_price_eur"],
                                       "封边单价（€/支）", min_value=0.0, step=0.01)
        config = editable_number_input("floor_price.moq_pieces", flp["moq_pieces"], flp_def["moq_pieces"],
                                       "WPC地板最小起订MOQ", min_value=1, step=1)
    st.divider()
    st.subheader("📦 包装参数")
    pkg_tab1, pkg_tab2, pkg_tab3 = st.tabs(["长城板", "围栏板", "地板"])
    pkg_type_map = {"长城板": "wall_panel", "围栏板": "fence", "地板": "floor"}
    for tab_name, tab in zip(["长城板", "围栏板", "地板"], [pkg_tab1, pkg_tab2, pkg_tab3]):
        with tab:
            pc = config["package"][pkg_type_map[tab_name]]
            pc_def = DEFAULT_CONFIG["package"][pkg_type_map[tab_name]]
            c1, c2, c3 = st.columns(3)
            with c1:
                config = editable_number_input(f"package.{pkg_type_map[tab_name]}.default_length_per_piece",
                                               pc["default_length_per_piece"], pc_def["default_length_per_piece"],
                                               "默认单支长度（m）", min_value=0.1, step=0.1)
                config = editable_number_input(f"package.{pkg_type_map[tab_name]}.default_weight_per_meter",
                                               pc["default_weight_per_meter"], pc_def["default_weight_per_meter"],
                                               "默认米重（KG/m）", min_value=0.01, step=0.01)
                config = editable_number_input(f"package.{pkg_type_map[tab_name]}.width_m",
                                               pc["width_m"], pc_def["width_m"],
                                               "包装宽度（m）", min_value=0.01, step=0.01)
            with c2:
                config = editable_number_input(f"package.{pkg_type_map[tab_name]}.length_extra_m",
                                               pc["length_extra_m"], pc_def["length_extra_m"],
                                               "长度余量（m）", min_value=0.0, step=0.01)
                config = editable_number_input(f"package.{pkg_type_map[tab_name]}.height_base_m",
                                               pc["height_base_m"], pc_def["height_base_m"],
                                               "高度基数（m）", min_value=0.0, step=0.01)
                config = editable_number_input(f"package.{pkg_type_map[tab_name]}.height_divisor",
                                               pc["height_divisor"], pc_def["height_divisor"],
                                               "高度除数", min_value=1, step=1)
            with c3:
                config = editable_number_input(f"package.{pkg_type_map[tab_name]}.height_coeff",
                                               pc["height_coeff"], pc_def["height_coeff"],
                                               "高度系数", min_value=0.001, step=0.001)
                config = editable_number_input(f"package.{pkg_type_map[tab_name]}.pallet_capacity",
                                               pc["pallet_capacity"], pc_def["pallet_capacity"],
                                               "每托盘容量（支）", min_value=1, step=1)
                config = editable_number_input(f"package.{pkg_type_map[tab_name]}.packing_weight_kg",
                                               pc["packing_weight_kg"], pc_def["packing_weight_kg"],
                                               "每托盘包装重（KG）", min_value=0, step=1)
            if tab_name == "围栏板":
                config = editable_number_input(f"package.{pkg_type_map[tab_name]}.over_height_pieces",
                                               pc.get("over_height_pieces", 182), pc_def.get("over_height_pieces", 182),
                                               "180支以上高度计算用支数（Excel固定为182）", min_value=1, step=1)
    st.divider()
    st.subheader("🔧 配件重量参数（KG/件）")
    aw = config["accessory_weight"]
    aw_def = DEFAULT_CONFIG["accessory_weight"]
    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1:
        config = editable_number_input("accessory_weight.post_weight_per_piece", aw["post_weight_per_piece"], aw_def["post_weight_per_piece"],
                                       "立柱单重", min_value=0.0, step=0.01)
        config = editable_number_input("accessory_weight.side_strip_weight", aw["side_strip_weight"], aw_def["side_strip_weight"],
                                       "侧条单重", min_value=0.0, step=0.01)
    with col_a2:
        config = editable_number_input("accessory_weight.groove_strip_weight", aw["groove_strip_weight"], aw_def["groove_strip_weight"],
                                       "凹条单重", min_value=0.0, step=0.01)
        config = editable_number_input("accessory_weight.tongue_strip_weight", aw["tongue_strip_weight"], aw_def["tongue_strip_weight"],
                                       "凸条单重", min_value=0.0, step=0.01)
    with col_a3:
        config = editable_number_input("accessory_weight.post_base_weight", aw["post_base_weight"], aw_def["post_base_weight"],
                                       "柱座单重", min_value=0.0, step=0.01)
        config = editable_number_input("accessory_weight.post_cap_weight", aw["post_cap_weight"], aw_def["post_cap_weight"],
                                       "柱帽单重", min_value=0.0, step=0.01)
    st.session_state["config"] = config


page_settings()
