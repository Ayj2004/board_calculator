# -*- coding: utf-8 -*-
"""
价格计算模块
严格对应 Excel Sheet1 的公式逻辑。
所有计算结果以欧元为基准币种，再根据用户选择的币种换算显示。
"""


import math
from typing import Dict, List, Tuple



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
        # 欧元 → 人民币：× CNY/EUR
        return amount_eur * cny_to_eur
    elif target_currency == "USD":
        # 欧元 → 美元：欧元 × (CNY/EUR) ÷ (CNY/USD)
        return amount_eur * cny_to_eur / cny_to_usd
    return amount_eur



def currency_symbol(currency: str) -> str:
    """返回币种符号"""
    return {"EUR": "€", "USD": "$", "CNY": "¥"}.get(currency, "")



# ============================================================
# 一、二代共挤四代长城板 价格计算
#    对应 Excel Sheet1 B2:F5
# ============================================================
def calc_wall_panel_unit_prices(
    price_per_meter_cny: float,
    length_per_piece: float,
    cny_to_eur: float,
    cny_to_usd: float,
    eur_extra_fee: float = 0.2,
    cny_extra_per_meter: float = 1.0,
) -> Dict[str, float]:
    """
    计算长城板单支价格（三币种）。

    Excel 逻辑:
        D2 人民币价格 = (B2 + 1) * C2
        E2 欧元单支价格 = D2 / 7.6 + 0.2
        F2 美元单支价格 = D2 / 6.6

    参数:
        price_per_meter_cny: 含税单价（人民币/米）B2
        length_per_piece: 单支米数 C2
        cny_to_eur: CNY/EUR 汇率
        cny_to_usd: CNY/USD 汇率
        eur_extra_fee: 欧元额外加价 E2 中的 +0.2
        cny_extra_per_meter: 每米加价 (B2+1) 中的 +1
    返回:
        {"cny": 人民币单支价, "eur": 欧元单支价, "usd": 美元单支价}
    """
    # 人民币单支价格 = (含税/米 + 1) × 单支米数
    price_cny_per_piece = (price_per_meter_cny + cny_extra_per_meter) * length_per_piece
    # 欧元单支价格 = 人民币单支价 / CNY/EUR + 0.2
    price_eur_per_piece = price_cny_per_piece / cny_to_eur + eur_extra_fee
    # 美元单支价格 = 人民币单支价 / CNY/USD
    price_usd_per_piece = price_cny_per_piece / cny_to_usd


    return {
        "cny": price_cny_per_piece,
        "eur": price_eur_per_piece,
        "usd": price_usd_per_piece,
    }



def calc_wall_panel_by_area(
    area_sqm: float,
    length_per_piece: float,
    price_per_meter_cny: float,
    cny_to_eur: float,
    cny_to_usd: float,
    panel_width_m: float = 0.2,
    eur_extra_fee: float = 0.2,
    cny_extra_per_meter: float = 1.0,
) -> Dict:
    """
    长城板 —— 按面积计算。

    Excel 逻辑:
        B4 所需数量 = B3 / (C2 * 0.2)
        B5 总价 = B4 * E2

    参数:
        area_sqm: 面积（平方米）B3
        length_per_piece: 单支米数 C2
        price_per_meter_cny: 含税单价（人民币/米）B2
        panel_width_m: 板材宽度（米），默认0.2
    返回:
        包含数量、单支价、总价等信息的字典
    """
    unit_prices = calc_wall_panel_unit_prices(
        price_per_meter_cny, length_per_piece,
        cny_to_eur, cny_to_usd, eur_extra_fee, cny_extra_per_meter
    )
    # 所需数量 = 面积 / (单支米数 × 板宽)
    pieces_needed = area_sqm / (length_per_piece * panel_width_m)
    # 各币种总价
    total_cny = pieces_needed * unit_prices["cny"]
    total_eur = pieces_needed * unit_prices["eur"]
    total_usd = pieces_needed * unit_prices["usd"]


    return {
        "method": "按面积",
        "input_area": area_sqm,
        "length_per_piece": length_per_piece,
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
    price_per_meter_cny: float,
    cny_to_eur: float,
    cny_to_usd: float,
    length_per_piece: float = 2.9,
    panel_width_m: float = 0.2,
    eur_extra_fee: float = 0.2,
    cny_extra_per_meter: float = 1.0,
    extra_pieces: float = 5,
) -> Dict:
    """
    长城板 —— 按长度计算。

    Excel 逻辑:
        E4 所需数量 = E3 / 0.2 + 5
        E5 总价 = E2 * E4

    参数:
        length_m: 长度（米）E3
        length_per_piece: 单支米数（用于计算单支价格，不影响数量）
        panel_width_m: 板材宽度（米），默认0.2
        extra_pieces: 额外余量支数，默认5
    """
    unit_prices = calc_wall_panel_unit_prices(
        price_per_meter_cny, length_per_piece,
        cny_to_eur, cny_to_usd, eur_extra_fee, cny_extra_per_meter
    )
    # 所需数量 = 长度 / 板宽 + 5（余量）
    pieces_needed = length_m / panel_width_m + extra_pieces
    # 各币种总价
    total_cny = pieces_needed * unit_prices["cny"]
    total_eur = pieces_needed * unit_prices["eur"]
    total_usd = pieces_needed * unit_prices["usd"]


    return {
        "method": "按长度",
        "input_length": length_m,
        "length_per_piece": length_per_piece,
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
#    对应 Excel Sheet1 B9:D18
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

    参数:
        fence_length_m: 围栏总长度（米）B9
        fence_config: 围栏板配置字典（来自 config）
    返回:
        {"items": [明细列表], "total_eur": 总价, "post_count": 立柱数}
    """
    section_len = fence_config["section_length_m"]  # 1.8
    boards_9 = fence_config["boards_per_section_9"]
    boards_11 = fence_config["boards_per_section_11"]
    bolts_per_post = fence_config["bolts_per_post"]

    # 所需立柱数 = 长度/1.8 + 1
    post_count = fence_length_m / section_len + 1

    # 构建各项明细 —— 给6个重量配件增加key字段
    items = [
        {
            "key": "post",   # ✅新增
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
            "key": "side_strip", # ✅新增
            "name": "侧条",
            "quantity": post_count,
            "unit": "根",
            "unit_price_eur": fence_config["side_strip"]["unit_price_eur"],
        },
        {
            "key": "groove_strip", # ✅新增
            "name": "凹条",
            "quantity": post_count,
            "unit": "根",
            "unit_price_eur": fence_config["groove_strip"]["unit_price_eur"],
        },
        {
            "key": "tongue_strip", # ✅新增
            "name": "凸条",
            "quantity": post_count,
            "unit": "根",
            "unit_price_eur": fence_config["tongue_strip"]["unit_price_eur"],
        },
        {
            "key": "post_base", # ✅新增
            "name": "柱座",
            "quantity": post_count,
            "unit": "个",
            "unit_price_eur": fence_config["post_base"]["unit_price_eur"],
        },
        {
            "key": "post_cap", # ✅新增
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
#    对应 Excel Sheet1 B23:F30
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

    参数:
        area_sqm: 地板面积（平方米）B23
        floor_config: 地板配置字典
    """
    cfg = floor_config
    sqrt_area = math.sqrt(area_sqm)  # SQRT(B23)

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
            # 龙骨总价 = 总长度/2.9 × 单价（按支计价）
            "unit_price_eur": cfg["keel"]["unit_price_eur"],
            "total_mode": "by_piece",  # 标记需要按支数计算总价
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
            # 龙骨：总价 = 总长度/单支长度 × 单价
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
#    对应 Excel Sheet2 配件重量公式
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

    参数:
        fence_length_m: 围栏长度（米）
        fence_config: 围栏配置
        accessory_config: 配件重量配置
    """
    section_len = fence_config["section_length_m"]
    post_count = fence_length_m / section_len + 1  # 立柱数 = 侧条/凹条/凸条/柱座/柱帽数


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