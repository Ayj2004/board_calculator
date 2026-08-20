# -*- coding: utf-8 -*-
"""
出厂默认配置文件
—— 不要随意修改本文件，除非要更改出厂默认值。
用户在界面上的修改会保存到同目录下的 config.json，优先级高于本文件。
"""

# ============================================================
# 一、汇率设置（人民币 CNY 为基准）
# ============================================================
DEFAULT_EXCHANGE_RATE = {
    "cny_to_eur": 7.6,   # 1 欧元 = 7.6 人民币（CNY/EUR）
    "cny_to_usd": 6.6,   # 1 美元 = 6.6 人民币（CNY/USD）
}

# ============================================================
# 二、二代共挤四代长城板 —— 价格参数
# ============================================================
DEFAULT_WALL_PANEL_PRICE = {
    "price_per_meter_cny": 18.93,  # 含税单价（人民币/米），对应 Excel B2
    "default_length_per_piece": 2.9,  # 单支米数默认值，对应 Excel C2
    "panel_width_m": 0.2,  # 板材宽度（米），用于面积/长度换算数量
    "eur_extra_fee": 0.2,  # 欧元单支价格额外加价，对应 Excel E2 中的 +0.2
    "cny_extra_per_meter": 1.0,  # 人民币价格计算时每米加价，对应 Excel (B2+1) 中的 +1
    "length_calc_extra_pieces": 5,  # 按长度计算时额外增加的支数（余量），对应 Excel E4 中的 +5
}

# ============================================================
# 三、围栏板 —— 各配件单价（欧元）
#    对应 Excel Sheet1 B9:D18 区域
# ============================================================
DEFAULT_FENCE_PRICE = {
    "post": {"unit_price_eur": 16.0},       # 立柱 B10/C10
    "fence_board_9": {"unit_price_eur": 3.6},  # 围栏板(每段9片) B11/C11
    "fence_board_11": {"unit_price_eur": 3.6}, # 围栏板(每段11片) B12/C12
    "side_strip": {"unit_price_eur": 1.5},   # 侧条 B13/C13
    "groove_strip": {"unit_price_eur": 3.0}, # 凹条 B14/C14
    "tongue_strip": {"unit_price_eur": 3.0}, # 凸条 B15/C15
    "post_base": {"unit_price_eur": 5.0},    # 柱座 B16/C16
    "post_cap": {"unit_price_eur": 1.0},     # 柱帽 B17/C17
    "expansion_bolt": {"unit_price_eur": 0.2}, # 膨胀丝 B18/C18
    # 计算系数
    "section_length_m": 1.8,  # 每段围栏长度（米），对应 Excel 中 /1.8
    "boards_per_section_9": 9,   # 每段围栏板数量(9片方案)
    "boards_per_section_11": 11, # 每段围栏板数量(11片方案)
    "bolts_per_post": 4,         # 每根立柱膨胀丝数量
}

# ============================================================
# 四、地板 —— 各配件单价（欧元）及计算系数
#    对应 Excel Sheet1 B23:F30 区域
# ============================================================
DEFAULT_FLOOR_PRICE = {
    "wpc_floor": {
        "unit_price_eur": 3.6,    # WPC地板单价
        "area_per_piece": 0.406,  # 单支面积（平方米），对应 /0.406
        "spec": "2.9米常规尺寸",
        "unit": "支",
    },
    "keel": {
        "unit_price_eur": 1.8,    # 龙骨单价（欧元/支）
        "length_multiplier": 3,   # 龙骨总长度 = 面积 × 3
        "piece_length_m": 2.9,    # 每支龙骨长度，总价 = 总长度/2.9 × 单价
        "spec": "总需长度，可除2.9得支数",
        "unit": "米",
    },
    "nail": {
        "unit_price_eur": 0.05,   # 美固钉单价
        "count_per_sqm": 6,       # 每平米数量
        "spec": "无",
        "unit": "个",
    },
    "clip": {
        "unit_price_eur": 0.05,   # 卡扣单价
        "count_per_sqm": 21,      # 每平米数量
        "spec": "无",
        "unit": "个",
    },
    "self_tapping_screw": {
        "unit_price_eur": 0.02,   # 自攻丝单价
        "count_per_sqm": 21,       # 每平米数量
        "spec": "无",
        "unit": "个",
    },
    "starter_clip": {
        "unit_price_eur": 0.05,   # 起始扣单价
        "spec": "无",
        "unit": "个",
        # 数量 = SQRT(面积)/0.5*2
    },
    "edge_band": {
        "unit_price_eur": 2.6,    # 封边单价
        "piece_length_m": 2.9,    # 每支长度
        "spec": "2.9米常规尺寸",
        "unit": "支",
        # 数量 = SQRT(面积)/2.9*2
    },
}

# ============================================================
# 五、包装计算 —— 各板材默认参数
#    对应 Excel Sheet2
# ============================================================
DEFAULT_PACKAGE = {
    # 二代共挤四代长城板
    "wall_panel": {
        "default_length_per_piece": 2.9,   # 单支长度(米) B7/F7
        "default_weight_per_meter": 2.95,  # 米重(KG) C7/G7
        "width_m": 1.15,                   # 包装宽度(米) B9/F9
        "length_extra_m": 0.02,            # 包装长度余量 A9/E9 = 单支长度+0.02
        "height_base_m": 0.3,              # 高度基数
        "height_divisor": 5,               # 高度计算除数：数量/5
        "height_coeff": 0.026,             # 高度系数：数量/5*0.026
        "pallet_capacity": 180,            # 每托盘最大支数
        "packing_weight_kg": 30,           # 每托盘包装重量
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
        # 注意：Excel 中 180支以上高度用的是 182/7*0.02+0.3（固定182）
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
#    对应 Excel Sheet2 配件重量公式
#    配件重量 = CEILING((1.7*1.8)*立柱数 + 0.18*侧条数 + 0.414*凹条数
#                     + 0.432*凸条数 + 2.14*柱座数 + 2.14*柱帽数, 1)
# ============================================================
DEFAULT_ACCESSORY_WEIGHT = {
    "post_weight_per_piece": 1.7 * 1.8,  # 立柱单重 = 1.7*1.8
    "side_strip_weight": 0.18,           # 侧条单重
    "groove_strip_weight": 0.414,        # 凹条单重
    "tongue_strip_weight": 0.432,        # 凸条单重
    "post_base_weight": 2.14,            # 柱座单重
    "post_cap_weight": 2.14,             # 柱帽单重
}

# ============================================================
# 合并为完整默认配置
# ============================================================
DEFAULT_CONFIG = {
    "exchange_rate": DEFAULT_EXCHANGE_RATE,
    "wall_panel_price": DEFAULT_WALL_PANEL_PRICE,
    "fence_price": DEFAULT_FENCE_PRICE,
    "floor_price": DEFAULT_FLOOR_PRICE,
    "package": DEFAULT_PACKAGE,
    "accessory_weight": DEFAULT_ACCESSORY_WEIGHT,
}
