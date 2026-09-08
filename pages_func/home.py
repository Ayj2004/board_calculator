# -*- coding: utf-8 -*-
"""首页页面"""
import streamlit as st

def page_home():
    st.header("📐 WPC 板材计算器")
    st.subheader("版本：V3")
    st.divider()
    st.markdown("### 📋 V3 本次更新内容")
    update_log = """
新增功能
 - 新增产品管理界面、产品详情界面、产品优势界面。
    """
    st.markdown(update_log)
    st.divider()
    st.markdown("### 🧭 模块导航")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("💰 价格计算\n\n二代长城板 / 围栏板 / 地板价格核算，支持EUR/USD/CNY切换，支持容错支数、MOQ最小起订")
    with col2:
        st.info("📦 包装计算\n\n托盘、体积、重量核算，用于物流柜量测算")
    with col3:
        st.info("⚙️ 设置\n\n云端参数配置，单字段保存/撤销/重置，配置持久化Supabase")
    st.divider()
    cfg = st.session_state["config"]
    st.caption(f"💡 当前汇率：1€ = {cfg['exchange_rate']['cny_to_eur']}元，1$ = {cfg['exchange_rate']['cny_to_usd']}元｜配置存储：Supabase云端")


page_home()
