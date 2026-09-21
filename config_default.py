# coding: utf-8 --
""" 出厂默认配置文件 —— 不要随意修改本文件，除非要更改出厂默认值。
用户在界面上的修改会保存到同目录下的 config.json，优先级高于本文件。 """

# ============================================================
# 墙板产品元数据（新增/删除产品只修改这里）
# ============================================================
WALL_PANEL_PRODUCTS = [
    # 原有产品（兼容历史数据）
    {
        "name": "二代共挤四代长城板",
        "price_key": "wall_panel_price",
        "package_key": "wall_panel",
    },
    # 新增6款产品
    {
        "name": "二代共挤半包四孔长城板",
        "price_key": "wall_panel_4hole_half_price",
        "package_key": "wall_panel_4hole_half",
    },
    {
        "name": "二代共挤五孔长城板",
        "price_key": "wall_panel_5hole_price",
        "package_key": "wall_panel_5hole",
    },
    {
        "name": "二代共挤圆弧四孔长城板",
        "price_key": "wall_panel_4hole_arc_price",
        "package_key": "wall_panel_4hole_arc",
    },
    {
        "name": "二代共挤长城板",
        "price_key": "wall_panel_standard_v2_price",
        "package_key": "wall_panel_standard_v2",
    },
    {
        "name": "二代共挤半包小长城板",
        "price_key": "wall_panel_mini_half_price",
        "package_key": "wall_panel_mini_half",
    },
    {
        "name": "二代共挤墙板",
        "price_key": "wall_panel_flat_price",
        "package_key": "wall_panel_flat",
    },
]

# ============================================================
# 一、汇率设置（人民币 CNY 为基准）
# ============================================================
DEFAULT_EXCHANGE_RATE = {
    "cny_to_eur": 7.6,   # 1 欧元 = 7.6 人民币（CNY/EUR）
    "cny_to_usd": 6.6,   # 1 美元 = 6.6 人民币（CNY/USD）
}

# ============================================================
# 二、墙板产品 —— 价格参数（已移除 length_calc_extra_pieces）
# ============================================================
# 原有产品：二代共挤四代长城板
DEFAULT_WALL_PANEL_PRICE = {
    "price_per_meter_cny": 18.93,
    "default_length_per_piece": 2.9,
    "panel_width_m": 0.2,
    "eur_extra_fee": 0.2,
    "cny_extra_per_meter": 1.0,
    "moq_pieces": 50,
}

# 新增1：二代共挤半包四孔长城板
DEFAULT_WALL_PANEL_4HOLE_HALF_PRICE = {
    "price_per_meter_cny": 18.3,
    "default_length_per_piece": 2.9,
    "panel_width_m": 0.2,
    "eur_extra_fee": 0.2,
    "cny_extra_per_meter": 1.0,
    "moq_pieces": 50,
}

# 新增2：二代共挤五孔长城板
DEFAULT_WALL_PANEL_5HOLE_PRICE = {
    "price_per_meter_cny": 19.9,
    "default_length_per_piece": 2.9,
    "panel_width_m": 0.2,
    "eur_extra_fee": 0.2,
    "cny_extra_per_meter": 1.0,
    "moq_pieces": 50,
}

# 新增3：二代共挤圆弧四孔长城板
DEFAULT_WALL_PANEL_4HOLE_ARC_PRICE = {
    "price_per_meter_cny": 17.2,
    "default_length_per_piece": 2.9,
    "panel_width_m": 0.2,
    "eur_extra_fee": 0.2,
    "cny_extra_per_meter": 1.0,
    "moq_pieces": 50,
}

# 新增4：二代共挤长城板
DEFAULT_WALL_PANEL_STANDARD_V2_PRICE = {
    "price_per_meter_cny": 28.4,
    "default_length_per_piece": 2.9,
    "panel_width_m": 0.22,
    "eur_extra_fee": 0.2,
    "cny_extra_per_meter": 1.0,
    "moq_pieces": 50,
}

# 新增5：二代共挤半包小长城板
DEFAULT_WALL_PANEL_MINI_HALF_PRICE = {
    "price_per_meter_cny": 11.48,
    "default_length_per_piece": 2.9,
    "panel_width_m": 0.157,
    "eur_extra_fee": 0.2,
    "cny_extra_per_meter": 1.0,
    "moq_pieces": 50,
}

# 新增6：二代共挤墙板
DEFAULT_WALL_PANEL_FLAT_PRICE = {
    "price_per_meter_cny": 12.2,
    "default_length_per_piece": 2.9,
    "panel_width_m": 0.136,
    "eur_extra_fee": 0.2,
    "cny_extra_per_meter": 1.0,
    "moq_pieces": 50,
}

# ============================================================
# 三、围栏板 —— 各配件单价（欧元）
# ============================================================
DEFAULT_FENCE_PRICE = {
    "post": {"unit_price_eur": 16.0},
    "fence_board_9": {"unit_price_eur": 3.6},
    "fence_board_11": {"unit_price_eur": 3.6},
    "side_strip": {"unit_price_eur": 1.5},
    "groove_strip": {"unit_price_eur": 3.0},
    "tongue_strip": {"unit_price_eur": 3.0},
    "post_base": {"unit_price_eur": 5.0},
    "post_cap": {"unit_price_eur": 1.0},
    "expansion_bolt": {"unit_price_eur": 0.2},
    "section_length_m": 1.8,
    "boards_per_section_9": 9,
    "boards_per_section_11": 11,
    "bolts_per_post": 4,
    "moq_pieces": 50,
}

# ============================================================
# 四、地板 —— 各配件单价（欧元）及计算系数
# ============================================================
DEFAULT_FLOOR_PRICE = {
    "wpc_floor": {
        "unit_price_eur": 7.3,
        "area_per_piece": 0.406,
        "spec": "2.9米常规尺寸",
        "unit": "支",
    },
    "keel": {
        "unit_price_eur": 1.8,
        "length_multiplier": 3,
        "piece_length_m": 2.9,
        "spec": "总需长度，可除2.9得支数",
        "unit": "米",
    },
    "nail": {
        "unit_price_eur": 0.05,
        "count_per_sqm": 6,
        "spec": "无",
        "unit": "个",
    },
    "clip": {
        "unit_price_eur": 0.05,
        "count_per_sqm": 21,
        "spec": "无",
        "unit": "个",
    },
    "self_tapping_screw": {
        "unit_price_eur": 0.02,
        "count_per_sqm": 21,
        "spec": "无",
        "unit": "个",
    },
    "starter_clip": {
        "unit_price_eur": 0.05,
        "spec": "无",
        "unit": "个",
    },
    "edge_band": {
        "unit_price_eur": 2.6,
        "piece_length_m": 2.9,
        "spec": "2.9米常规尺寸",
        "unit": "支",
    },
    "moq_pieces": 50,
}

# ============================================================
# 五、包装计算 —— 各板材默认参数
# ============================================================
DEFAULT_PACKAGE = {
    # 原有：二代共挤四代长城板
    "wall_panel": {
        "default_length_per_piece": 2.9,
        "default_weight_per_meter": 2.95,
        "width_m": 1.15,
        "length_extra_m": 0.02,
        "height_base_m": 0.3,
        "height_divisor": 5,
        "height_coeff": 0.026,
        "pallet_capacity": 180,
        "packing_weight_kg": 30,
    },
    # 新增1：二代共挤半包四孔长城板
    "wall_panel_4hole_half": {
        "default_length_per_piece": 2.9,
        "default_weight_per_meter": 3.0,
        "width_m": 1.15,
        "length_extra_m": 0.02,
        "height_base_m": 0.3,
        "height_divisor": 5,
        "height_coeff": 0.026,
        "pallet_capacity": 180,
        "packing_weight_kg": 30,
    },
    # 新增2：二代共挤五孔长城板
    "wall_panel_5hole": {
        "default_length_per_piece": 2.9,
        "default_weight_per_meter": 3.0,
        "width_m": 1.15,
        "length_extra_m": 0.02,
        "height_base_m": 0.3,
        "height_divisor": 5,
        "height_coeff": 0.026,
        "pallet_capacity": 180,
        "packing_weight_kg": 30,
    },
    # 新增3：二代共挤圆弧四孔长城板
    "wall_panel_4hole_arc": {
        "default_length_per_piece": 2.9,
        "default_weight_per_meter": 2.5,
        "width_m": 1.15,
        "length_extra_m": 0.02,
        "height_base_m": 0.3,
        "height_divisor": 5,
        "height_coeff": 0.026,
        "pallet_capacity": 180,
        "packing_weight_kg": 30,
    },
    # 新增4：二代共挤长城板
    "wall_panel_standard_v2": {
        "default_length_per_piece": 2.9,
        "default_weight_per_meter": 3.9,
        "width_m": 1.15,
        "length_extra_m": 0.02,
        "height_base_m": 0.3,
        "height_divisor": 5,
        "height_coeff": 0.034,
        "pallet_capacity": 180,
        "packing_weight_kg": 30,
    },
    # 新增5：二代共挤半包小长城板
    "wall_panel_mini_half": {
        "default_length_per_piece": 2.9,
        "default_weight_per_meter": 1.85,
        "width_m": 1.15,
        "length_extra_m": 0.02,
        "height_base_m": 0.3,
        "height_divisor": 7,
        "height_coeff": 0.013,
        "pallet_capacity": 180,
        "packing_weight_kg": 30,
    },
    # 新增6：二代共挤墙板
    "wall_panel_flat": {
        "default_length_per_piece": 2.9,
        "default_weight_per_meter": 1.75,
        "width_m": 1.15,
        "length_extra_m": 0.02,
        "height_base_m": 0.3,
        "height_divisor": 7,
        "height_coeff": 0.021,
        "pallet_capacity": 180,
        "packing_weight_kg": 30,
    },
    # 围栏板
    "fence": {
        "default_length_per_piece": 1.8,
        "default_weight_per_meter": 2.25,
        "width_m": 1.15,
        "length_extra_m": 0.02,
        "height_base_m": 0.3,
        "height_divisor": 7,
        "height_coeff": 0.02,
        "pallet_capacity": 180,
        "packing_weight_kg": 30,
        "over_height_pieces": 182,
    },
    # 地板
    "floor": {
        "default_length_per_piece": 2.9,
        "default_weight_per_meter": 2.95,
        "width_m": 1.15,
        "length_extra_m": 0.02,
        "height_base_m": 0.3,
        "height_divisor": 7,
        "height_coeff": 0.023,
        "pallet_capacity": 180,
        "packing_weight_kg": 30,
    },
}

# ============================================================
# 六、配件重量计算参数
# ============================================================
DEFAULT_ACCESSORY_WEIGHT = {
    "post_weight_per_piece": 1.7 * 1.8,
    "side_strip_weight": 0.18,
    "groove_strip_weight": 0.414,
    "tongue_strip_weight": 0.432,
    "post_base_weight": 2.14,
    "post_cap_weight": 2.14,
}

# ============================================================
# 合并为完整默认配置
# ============================================================
DEFAULT_CONFIG = {
    "exchange_rate": DEFAULT_EXCHANGE_RATE,
    # 墙板价格配置（原有+新增）
    "wall_panel_price": DEFAULT_WALL_PANEL_PRICE,
    "wall_panel_4hole_half_price": DEFAULT_WALL_PANEL_4HOLE_HALF_PRICE,
    "wall_panel_5hole_price": DEFAULT_WALL_PANEL_5HOLE_PRICE,
    "wall_panel_4hole_arc_price": DEFAULT_WALL_PANEL_4HOLE_ARC_PRICE,
    "wall_panel_standard_v2_price": DEFAULT_WALL_PANEL_STANDARD_V2_PRICE,
    "wall_panel_mini_half_price": DEFAULT_WALL_PANEL_MINI_HALF_PRICE,
    "wall_panel_flat_price": DEFAULT_WALL_PANEL_FLAT_PRICE,
    # 原有其他配置
    "fence_price": DEFAULT_FENCE_PRICE,
    "floor_price": DEFAULT_FLOOR_PRICE,
    "package": DEFAULT_PACKAGE,
    "accessory_weight": DEFAULT_ACCESSORY_WEIGHT,
}
