# -*- coding: utf-8 -*-
"""
包装计算模块
严格对应 Excel Sheet2 的公式逻辑。
支持 180 支以下（单托盘）和 180 支以上（多托盘）两种模式，自动判断。
"""

import math
from typing import Dict


def _round_up(value: float, decimals: int = 0) -> float:
    """
    模拟 Excel ROUNDUP 函数：向上舍入。
    ROUNDUP(x, 0) = 向上取整到整数。
    """
    if decimals == 0:
        return math.ceil(value)
    factor = 10 ** decimals
    return math.ceil(value * factor) / factor


def _ceiling(value: float, significance: float = 1) -> float:
    """
    模拟 Excel CEILING 函数：将数字向上舍入到最接近的指定倍数。
    CEILING(x, 1) = 向上取整。
    """
    if significance == 0:
        return 0
    return math.ceil(value / significance) * significance


def calc_package(
    pieces: int,
    length_per_piece: float,
    weight_per_meter: float,
    pkg_config: Dict,
) -> Dict:
    """
    包装计算（自动判断 180 支以下/以上）。

    Excel 逻辑（以长城板为例）:
    --- 180支以下 ---
        A9 长度 = B7 + 0.02
        B9 宽度 = 1.15
        C9 高度 = A7/5*0.026 + 0.3
        A11 包装方数 = ROUNDUP(A9*B9*C9, 0)
        B11 包装重量 = ROUNDUP(C7*B7*A7 + 30, 0)

    --- 180支以上 ---
        E9 长度 = F7 + 0.02
        F9 宽度 = 1.15
        G9 高度 = 180/5*0.026 + 0.3  (固定按满托盘计算)
        G11 打包托盘数量 = CEILING(E7/180, 1)
        E11 包装总方数 = CEILING(PRODUCT(E9,F9,G9), 1) * G11
        F11 包装重量 = CEILING(G7*F7*E7 + (30*G11), 1)

    参数:
        pieces: 数量（支）
        length_per_piece: 单支长度(米)
        weight_per_meter: 米重(KG/米)
        pkg_config: 该板材的包装配置字典
    返回:
        包含尺寸、方数、重量、托盘数等的字典
    """
    pallet_capacity = pkg_config["pallet_capacity"]  # 180
    width = pkg_config["width_m"]                     # 1.15
    length_extra = pkg_config["length_extra_m"]       # 0.02
    height_base = pkg_config["height_base_m"]         # 0.3
    height_divisor = pkg_config["height_divisor"]     # 5 或 7
    height_coeff = pkg_config["height_coeff"]         # 0.026 / 0.02 / 0.023
    packing_weight = pkg_config["packing_weight_kg"]  # 30

    # 包装长度 = 单支长度 + 0.02
    pkg_length = length_per_piece + length_extra
    # 包装宽度
    pkg_width = width

    if pieces <= pallet_capacity:
        # ===== 180支以下：单托盘 =====
        # 高度 = 数量/除数*系数 + 基数
        pkg_height = pieces / height_divisor * height_coeff + height_base
        # 体积 = 长 × 宽 × 高
        volume = pkg_length * pkg_width * pkg_height
        # 包装方数 = ROUNDUP(体积, 0)
        total_cbm = _round_up(volume, 0)
        # 包装重量 = ROUNDUP(米重×单支长×数量 + 30, 0)
        total_weight = _round_up(
            weight_per_meter * length_per_piece * pieces + packing_weight, 0
        )
        pallet_count = 1
        mode = "180支以下（单托盘）"

    else:
        # ===== 180支以上：多托盘 =====
        # 每托盘高度按满托盘计算（Excel中固定为 180/除数*系数+基数）
        # 注意：围栏板 Excel 中用的是 182 而非 180
        over_height_pieces = pkg_config.get("over_height_pieces", pallet_capacity)
        pkg_height = over_height_pieces / height_divisor * height_coeff + height_base
        # 单托盘体积
        single_pallet_volume = pkg_length * pkg_width * pkg_height
        # 打包托盘数量 = CEILING(数量/180, 1)
        pallet_count = _ceiling(pieces / pallet_capacity, 1)
        # 包装总方数 = CEILING(单托盘体积, 1) × 托盘数
        total_cbm = _ceiling(single_pallet_volume, 1) * pallet_count
        # 包装重量 = CEILING(米重×单支长×数量 + 30×托盘数, 1)
        total_weight = _ceiling(
            weight_per_meter * length_per_piece * pieces + packing_weight * pallet_count, 1
        )
        mode = "180支以上（多托盘）"

    return {
        "mode": mode,
        "pieces": pieces,
        "length_per_piece": length_per_piece,
        "weight_per_meter": weight_per_meter,
        "pkg_length": pkg_length,
        "pkg_width": pkg_width,
        "pkg_height": pkg_height,
        "single_pallet_volume": pkg_length * pkg_width * pkg_height,
        "pallet_count": int(pallet_count),
        "total_cbm": total_cbm,
        "total_weight_kg": total_weight,
    }
