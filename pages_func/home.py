# -*- coding: utf-8 -*-
"""首页页面"""
import streamlit as st

def page_home():
    # ========== 新增顶部跳转按钮 ==========
    col_top1, col_top2, _ = st.columns([1, 1, 8])
    with col_top1:
        st.link_button("🚚 运费计算器", url="https://freightcalc-todufytkjq3zjv5c5tr2iz.streamlit.app/", use_container_width=True)
    with col_top2:
        st.link_button("💻 下载桌面版", url="https://github.com/Ayj2004/board_calculator/releases/download/wpc-calculator-desktop/WPC_calculator.exe", use_container_width=True)
    st.divider()
    # ======================================

    st.header("📐 WPC 板材计算器")
    st.subheader("版本：V6")
    st.divider()
    st.markdown("### 📋 V6 本次更新内容")
    update_log = """
**新增功能**
 - 修复价格计算，不再按照底层多位小数计算总价，统一按照保留两位小数单价计算总价。
 - 价格计算界面新增报价模板，可以复制翻译后直接发给客户。
 - 包装计算界面新增询价模板，填写客户地址后可以直接发送货代群询价。
"""
    st.markdown(update_log)
    st.divider()
    st.markdown("### 🧭 模块导航")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("""💰 **价格计算**
全系列墙板 / 围栏板 / 地板价格核算
- 支持 CNY / EUR / USD 多币种切换
- 支持容错支数、MOQ最小起订量
- 自动计算板材、配件数量与总价格
""")
    with col2:
        st.info("""📦 **包装计算**
托盘、体积、重量核算，用于物流柜量测算
- 单托装箱数量、托盘重量、体积计算
- 柜装数量、总毛重、总体积输出
- 适配全系列墙板、围栏板、地板不同包装参数
""")
    with col3:
        st.info("""⚙️ **设置**
云端参数配置，单字段保存/撤销/重置
- 汇率、板材单价、配件重量、包装参数全部云端存储
- 修改后按需保存，支持单字段恢复出厂默认
- 数据持久化到Supabase，多会话共享配置
""")
    col4, col5, col6 = st.columns(3)
    with col4:
        st.info("""🏷️ **产品管理**
维护板材与配件基础产品库
- 全系列墙板、围栏板、地板基础产品录入
- 围栏/地板配件维护，填写单价、重量、规格
- 支持上传产品图片，存储到Supabase Storage
""")
    with col5:
        st.info("""🔍 **产品详情查看**
浏览已录入产品完整参数
- 选择产品查看全部规格参数
- 展示产品图片、尺寸、米重、价格、起订量
- 表格化展示，方便核对产品基础数据
""")
    with col6:
        st.info("""✨ **产品优势**
对外展示产品卖点、参数、应用场景
- 整理WPC板材对外宣传文案
- 可用于给客户截图参考
""")
    st.divider()
    cfg = st.session_state["config"]
    st.caption(f"💡 当前汇率：1€ = {cfg['exchange_rate']['cny_to_eur']}元，1$ = {cfg['exchange_rate']['cny_to_usd']}元｜配置存储：Supabase云端")

page_home()
