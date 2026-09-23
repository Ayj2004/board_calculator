# -*- coding: utf-8 -*-
"""
价格计算模块
严格对应 Excel Sheet1 的公式逻辑。
所有计算结果以欧元为基准币种，再根据用户选择的币种换算显示。
"""
import math
from typing import Dict
# ============================================================
# 币种换算工具
# ============================================================
def convert_currency(amount_eur: float, target_currency: str,
                     cny_to_eur: float, cny_to_usd: float) -> float:
    """
    将欧元金额换算为目标币种。
    参数:
        amount_eur: 欧元金额
        target_currency: 目标币种 "EUR" / "USD" / "CNY"
        cny_to_eur: 人民币兑欧元汇率（1欧元=X人民币）
        cny_to_usd: 人民币兑美元汇率（1美元=X人民币）
    返回:
        换算后的金额
    """
    if target_currency == "EUR":
        return amount_eur
    elif target_currency == "CNY":
        return amount_eur * cny_to_eur
    elif target_currency == "USD":
        return amount_eur * cny_to_eur / cny_to_usd
    return amount_eur


def currency_symbol(currency: str) -> str:
    """返回币种符号"""
    return {"EUR": "€", "USD": "$", "CNY": "¥"}.get(currency, "")


# ============================================================
# 一、墙板 价格计算（所有墙板产品通用）
#   对应 Excel Sheet1 B2:F5
# ============================================================
def calc_wall_panel_unit_prices(
    product_price_config: Dict,
    actual_length_per_piece: float,
    cny_to_eur: float,
    cny_to_usd: float,
) -> Dict[str, float]:
    """
    计算墙板单支价格（三币种）。
    Excel 逻辑:
        D2 人民币价格 = (B2 + 1) * C2
        E2 欧元单支价格 = D2 / 7.6 + 0.2
        F2 美元单支价格 = D2 / 6.6
    """
    price_per_meter_cny = product_price_config["price_per_meter_cny"]
    eur_extra_fee = product_price_config["eur_extra_fee"]
    cny_extra_per_meter = product_price_config["cny_extra_per_meter"]

    price_cny_per_piece = (price_per_meter_cny + cny_extra_per_meter) * actual_length_per_piece
    price_eur_per_piece = price_cny_per_piece / cny_to_eur + eur_extra_fee
    price_usd_per_piece = price_cny_per_piece / cny_to_usd

    return {
        "cny": price_cny_per_piece,
        "eur": price_eur_per_piece,
        "usd": price_usd_per_piece,
    }


def calc_wall_panel_by_area(
    area_sqm: float,
    product_price_config: Dict,
    actual_length_per_piece: float,
    cny_to_eur: float,
    cny_to_usd: float,
) -> Dict:
    """
    墙板 —— 按面积计算。
    Excel 逻辑:
        B4 所需数量 = B3 / (C2 * 0.2)
        B5 总价 = B4 * E2
    """
    unit_prices = calc_wall_panel_unit_prices(
        product_price_config, actual_length_per_piece, cny_to_eur, cny_to_usd
    )
    panel_width_m = product_price_config["panel_width_m"]
    # 所需数量 = 面积 / (实际单支米数 × 板宽)
    pieces_needed = area_sqm / (actual_length_per_piece * panel_width_m)

    total_cny = pieces_needed * unit_prices["cny"]
    total_eur = pieces_needed * unit_prices["eur"]
    total_usd = pieces_needed * unit_prices["usd"]
    return {
        "method": "按面积",
        "input_area": area_sqm,
        "length_per_piece": actual_length_per_piece,
        "pieces_needed": pieces_needed,
        "unit_price_cny": unit_prices["cny"],
        "unit_price_eur": unit_prices["eur"],
        "unit_price_usd": unit_prices["usd"],
        "total_cny": total_cny,
        "total_eur": total_eur,
        "total_usd": total_usd,
    }


def calc_wall_panel_by_length(
    length_m: float,
    product_price_config: Dict,
    actual_length_per_piece: float,
    cny_to_eur: float,
    cny_to_usd: float,
) -> Dict:
    """
    墙板 —— 按长度计算。
    Excel 逻辑:
        E4 所需数量 = E3 / 0.2
        E5 总价 = E2 * E4
    """
    unit_prices = calc_wall_panel_unit_prices(
        product_price_config, actual_length_per_piece, cny_to_eur, cny_to_usd
    )
    panel_width_m = product_price_config["panel_width_m"]
    # 所需数量 = 长度 / 板宽
    pieces_needed = length_m / panel_width_m

    total_cny = pieces_needed * unit_prices["cny"]
    total_eur = pieces_needed * unit_prices["eur"]
    total_usd = pieces_needed * unit_prices["usd"]
    return {
        "method": "按长度",
        "input_length": length_m,
        "length_per_piece": actual_length_per_piece,
        "pieces_needed": pieces_needed,
        "unit_price_cny": unit_prices["cny"],
        "unit_price_eur": unit_prices["eur"],
        "unit_price_usd": unit_prices["usd"],
        "total_cny": total_cny,
        "total_eur": total_eur,
        "total_usd": total_usd,
    }


# ============================================================
# 二、围栏板 价格计算
#   对应 Excel Sheet1 B9:D18
# ============================================================
def calc_fence(
    fence_length_m: float,
    fence_config: Dict,
    cny_to_eur: float,
    cny_to_usd: float,
) -> Dict:
    """
    围栏板价格计算。
    Excel 逻辑:
        B10 所需立柱 = B9/1.8 + 1
        B11 所需围栏板(9片) = B9/1.8 * 9
        B12 所需围栏板(11片) = B9/1.8 * 11
        B13 侧条 = B10
        B14 凹条 = B10
        B15 凸条 = B10
        B16 柱座 = B10
        B17 柱帽 = B10
        B18 膨胀丝 = B10 * 4
        各项总价 = 数量 × 单价（欧元）
    """
    section_len = fence_config["section_length_m"]
    boards_9 = fence_config["boards_per_section_9"]
    boards_11 = fence_config["boards_per_section_11"]
    bolts_per_post = fence_config["bolts_per_post"]
    # 所需立柱数 = 长度/1.8 + 1
    post_count = fence_length_m / section_len + 1
    # 构建各项明细
    items = [
        {
            "key": "post",
            "name": "立柱",
            "quantity": post_count,
            "unit": "根",
            "unit_price_eur": fence_config["post"]["unit_price_eur"],
        },
        {
            "name": "1.5米高围栏板（9层）",
            "quantity": fence_length_m / section_len * boards_9,
            "unit": "片",
            "unit_price_eur": fence_config["fence_board_9"]["unit_price_eur"],
        },
        {
            "name": "1.8米高围栏板（11层）",
            "quantity": fence_length_m / section_len * boards_11,
            "unit": "片",
            "unit_price_eur": fence_config["fence_board_11"]["unit_price_eur"],
        },
        {
            "key": "side_strip",
            "name": "侧条",
            "quantity": post_count,
            "unit": "根",
            "unit_price_eur": fence_config["side_strip"]["unit_price_eur"],
        },
        {
            "key": "groove_strip",
            "name": "凹条",
            "quantity": post_count,
            "unit": "根",
            "unit_price_eur": fence_config["groove_strip"]["unit_price_eur"],
        },
        {
            "key": "tongue_strip",
            "name": "凸条",
            "quantity": post_count,
            "unit": "根",
            "unit_price_eur": fence_config["tongue_strip"]["unit_price_eur"],
        },
        {
            "key": "post_base",
            "name": "柱座",
            "quantity": post_count,
            "unit": "个",
            "unit_price_eur": fence_config["post_base"]["unit_price_eur"],
        },
        {
            "key": "post_cap",
            "name": "柱帽",
            "quantity": post_count,
            "unit": "个",
            "unit_price_eur": fence_config["post_cap"]["unit_price_eur"],
        },
        {
            "name": "膨胀丝",
            "quantity": post_count * bolts_per_post,
            "unit": "个",
            "unit_price_eur": fence_config["expansion_bolt"]["unit_price_eur"],
        },
    ]
    # 计算每项总价（欧元）
    total_eur = 0.0
    for item in items:
        item["total_eur"] = item["quantity"] * item["unit_price_eur"]
        total_eur += item["total_eur"]
    return {
        "fence_length": fence_length_m,
        "post_count": post_count,
        "items": items,
        "total_eur": total_eur,
    }


# ============================================================
# 三、地板 价格计算
#   对应 Excel Sheet1 B23:F30
# ============================================================
def calc_floor(
    area_sqm: float,
    floor_config: Dict,
    cny_to_eur: float,
    cny_to_usd: float,
) -> Dict:
    """
    地板价格计算。
    Excel 逻辑:
        B24 WPC地板数量 = B23/0.406；总价 = 3.6 × 数量
        B25 龙骨 = B23*3；总价 = B25/2.9 × 1.8
        B26 美固钉 = B23*6；总价 = 0.05 × 数量
        B27 卡扣 = B23*21；总价 = 0.05 × 数量
        B28 自攻丝 = B23*21；总价 = 0.02 × 数量
        B29 起始扣 = SQRT(B23)/0.5*2；总价 = 0.05 × 数量
        B30 封边 = SQRT(B23)/2.9*2；总价 = 2.6 × 数量
    """
    cfg = floor_config
    sqrt_area = math.sqrt(area_sqm)
    items = [
        {
            "name": "WPC地板",
            "quantity": area_sqm / cfg["wpc_floor"]["area_per_piece"],
            "spec": cfg["wpc_floor"]["spec"],
            "unit": cfg["wpc_floor"]["unit"],
            "unit_price_eur": cfg["wpc_floor"]["unit_price_eur"],
        },
        {
            "name": "龙骨",
            "quantity": area_sqm * cfg["keel"]["length_multiplier"],
            "spec": cfg["keel"]["spec"],
            "unit": cfg["keel"]["unit"],
            "unit_price_eur": cfg["keel"]["unit_price_eur"],
            "total_mode": "by_piece",
            "piece_length": cfg["keel"]["piece_length_m"],
        },
        {
            "name": "美固钉",
            "quantity": area_sqm * cfg["nail"]["count_per_sqm"],
            "spec": cfg["nail"]["spec"],
            "unit": cfg["nail"]["unit"],
            "unit_price_eur": cfg["nail"]["unit_price_eur"],
        },
        {
            "name": "卡扣",
            "quantity": area_sqm * cfg["clip"]["count_per_sqm"],
            "spec": cfg["clip"]["spec"],
            "unit": cfg["clip"]["unit"],
            "unit_price_eur": cfg["clip"]["unit_price_eur"],
        },
        {
            "name": "自攻丝",
            "quantity": area_sqm * cfg["self_tapping_screw"]["count_per_sqm"],
            "spec": cfg["self_tapping_screw"]["spec"],
            "unit": cfg["self_tapping_screw"]["unit"],
            "unit_price_eur": cfg["self_tapping_screw"]["unit_price_eur"],
        },
        {
            "name": "起始扣",
            "quantity": sqrt_area / 0.5 * 2,
            "spec": cfg["starter_clip"]["spec"],
            "unit": cfg["starter_clip"]["unit"],
            "unit_price_eur": cfg["starter_clip"]["unit_price_eur"],
        },
        {
            "name": "封边",
            "quantity": sqrt_area / cfg["edge_band"]["piece_length_m"] * 2,
            "spec": cfg["edge_band"]["spec"],
            "unit": cfg["edge_band"]["unit"],
            "unit_price_eur": cfg["edge_band"]["unit_price_eur"],
        },
    ]
    # 计算总价
    total_eur = 0.0
    for item in items:
        if item.get("total_mode") == "by_piece":
            piece_count = item["quantity"] / item["piece_length"]
            item["piece_count"] = piece_count
            item["total_eur"] = piece_count * item["unit_price_eur"]
        else:
            item["total_eur"] = item["quantity"] * item["unit_price_eur"]
        total_eur += item["total_eur"]
    return {
        "area": area_sqm,
        "items": items,
        "total_eur": total_eur,
    }


# ============================================================
# 四、配件重量计算
#   对应 Excel Sheet2 配件重量公式
# ============================================================
def calc_accessory_weight(
    fence_length_m: float,
    fence_config: Dict,
    accessory_config: Dict,
) -> Dict:
    """
    配件重量计算（依赖围栏板的立柱数等）。
    Excel 逻辑:
        配件重量 = CEILING(
            (1.7*1.8)*立柱数 + 0.18*侧条数 + 0.414*凹条数
            + 0.432*凸条数 + 2.14*柱座数 + 2.14*柱帽数, 1)
    """
    section_len = fence_config["section_length_m"]
    post_count = fence_length_m / section_len + 1
    weight = (
        accessory_config["post_weight_per_piece"] * post_count
        + accessory_config["side_strip_weight"] * post_count
        + accessory_config["groove_strip_weight"] * post_count
        + accessory_config["tongue_strip_weight"] * post_count
        + accessory_config["post_base_weight"] * post_count
        + accessory_config["post_cap_weight"] * post_count
    )
    # CEILING(..., 1) 向上取整
    weight_ceil = math.ceil(weight)
    return {
        "fence_length": fence_length_m,
        "post_count": post_count,
        "raw_weight": weight,
        "weight_kg": weight_ceil,
    }
