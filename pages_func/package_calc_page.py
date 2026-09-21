# -*- coding: utf-8 -*-
"""包装计算页面"""
import pandas as pd
import streamlit as st
from calculator.package_calc import calc_package
from config_default import WALL_PANEL_PRODUCTS

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

def page_package_calc():
    config = st.session_state["config"]
    st.header("📦 包装计算")

    wall_product_names = [p["name"] for p in WALL_PANEL_PRODUCTS]
    panel_type = st.selectbox(
        "选择板材类型",
        options=wall_product_names + ["围栏板", "地板"],
        key="pkg_panel_type",
    )

    # ========== 墙板产品包装计算 ==========
    if panel_type in wall_product_names:
        product = next(p for p in WALL_PANEL_PRODUCTS if p["name"] == panel_type)
        pkg_cfg = config["package"][product["package_key"]]

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

    # ========== 围栏板包装计算 ==========
    elif panel_type == "围栏板":
        pkg_cfg = config["package"]["fence"]
        col1, col2, col3 = st.columns(3)
        with col1:
            pieces = st.number_input(
                "数量（支）", min_value=1, value=100, step=1,
                key="pkg_pieces_fence",
            )
        with col2:
            length_per_piece = st.number_input(
                "单支长度（米）",
                min_value=0.1,
                value=float(pkg_cfg["default_length_per_piece"]),
                step=0.1,
                key="pkg_length_fence",
                help=f"该板材默认 {pkg_cfg['default_length_per_piece']} 米，可修改",
            )
        with col3:
            weight_per_meter = st.number_input(
                "米重（KG/米）",
                min_value=0.01,
                value=float(pkg_cfg["default_weight_per_meter"]),
                step=0.01,
                key="pkg_weight_fence",
                help=f"该板材默认 {pkg_cfg['default_weight_per_meter']} KG/米，可修改",
            )
        if st.button("计算包装", type="primary", key="pkg_calc_fence"):
            result = calc_package(pieces, length_per_piece, weight_per_meter, pkg_cfg)
            _display_package_result(result)

    # ========== 地板包装计算 ==========
    elif panel_type == "地板":
        pkg_cfg = config["package"]["floor"]
        col1, col2, col3 = st.columns(3)
        with col1:
            pieces = st.number_input(
                "数量（支）", min_value=1, value=100, step=1,
                key="pkg_pieces_floor",
            )
        with col2:
            length_per_piece = st.number_input(
                "单支长度（米）",
                min_value=0.1,
                value=float(pkg_cfg["default_length_per_piece"]),
                step=0.1,
                key="pkg_length_floor",
                help=f"该板材默认 {pkg_cfg['default_length_per_piece']} 米，可修改",
            )
        with col3:
            weight_per_meter = st.number_input(
                "米重（KG/米）",
                min_value=0.01,
                value=float(pkg_cfg["default_weight_per_meter"]),
                step=0.01,
                key="pkg_weight_floor",
                help=f"该板材默认 {pkg_cfg['default_weight_per_meter']} KG/米，可修改",
            )
        if st.button("计算包装", type="primary", key="pkg_calc_floor"):
            result = calc_package(pieces, length_per_piece, weight_per_meter, pkg_cfg)
            _display_package_result(result)

page_package_calc()
