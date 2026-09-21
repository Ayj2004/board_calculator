# -*- coding: utf-8 -*-
"""公共模块：supabase、配置读写、工具函数、editable_number_input组件"""
import copy
import streamlit as st
from supabase import create_client, Client
from postgrest.exceptions import APIError
from config_default import DEFAULT_CONFIG

@st.cache_resource(show_spinner="连接Supabase...")
def get_supabase_client() -> Client:
    """初始化supabase客户端，cache_resource只实例化一次"""
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except KeyError:
        st.error("⚠️缺少Supabase Secrets：SUPABASE_URL / SUPABASE_KEY")
        return None



def dict_to_kv_rows(d: dict, prefix: str = "") -> list[dict]:
    """嵌套字典转为扁平key‑value行 {"a":{"b":1}} → [{"key":"a.b","value":1}]"""
    rows = []
    for k, v in d.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            rows.extend(dict_to_kv_rows(v, full_key))
        else:
            rows.append({"key": full_key, "value": v})
    return rows


def kv_rows_to_dict(rows: list[dict]) -> dict:
    """数据库扁平key‑value列表还原为嵌套字典"""
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
    """扁平key读取嵌套字典的值"""
    parts = flat_key.split(".")
    node = d
    for p in parts:
        node = node[p]
    return node


def _deep_merge(base: dict, override: dict) -> dict:
    """深度合并字典，override键覆盖base；base会被原地修改，请传入deepcopy副本"""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def load_config_supabase() -> dict:
    """从supabase加载配置；无数据返回DEFAULT_CONFIG，首次自动初始化全部行"""
    try:
        supabase = get_supabase_client()
        if supabase is None:
            return copy.deepcopy(DEFAULT_CONFIG)
        resp = supabase.table("app_config").select("key,value").execute()
        rows = resp.data or []
        if len(rows) == 0:
            default_cfg = copy.deepcopy(DEFAULT_CONFIG)
            save_config_supabase(default_cfg)
            return default_cfg
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


def editable_number_input(flat_key: str, db_value, default_value, label: str,
                          min_value=None, max_value=None, step=0.01):
    """带行内✔保存、✖撤销、↺单字段重置 的数字输入组件"""
    edit_key = f"edit_tmp_{flat_key}"
    changed_flag_key = f"is_changed_{flat_key}"
    if edit_key not in st.session_state:
        st.session_state[edit_key] = db_value
    if changed_flag_key not in st.session_state:
        st.session_state[changed_flag_key] = False
    tmp_val = st.session_state[edit_key]
    is_modified = (tmp_val != db_value)
    is_not_default = (db_value != default_value)

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
        btn_count = len(btn_list)
        if btn_count > 0:
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
    return st.session_state["config"]
