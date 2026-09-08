# -*- coding: utf-8 -*-
"""WPC 板材计算器 — Streamlit 主入口，侧边栏下拉导航，页面独立文件"""
import streamlit as st
from importlib.util import module_from_spec, spec_from_file_location
from common import load_config_supabase

st.set_page_config(
    page_title="WPC 板材报价系统",
    page_icon="📐",
    layout="wide"
)

# 初始化全局配置
if "config" not in st.session_state:
    with st.spinner("加载云端配置..."):
        st.session_state["config"] = load_config_supabase()

# 页面映射：显示名称 -> 文件路径
page_mapping = {
    "🏠 首页": "pages_func/home.py",
    "🧮 价格计算": "pages_func/price_calc_page.py",
    "📦 包装计算": "pages_func/package_calc_page.py",
    "⚙️ 计算设置": "pages_func/settings_page.py",
    "🗃️ 产品信息管理": "pages_func/product_settings.py",
    "📄 产品详情": "pages_func/product_detail.py",
    "⭐ 产品优势": "pages_func/product_advantages.py",
}

with st.sidebar:
    st.header("导航")
    selected_name = st.selectbox(
        "选择页面",
        options=list(page_mapping.keys()),
        label_visibility="collapsed",
        key="main_nav_select"
    )
    st.divider()
    cfg = st.session_state["config"]
    st.caption(
        f"当前汇率：\n"
        f"1€ = {cfg['exchange_rate']['cny_to_eur']} 元\n"
        f"1$ = {cfg['exchange_rate']['cny_to_usd']} 元"
    )
    st.caption("☁️ 配置存储：Supabase云端")

# 动态加载执行选中页面，增加文件异常捕获
page_file = page_mapping[selected_name]
try:
    spec = spec_from_file_location("target_page", page_file)
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
except FileNotFoundError:
    st.error(f"页面文件不存在：`{page_file}`，请检查pages_func目录")
except Exception as err:
    st.error(f"页面加载异常：{err}")
