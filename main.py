# coding: utf-8 --
""" WPC 板材计算器 —— Streamlit + Supabase版本
app_config改为key‑value行式存储，不再单条jsonb大字段
版本：V2 + MOQ最小起订量适配
"""
import copy
import math
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
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_ANON_KEY"]
        return create_client(url, key)
    except KeyError:
        st.error("⚠️缺少Supabase Secrets：SUPABASE_URL / SUPABASE_ANON_KEY")
        return None


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


def _get_nested_value(d: dict, flat_key: str):
    """扁平key如 wall_panel_price.length_calc_extra_pieces 读取嵌套字典的值"""
    parts = flat_key.split(".")
    node = d
    for p in parts:
        node = node[p]
    return node


def load_config_supabase() -> dict:
    """从supabase加载配置；无数据返回DEFAULT_CONFIG，首次自动初始化全部行"""
    try:
        supabase = get_supabase_client()
        if supabase is None:
            return copy.deepcopy(DEFAULT_CONFIG)
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
    """【全量保存】把嵌套dict展开为全部kv行，批量upsert到app_config（用于初始化）"""
    supabase = get_supabase_client()
    if supabase is None:
        return None
    kv_list = dict_to_kv_rows(cfg)
    resp = supabase.table("app_config").upsert(kv_list).execute()
    return resp


def save_single_kv(key_flat: str, value):
    """保存单个扁平key‑value到supabase"""
    supabase = get_supabase_client()
    if supabase is None:
        return False
    supabase.table("app_config").upsert([{"key": key_flat, "value": value}]).execute()
    return True


def _deep_merge(base: dict, override: dict) -> dict:
    """深度合并字典，override键覆盖base；base会被原地修改，请传入deepcopy副本"""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


# 封装：带行内按钮的数字输入组件
# flat_key: "exchange_rate.cny_to_eur" 扁平key
# db_value: 当前数据库真实值
# default_value: DEFAULT_CONFIG出厂默认值
# label: 输入框标签
# min_value, step等数字输入参数
def editable_number_input(flat_key: str, db_value, default_value, label: str,
                          min_value=None, max_value=None, step=0.01):
    edit_key = f"edit_tmp_{flat_key}"
    changed_flag_key = f"is_changed_{flat_key}"
    # 初始化临时编辑缓存
    if edit_key not in st.session_state:
        st.session_state[edit_key] = db_value
    if changed_flag_key not in st.session_state:
        st.session_state[changed_flag_key] = False
    tmp_val = st.session_state[edit_key]
    # 判断状态
    is_modified = (tmp_val != db_value)
    is_not_default = (db_value != default_value)
    # -------- 修复：统一 number_input 数值类型，避免 int/float 混用报错 --------
    if isinstance(tmp_val, float):
        if min_value is not None:
            min_value = float(min_value)
        if max_value is not None:
            max_value = float(max_value)
        step = float(step)
    else:
        if min_value is not None:
            min_value = int(min_value)
        if max_value is not None:
            max_value = int(max_value)
        step = int(step)
    # 列比例，不使用 vertical_alignment（低版本 streamlit 没有这个参数，避免额外报错）
    col_input, col_btns = st.columns([7, 3])
    with col_input:
        new_val = st.number_input(
            label=label,
            value=tmp_val,
            min_value=min_value,
            max_value=max_value,
            step=step,
            key=f"num_{flat_key}",
            on_change=lambda: (
                setattr(st.session_state, edit_key, st.session_state[f"num_{flat_key}"]),
                setattr(st.session_state, changed_flag_key, True)
            )
        )
    with col_btns:
        btn_list = []
        if is_modified:
            btn_list.append(("✔", f"save_{flat_key}", "保存此字段到云端"))
            btn_list.append(("✖", f"cancel_{flat_key}", "撤销本次修改，恢复数据库当前值"))
        if is_not_default:
            btn_list.append(("↺", f"resetdef_{flat_key}", "重置为此字段出厂默认值并保存云端"))
        # 兼容：没有按钮就直接返回，禁止 columns (0)
        btn_count = len(btn_list)
        if btn_count > 0:
            # 使用等宽比例列表，替代数字 + gap，兼容旧版 streamlit
            ratios = [1.0] * btn_count
            cols_btn = st.columns(ratios)
            for idx, (btn_text, btn_key, help_text) in enumerate(btn_list):
                with cols_btn[idx]:
                    if st.button(btn_text, key=btn_key, help=help_text, use_container_width=True):
                        if btn_text == "✔":
                            ok = save_single_kv(flat_key, st.session_state[edit_key])
                            if ok:
                                st.success("已保存")
                                st.session_state["config"] = load_config_supabase()
                                st.session_state[edit_key] = _get_nested_value(st.session_state["config"], flat_key)
                                st.session_state[changed_flag_key] = False
                                st.rerun()
                        elif btn_text == "✖":
                            st.session_state[edit_key] = db_value
                            st.session_state[changed_flag_key] = False
                            st.rerun()
                        elif btn_text == "↺":
                            ok = save_single_kv(flat_key, default_value)
                            if ok:
                                st.success("已重置为默认值并保存")
                                st.session_state["config"] = load_config_supabase()
                                st.session_state[edit_key] = default_value
                                st.session_state[changed_flag_key] = False
                                st.rerun()
    # 不返回局部config，外部统一读取 st.session_state["config"]
    return st.session_state["config"]


# 【新增】首页页面
def page_home():
    st.header("📐 WPC 板材计算器")
    st.subheader("版本：V2")
    st.divider()
    st.markdown("### 📋 V2 本次更新内容")
    update_log = """
新增功能
 - 增加首页。
 - 二代共挤四代长城板按长度计算：可正常使用(其中长度为所覆盖的墙面长度，单支米数可以理解为单支可以覆盖墙面的高度)。
 - 每个计算模块增加容错支数输入框，默认5；仅主板材加容错，配件不加容错
 - 围栏板输出1.5米、1.8米两套围栏板单独分项总价
 - ✨新增最小起订MOQ校验：计算数量小于MOQ自动取最小起订量并弹窗提示
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
    st.caption("💡 提示：请使用左侧侧边栏切换功能页面；配置自动保存在Supabase云端。")


# 页面：价格计算
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
                # 二代长城板主板叠加容错
                result["pieces_needed"] += tolerance_pieces_wall
                # ========= MOQ最小起订校验 =========
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
                # 叠加用户自定义容错支数
                result["pieces_needed"] += tolerance_pieces_wall_len
                # ========= MOQ最小起订校验 =========
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
            # 围栏板仅两块主板加容错，配件全部不加
            for it in result["items"]:
                if it["name"] in ("1.5米高围栏板（9层）", "1.8米高围栏板（11层）"):
                    it["quantity"] += tolerance_pieces_fence

            # ========= MOQ校验：仅2个围栏主板项目做最小起订量判断 =========
            for it in result["items"]:
                if it["name"] in ("1.5米高围栏板（9层）", "1.8米高围栏板（11层）"):
                    ori_qty = it["quantity"]
                    if ori_qty < moq_fence:
                        st.warning(f"⚠️[{it['name']}] 计算数量 {ori_qty:.0f}，小于最小起订{moq_fence}，已自动使用MOQ")
                        it["quantity"] = moq_fence
                    it["total_eur"] = it["quantity"] * it["unit_price_eur"]

            # 重新汇总总eur
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
            # 仅WPC地板主板加容错，其他配件不加
            for it in result["items"]:
                if it["name"] == "WPC地板":
                    it["quantity"] += tolerance_pieces_floor
                    # ========= MOQ最小起订校验 =========
                    ori_qty = it["quantity"]
                    if ori_qty < moq_floor:
                        st.warning(f"⚠️WPC地板计算得到 {ori_qty:.0f}支，小于最小起订{moq_floor}支，已自动使用MOQ最小起订量")
                        it["quantity"] = moq_floor
                    it["total_eur"] = it["quantity"] * it["unit_price_eur"]
            # 重新汇总总eur
            total_eur_new = 0.0
            for it in result["items"]:
                total_eur_new += it["total_eur"]
            result["total_eur"] = total_eur_new
            _display_floor_result(result, currency, cny_to_eur, cny_to_usd, sym)


def _display_wall_panel_result(result: dict, currency: str, sym: str):
    """
    二代长城板渲染：直接读取result内部已经算好的各币种价格，不再二次汇率转换
    修复：顶部metric和表格价格不一致
    """
    st.subheader("📊 计算结果")
    col1, col2, col3 = st.columns(3)
    col1.metric("人民币单支价", f"¥ {result['unit_price_cny']:.2f}")
    col2.metric("欧元单支价", f"€ {result['unit_price_eur']:.2f}")
    col3.metric("美元单支价", f"$ {result['unit_price_usd']:.2f}")
    # 直接取已经计算完成的对应币种，禁止二次convert_currency
    if currency == "CNY":
        unit_price_target = result["unit_price_cny"]
        total_target = result["pieces_needed"] * unit_price_target
    elif currency == "EUR":
        unit_price_target = result["unit_price_eur"]
        total_target = result["pieces_needed"] * unit_price_target
    else:  # USD
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
    # 用于统计配件重量：保存原始未四舍五入的计算数量
    qty_map = {}
    # 需要统计重量的key白名单，不在名单的配件不存入qty_map
    weight_key_list = {"post", "side_strip", "groove_strip", "tongue_strip", "post_base", "post_cap"}
    price_9layer_board_eur = 0.0
    price_11layer_board_eur = 0.0
    accessories_total_eur = 0.0
    for item in result["items"]:
        unit_price = convert_currency(item["unit_price_eur"], currency, cny_to_eur, cny_to_usd)
        total = convert_currency(item["total_eur"], currency, cny_to_eur, cny_to_usd)
        raw_qty = item["quantity"]
        disp_qty = round(raw_qty)  # ✅仅前端表格展示
        # 区分板材和配件
        if item["name"] == "1.5米高围栏板（9层）":
            price_9layer_board_eur = item["total_eur"]
        elif item["name"] == "1.8米高围栏板（11层）":
            price_11layer_board_eur = item["total_eur"]
        else:
            # 其余全部视为配件，累加配件总金额
            accessories_total_eur += item["total_eur"]
        # 安全取key，只有key存在并且在重量白名单才存入qty_map
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
    # ✅业务规则：分项总价 = 板材本身 + 全部配件总价
    total_9_all_eur = price_9layer_board_eur + accessories_total_eur
    total_11_all_eur = price_11layer_board_eur + accessories_total_eur
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        p9 = convert_currency(total_9_all_eur, currency, cny_to_eur, cny_to_usd)
        st.metric("1.5米围栏板（9层）分项总价", f"{sym} {p9:.2f}")
    with col_p2:
        p11 = convert_currency(total_11_all_eur, currency, cny_to_eur, cny_to_usd)
        st.metric("1.8米围栏板（11层）分项总价", f"{sym} {p11:.2f}")
    # ========== 删除原：全部（围栏板+配件）总价标题，不再输出 ==========
    # ========== 围栏配件总重量，复刻Excel CEILING公式 ==========
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
    # Excel CEILING(xxx,1) → math.ceil向上取整整数
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


# 页面：包装计算
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


# 页面：设置 —— 改造为行内✔✖↺单字段保存，移除底部全局保存/恢复出厂
def page_settings(config: dict) -> dict:
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
    return config


# 主入口
def main():
    st.set_page_config(
        page_title="WPC 板材计算器",
        page_icon="📐",
        layout="wide",
    )
    if "config" not in st.session_state:
        with st.spinner("加载云端配置..."):
            st.session_state["config"] = load_config_supabase()
    # 临时编辑缓存不需要全局revision，每个字段独立维护临时状态
    config = st.session_state["config"]
    st.title("📐 WPC 板材计算器")
    st.caption("二代共挤四代长城板 / 围栏板 / 地板 —— 价格 & 包装计算；支持 CNY / EUR / USD 币种切换")
    with st.sidebar:
        st.header("导航")
        # 【改动】增加首页，放在列表第一个，打开默认选中首页
        page_options = ["首页", "价格计算", "包装计算", "设置"]
        page = st.selectbox(
            "选择页面",
            options=page_options,
            label_visibility="collapsed",
            key="nav_page",
        )
        st.divider()
        st.caption(
            f"当前汇率：\n"
            f"1€ = {config['exchange_rate']['cny_to_eur']} 元\n"
            f"1$ = {config['exchange_rate']['cny_to_usd']} 元"
        )
        st.caption("☁️ 配置存储：Supabase云端")
    # 路由分发
    if page == "首页":
        page_home()
    elif page == "价格计算":
        page_price_calc(config)
    elif page == "包装计算":
        page_package_calc(config)
    elif page == "设置":
        st.session_state["config"] = page_settings(config)


if __name__ == "__main__":
    main()
