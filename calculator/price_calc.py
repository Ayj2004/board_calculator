# -- coding: utf-8 --
""" 价格计算模块
严格对应 Excel Sheet1 的公式逻辑。
所有计算结果以欧元为基准币种，再根据用户选择的币种换算显示。
【重要】本模块只输出原始浮点数；数量四舍五入 int(round()) 在展示层 _display 函数处理，本文件不做ceil/round
"""
import math
from typing import Dict, List, Any

# 币种换算工具
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

# 一、墙板 价格计算（所有墙板产品通用） 对应 Excel Sheet1 B2:F5
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

# 二、围栏板 价格计算 对应 Excel Sheet1 B9:D18
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
    qty_9board = fence_length_m / section_len * boards_9
    qty_11board = fence_length_m / section_len * boards_11
    accessory_items = [
        {
            "key": "post",
            "name": "立柱",
            "quantity": post_count,
            "unit": "根",
            "unit_price_eur": fence_config["post"]["unit_price_eur"],
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
    # 配件总价
    acc_total_eur = 0.0
    for it in accessory_items:
        it["total_eur"] = it["quantity"] * it["unit_price_eur"]
        acc_total_eur += it["total_eur"]
    # 两个板单独对象
    board_9 = {
        "name": "1.5米高围栏板（9层）",
        "quantity": qty_9board,
        "unit": "片",
        "unit_price_eur": fence_config["fence_board_9"]["unit_price_eur"],
        "total_eur": qty_9board * fence_config["fence_board_9"]["unit_price_eur"]
    }
    board_11 = {
        "name": "1.8米高围栏板（11层）",
        "quantity": qty_11board,
        "unit": "片",
        "unit_price_eur": fence_config["fence_board_11"]["unit_price_eur"],
        "total_eur": qty_11board * fence_config["fence_board_11"]["unit_price_eur"]
    }
    # 给页面表格渲染用的合并items（同时展示两种板）
    table_items = [board_9, board_11] + accessory_items
    return {
        "fence_length": fence_length_m,
        "post_count": post_count,
        "board_9": board_9,
        "board_11": board_11,
        "accessory_items": accessory_items,
        "table_items": table_items,
        "accessory_total_eur": acc_total_eur,
    }

# 三、地板 价格计算 对应 Excel Sheet1 B23:F30
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

# 四、配件重量计算 对应 Excel Sheet2 配件重量公式
def calc_accessory_weight(
    fence_length_m: float,
    fence_config: Dict,
    accessory_config: Dict,
) -> Dict:
    """
    配件重量计算（依赖围栏板的立柱数等）。
    Excel 逻辑:
        配件重量 = CEILING(
            post_weight *立柱数 + side_strip_weight*侧条数 + groove_strip_weight*凹条数
            + tongue_strip_weight*凸条数 + post_base_weight*柱座数 + post_cap_weight*柱帽数, 1)
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
    # CEILING(..., 1) 向上取整，重量规则不变
    weight_ceil = math.ceil(weight)
    return {
        "fence_length": fence_length_m,
        "post_count": post_count,
        "raw_weight": weight,
        "weight_kg": weight_ceil,
    }

# 报价生成函数
def fmt_price(v: float) -> str:
    return f"{v:.2f}"

def gen_quote_text_wall(
    input_label: str,
    len_piece: float,
    product_name: str,
    raw_need_qty: int,
    tolerance_qty: int,
    total_qty: int,
    disp_unit_price: float,
    disp_total: float,
    sym: str,
) -> str:
    return (
        f"对于{input_label}的{product_name}，单支长度{len_piece} m，共需{raw_need_qty}支，外加{tolerance_qty}支容错，共计{total_qty}支，"
        f"单支售价为{sym}{fmt_price(disp_unit_price)}，共计 {sym}{fmt_price(disp_total)}"
    )

# ===== 【改动重点】围栏报价生成：配件不再输出容错文字 =====
def gen_quote_text_fence_single(
    fence_length: float,
    height_name: str,
    board_line: Dict,
    accessory_line_list: List[Dict],
    total_sum: float,
    sym: str,
) -> str:
    lines = [f"围栏总长 {fence_length} m 的{height_name}："]
    lines.append(
        f"{board_line['name']}：共需{board_line['need_qty']}{board_line['unit']}，外加{board_line['tol']}{board_line['unit']}容错，共计{board_line['total_qty']}{board_line['unit']}，"
        f"单价 {sym}{fmt_price(board_line['unit_price'])}，小计 {sym}{fmt_price(board_line['subtotal'])}"
    )
    for line in accessory_line_list:
        # 配件tol固定0，不打印容错
        lines.append(
            f"{line['name']}：共需{line['need_qty']}{line['unit']}，共计{line['total_qty']}{line['unit']}，"
            f"单价 {sym}{fmt_price(line['unit_price'])}，小计 {sym}{fmt_price(line['subtotal'])}"
        )
    lines.append(f"整套合计：{sym}{fmt_price(total_sum)}")
    return "\n".join(lines)

def gen_quote_text_floor(
    area: float,
    product_name: str,
    line_list: List[Dict[str, Any]],
    total_sum: float,
    sym: str,
) -> str:
    lines = [f"对于{area} m²面积的{product_name}："]
    for line in line_list:
        if line["tol"] > 0:
            lines.append(
                f"{line['name']}：共需{line['need_qty']}{line['unit']}，外加{line['tol']}{line['unit']}容错，共计{line['total_qty']}{line['unit']}，"
                f"单价 {sym}{fmt_price(line['unit_price'])}，小计 {sym}{fmt_price(line['subtotal'])}"
            )
        else:
            lines.append(
                f"{line['name']}：共需{line['need_qty']}{line['unit']}，共计{line['total_qty']}{line['unit']}，"
                f"单价 {sym}{fmt_price(line['unit_price'])}，小计 {sym}{fmt_price(line['subtotal'])}"
            )
    lines.append(f"整套合计：{sym}{fmt_price(total_sum)}")
    return "\n".join(lines)
