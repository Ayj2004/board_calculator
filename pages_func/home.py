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
    st.subheader("版本：V5")
    st.divider()
    st.markdown("### 📋 V5 本次更新内容")
    update_log = """
**新增功能**
 - 发布独立 Windows 桌面客户端，打包为 exe，支持离线使用。
 - 首页顶部增加快捷入口：运费计算器跳转链接、桌面版下载按钮。
 - 墙板产品矩阵扩展：新增6款墙板产品（二代共挤半包四孔、五孔、圆弧四孔、标准共挤、半包小长城、共挤墙板），价格计算、包装计算、参数设置全模块原生适配，所有配置云端持久化同步。
 - 新增产品管理界面、产品详情界面、产品优势界面。
 - 适配MOQ最小起订量逻辑，计算自动向上取整到起订数量。
 - 围栏板、地板计算支持容错支数叠加，配件不叠加容错。
 - 设置页面改为单字段✔保存 / ✖撤销 / ↺重置，配置持久化存储Supabase。
 - 修复表格与顶部metric价格不一致、数字类型混合报错等问题。
 - UI价格统一保留2位小数，底层计算保留完整高精度，与Excel逻辑完全对齐。
**业务调整**
 - 墙板计算移除固定长度余量参数（length_calc_extra_pieces），统一由前端「容错支数」手动输入控制，适配不同业务场景。
 - 包装计算移除配件重量模块；配件重量仅围栏板价格页面保留。
 - 围栏板结果页移除独立立柱数量展示，仅保留汇总表格。
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
