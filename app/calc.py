from __future__ import annotations

import math
import re
from typing import Any


ARMOR = 380
STAT_KEYS = ("STR", "DEX", "INT", "LUK")
CONVERTED_STAT_SCALE = 4.0
REGULAR_DAMAGE_BOSS_WEIGHT = 0.0

K_ATTACK = "\uacf5\uaca9\ub825"
K_MAGIC = "\ub9c8\ub825"
K_DAMAGE = "\ub370\ubbf8\uc9c0"
K_BOSS = "\ubcf4\uc2a4 \ubaac\uc2a4\ud130 \ub370\ubbf8\uc9c0"
K_FINAL = "\ucd5c\uc885 \ub370\ubbf8\uc9c0"
K_IED = "\ubc29\uc5b4\uc728 \ubb34\uc2dc"
K_CRIT_RATE = "\ud06c\ub9ac\ud2f0\uceec \ud655\ub960"
K_CRIT_DAMAGE = "\ud06c\ub9ac\ud2f0\uceec \ub370\ubbf8\uc9c0"
K_ELEMENTAL = "\uc18d\uc131 \ub0b4\uc131 \ubb34\uc2dc"
K_COMBAT = "\uc804\ud22c\ub825"
K_HP = "\ucd5c\ub300 HP"

OPTION_ALIASES = {
    "STR": ("STR", "str"),
    "DEX": ("DEX", "dex"),
    "INT": ("INT", "int"),
    "LUK": ("LUK", "luk"),
    K_ATTACK: (K_ATTACK, "attack_power"),
    K_MAGIC: (K_MAGIC, "magic_power"),
    K_BOSS: (K_BOSS, "boss_damage"),
    K_DAMAGE: (K_DAMAGE, "damage"),
    K_HP: (K_HP, "max_hp", "hp"),
    "\uc62c\uc2a4\ud0ef": ("\uc62c\uc2a4\ud0ef", "all_stat"),
}

STAT_NAME_ALIASES = {
    K_ATTACK: (K_ATTACK, "attack_power"),
    K_MAGIC: (K_MAGIC, "magic_attack", "magic_power"),
    K_DAMAGE: (K_DAMAGE, "damage"),
    K_BOSS: (K_BOSS, "\ubcf4\uc2a4 \ub370\ubbf8\uc9c0", "boss_damage_multiplier"),
    K_FINAL: (K_FINAL, "final_damage_multiplier"),
    K_IED: (K_IED, "ignored_defence"),
    K_CRIT_RATE: (K_CRIT_RATE, "critical_rate"),
    K_CRIT_DAMAGE: (K_CRIT_DAMAGE, "critical_damage"),
    K_ELEMENTAL: (K_ELEMENTAL, "\uc18d\uc131 \ub0b4\uc131 \ubb34\uc2dc %", "elemental_resistance"),
    K_COMBAT: (K_COMBAT, "Combat Power", "combat_power"),
    K_HP: (K_HP, "HP", "MHP", "max_hp"),
}

WEAPON_CONSTANT_BY_PART = {
    "\ud55c\uc190\uac80": 1.2,
    "\ud55c\uc190\ub3c4\ub07c": 1.2,
    "\ud55c\uc190\ub454\uae30": 1.2,
    "\ub2e8\uac80": 1.3,
    "\ucf00\uc778": 1.3,
    "\uc644\ub4dc": 1.2,
    "\uc2a4\ud0dc\ud504": 1.2,
    "\ub450\uc190\uac80": 1.34,
    "\ub450\uc190\ub3c4\ub07c": 1.34,
    "\ub450\uc190\ub454\uae30": 1.34,
    "\ucc3d": 1.49,
    "\ud3f4\uc554": 1.49,
    "\ud65c": 1.3,
    "\uc11d\uad81": 1.35,
    "\uc544\ub300": 1.75,
    "\ub108\ud074": 1.7,
    "\uac74": 1.5,
    "\ub4c0\uc5bc\ubcf4\uc6b0\uac74": 1.3,
    "\ud578\ub4dc\uce90\ub17c": 1.5,
    "\ub370\uc2a4\ud398\ub77c\ub3c4": 1.3,
    "\uc5d0\ub108\uc9c0\uc18c\ub4dc": 1.5,
    "\uccb4\uc778": 1.3,
    "\ubd80\ucc44": 1.3,
    "\ud29c\ub108": 1.3,
    "\ube0c\ub808\uc2a4 \uc288\ud130": 1.3,
    "\uc5d0\uc778\uc158\ud2b8 \ubcf4\uc6b0": 1.3,
    "\ub9e4\uc9c1 \uac74\ud2c0\ub81b": 1.2,
    "ESP \ub9ac\ubbf8\ud130": 1.2,
    "\uc0e4\uc774\ub2dd \ub85c\ub4dc": 1.2,
    "\uc18c\uc6b8 \uc288\ud130": 1.7,
    "\uac74\ud2c0\ub81b \ub9ac\ubcfc\ubc84": 1.7,
    "\ucc28\ud06c\ub78c": 1.3,
    "\ud0dc\ub3c4": 1.49,
    "\ub300\uac80": 1.49,
    "\ub77c\ud53c\uc2a4": 1.49,
    "\ub77c\uc990\ub9ac": 1.49,
}

MASTERY_BY_PART = {
    "\uc644\ub4dc": 0.96,
    "\uc2a4\ud0dc\ud504": 0.96,
    "\ub9e4\uc9c1 \uac74\ud2c0\ub81b": 0.96,
    "ESP \ub9ac\ubbf8\ud130": 0.96,
    "\uc0e4\uc774\ub2dd \ub85c\ub4dc": 0.96,
    "\ud65c": 0.86,
    "\uc11d\uad81": 0.86,
    "\ub4c0\uc5bc\ubcf4\uc6b0\uac74": 0.86,
    "\uc5d0\uc778\uc158\ud2b8 \ubcf4\uc6b0": 0.86,
    "\ube0c\ub808\uc2a4 \uc288\ud130": 0.86,
    "\uac74": 0.86,
    "\ud578\ub4dc\uce90\ub17c": 0.86,
    "\uc544\ub300": 0.86,
}

DEFAULT_WEAPON_CONSTANT = 1.3
DEFAULT_MASTERY = 0.91
STAT_PERCENT_EFFECT_RATIO = 0.16
ATTACK_PERCENT_EFFECT_RATIO = 0.4
HEXA_MAIN_LEVEL_MULTIPLIER = (0, 1, 2, 3, 4, 6, 8, 10, 13, 16, 20)
HEXA_SKILL_EFFECT_PER_LEVEL = 0.00035
HEXA_SKILL_EFFECT_CAP = 0.2
HEXA_COMPLETION_LEVEL_CAP = 780
HEXA_INCOMPLETE_BASE_RATIO = 0.835
API_REQUIRED_SECTIONS = ("basic", "stat", "itemEquipment")
API_OPTIONAL_SECTIONS = (
    "symbol",
    "ability",
    "setEffect",
    "hyperStat",
    "otherStat",
    "hexamatrixStat",
    "union",
    "petEquipment",
    "linkSkill",
    "vmatrix",
    "hexamatrix",
    "ringExchangeSkillEquipment",
    "ringReserveSkillEquipment",
    "skill5",
    "skill6",
)
API_SECTION_LABELS = {
    "basic": "기본 정보",
    "stat": "종합 능력치",
    "itemEquipment": "장착 장비",
    "symbol": "심볼",
    "ability": "어빌리티",
    "setEffect": "세트 효과",
    "hyperStat": "하이퍼스탯",
    "otherStat": "기타 능력치",
    "hexamatrixStat": "HEXA 스탯",
    "union": "유니온",
    "petEquipment": "펫 장비",
    "linkSkill": "링크 스킬",
    "vmatrix": "V매트릭스",
    "hexamatrix": "HEXA 코어",
    "ringExchangeSkillEquipment": "링 익스체인지",
    "ringReserveSkillEquipment": "예비 특수 반지",
    "skill5": "5차 스킬",
    "skill6": "6차 스킬",
}

JOB_CONVERTED_MULTIPLIERS = [
    {"keywords": ("나이트로드", "나로"), "multiplier": 0.732874},
    {"keywords": ("나이트워커", "나워"), "multiplier": 0.759540},
    {"keywords": ("다크나이트", "닼나"), "multiplier": 0.554204},
    {"keywords": ("데몬슬레이어", "데슬"), "multiplier": 1.079699},
    {"keywords": ("데몬어벤져", "데벤"), "multiplier": 4.345210},
    {"keywords": ("듀얼블레이드", "듀블"), "multiplier": 0.814065},
    {"keywords": ("라라",), "multiplier": 0.818853},
    {"keywords": ("레테",), "multiplier": 0.814100},
    {"keywords": ("렌",), "multiplier": 0.789977},
    {"keywords": ("루미너스",), "multiplier": 0.837897},
    {"keywords": ("메르세데스",), "multiplier": 0.796837},
    {"keywords": ("메카닉",), "multiplier": 0.877388},
    {"keywords": ("미하일",), "multiplier": 0.828985},
    {"keywords": ("바이퍼",), "multiplier": 0.643093},
    {"keywords": ("배틀메이지", "배메"), "multiplier": 0.854250},
    {"keywords": ("보우마스터", "보마"), "multiplier": 0.665563},
    {"keywords": ("블래스터",), "multiplier": 0.780192},
    {"keywords": ("비숍",), "multiplier": 0.573232},
    {"keywords": ("섀도어",), "multiplier": 0.557984},
    {"keywords": ("소울마스터", "소마"), "multiplier": 0.889391},
    {"keywords": ("스트라이커",), "multiplier": 0.867825},
    {"keywords": ("신궁",), "multiplier": 0.789414},
    {"keywords": ("아델",), "multiplier": 0.648223},
    {"keywords": ("아란",), "multiplier": 0.877694},
    {"keywords": ("아크",), "multiplier": 0.850588},
    {"keywords": ("아크메이지(불,독)", "불독"), "multiplier": 0.612405},
    {"keywords": ("아크메이지(썬,콜)", "썬콜"), "multiplier": 0.501773},
    {"keywords": ("에반",), "multiplier": 0.802846},
    {"keywords": ("엔젤릭버스터", "엔버"), "multiplier": 0.804773},
    {"keywords": ("와일드헌터", "와헌"), "multiplier": 0.724107},
    {"keywords": ("윈드브레이커", "윈브"), "multiplier": 0.693556},
    {"keywords": ("은월",), "multiplier": 0.616369},
    {"keywords": ("일리움",), "multiplier": 0.702077},
    {"keywords": ("제논",), "multiplier": 1.097595},
    {"keywords": ("제로",), "multiplier": 0.939693},
    {"keywords": ("카데나",), "multiplier": 1.024886},
    {"keywords": ("카이저",), "multiplier": 0.922322},
    {"keywords": ("카인",), "multiplier": 0.665494},
    {"keywords": ("칼리",), "multiplier": 0.768886},
    {"keywords": ("캐논슈터", "캐논"), "multiplier": 0.775574},
    {"keywords": ("캡틴",), "multiplier": 0.815222},
    {"keywords": ("키네시스",), "multiplier": 0.657032},
    {"keywords": ("팔라딘",), "multiplier": 0.805109},
    {"keywords": ("패스파인더", "패파"), "multiplier": 0.748340},
    {"keywords": ("팬텀",), "multiplier": 0.807691},
    {"keywords": ("플레임위자드", "플위"), "multiplier": 0.738814},
    {"keywords": ("호영",), "multiplier": 0.421200},
    {"keywords": ("히어로",), "multiplier": 0.881803},
]

CALIBRATION_EVIDENCE_ROWS = (
    ("나이트로드", 5, 131999, 131999, 1391399575, 180111.392, 0.732874, 0.0, 5),
    ("나이트워커", 2, 131341, 131341, 1357517044, 172921.812, 0.75954, 0.0, 2),
    ("다크나이트", 1, 130134, 130134, 1270699326, 234812.413, 0.554204, 0.0, 1),
    ("데몬슬레이어", 11, 121197, 121197, 946949299, 112250.693, 1.079699, 0.0, 11),
    ("데몬어벤져", 1, 136354, 135885, 1646714570, 31380.298, 4.34521, 0.0, 1),
    ("듀얼블레이드", 2, 133613, 133613, 1706177196, 164130.634, 0.814065, 0.276, 2),
    ("라라", 2, 127031, 127031, 1105300982, 155132.893, 0.818853, 2.416, 2),
    ("레테", 1, 70361, 57349, 275743579, 86427.921, 0.8141, 0.39, 1),
    ("렌", 1, 138496, 138184, 1720232741, 175316.574, 0.789977, 0.0, 1),
    ("루미너스", 2, 128066, 128066, 1190280038, 152842.223, 0.837897, 1.173, 2),
    ("메르세데스", 2, 133102, 133078, 1472249674, 167037.938, 0.796837, 2.782, 2),
    ("메카닉", 6, 125241, 125241, 1072036514, 142743.022, 0.877388, 0.423, 6),
    ("미하일", 1, 126200, 126200, 1123739065, 152234.285, 0.828985, 0.0, 1),
    ("바이퍼", 1, 133621, 133621, 1478917620, 207778.543, 0.643093, 0.644, 1),
    ("배틀메이지", 2, 127524, 127524, 1202992951, 149281.869, 0.85425, 0.0, 2),
    ("보우마스터", 4, 127319, 127319, 1158092416, 191295.196, 0.665563, 0.0, 4),
    ("블래스터", 1, 128209, 128209, 1180785174, 164330.134, 0.780192, 0.0, 1),
    ("비숍", 3, 133264, 133264, 1482328105, 232478.457, 0.573232, 0.0, 3),
    ("섀도어", 2, 135640, 135640, 1641292039, 243089.538, 0.557984, 0.0, 2),
    ("소울마스터", 4, 128247, 128247, 1214720139, 144196.499, 0.889391, 2.644, 4),
    ("스트라이커", 4, 126446, 126446, 1120645864, 145704.49, 0.867825, 0.0, 4),
    ("신궁", 1, 129101, 129101, 1249633946, 163540.207, 0.789414, 1.267, 1),
    ("아델", 1, 147144, 147144, 2126416856, 226996.104, 0.648223, 1.422, 1),
    ("아란", 2, 130083, 130083, 1317095102, 148210.022, 0.877694, 0.0, 2),
    ("아크", 1, 132258, 132258, 1400979775, 155490.015, 0.850588, 0.0, 1),
    ("아크메이지(불,독)", 4, 131808, 131808, 1368145883, 215230.282, 0.612405, 0.39, 4),
    ("아크메이지(썬,콜)", 1, 135522, 135522, 1569260815, 270086.24, 0.501773, 0.0, 1),
    ("에반", 1, 131901, 131901, 1425616786, 164291.863, 0.802846, 0.0, 1),
    ("엔젤릭버스터", 1, 133644, 133644, 1509013408, 166064.209, 0.804773, 0.0, 1),
    ("와일드헌터", 1, 127421, 127421, 1131897067, 175969.849, 0.724107, 0.0, 1),
    ("윈드브레이커", 1, 140606, 140606, 1818744322, 202732.048, 0.693556, 0.145, 1),
    ("은월", 1, 135437, 135437, 1518292263, 219733.477, 0.616369, 0.447, 1),
    ("일리움", 1, 135800, 135800, 1564279074, 193425.966, 0.702077, 0.956, 1),
    ("제논", 1, 135963, 135963, 1658373525, 123873.528, 1.097595, 0.0, 1),
    ("제로", 1, 131708, 131708, 1281745434, 140160.716, 0.939693, 0.0, 1),
    ("카데나", 1, 133939, 133939, 1515466805, 130686.694, 1.024886, 0.0, 1),
    ("카이저", 1, 134516, 134516, 1466955942, 145844.977, 0.922322, 0.0, 1),
    ("카인", 10, 123849, 123849, 1069098463, 186100.97, 0.665494, 0.0, 10),
    ("칼리", 2, 128407, 128407, 1171359771, 167003.846, 0.768886, 0.0, 2),
    ("캐논슈터", 3, 135072, 135072, 1520656491, 174157.54, 0.775574, 0.006, 3),
    ("캡틴", 1, 131120, 131120, 1318349697, 160839.531, 0.815222, 0.0, 1),
    ("키네시스", 1, 132069, 132069, 1375710633, 201008.366, 0.657032, 0.0, 1),
    ("팔라딘", 3, 131672, 131672, 1344352547, 163545.535, 0.805109, 0.0, 3),
    ("패스파인더", 1, 130749, 130749, 1296986736, 174718.629, 0.74834, 0.0, 1),
    ("팬텀", 2, 136176, 136176, 1560274714, 168599.234, 0.807691, 0.0, 2),
    ("플레임위자드", 1, 130082, 130082, 1262098601, 176068.721, 0.738814, 1.957, 1),
    ("호영", 1, 137623, 137623, 1706662020, 326740.296, 0.4212, 0.0, 1),
    ("히어로", 4, 130090, 130090, 1344672406, 147527.214, 0.881803, 0.0, 4),
)

CALIBRATION_EVIDENCE = {
    job: {
        "sampleRank": sample_rank,
        "originConverted": origin_converted,
        "originHexa": origin_hexa,
        "originCombatPower": origin_combat_power,
        "rawConverted": raw_converted,
        "multiplier": multiplier,
        "combatErrorPercent": combat_error_percent,
        "checkedCount": checked_count,
        "confidence": "high",
    }
    for (
        job,
        sample_rank,
        origin_converted,
        origin_hexa,
        origin_combat_power,
        raw_converted,
        multiplier,
        combat_error_percent,
        checked_count,
    ) in CALIBRATION_EVIDENCE_ROWS
}

COMBAT_CONVERTED_LOG_COEFFICIENTS = (
    -289.296670981936,
    42.84563887852173,
    -2.043242546031638,
    0.0326515722995472,
)
COMBAT_CONVERTED_JOB_FACTORS = [
    {"keywords": ("나이트로드", "나로"), "factor": 1.000000},
    {"keywords": ("나이트워커", "나워"), "factor": 0.999364},
    {"keywords": ("다크나이트", "닼나"), "factor": 1.007784},
    {"keywords": ("데몬슬레이어", "데슬"), "factor": 1.000657},
    {"keywords": ("듀얼블레이드", "듀블"), "factor": 0.968829},
    {"keywords": ("라라",), "factor": 1.012604},
    {"keywords": ("레테",), "factor": 0.845707},
    {"keywords": ("렌",), "factor": 0.999091},
    {"keywords": ("루미너스",), "factor": 1.006563},
    {"keywords": ("메르세데스",), "factor": 1.008429},
    {"keywords": ("메카닉",), "factor": 1.011004},
    {"keywords": ("미하일",), "factor": 1.003788},
    {"keywords": ("바이퍼",), "factor": 1.000166},
    {"keywords": ("배틀메이지", "배메"), "factor": 0.998542},
    {"keywords": ("보우마스터", "보마"), "factor": 1.005053},
    {"keywords": ("블래스터",), "factor": 0.996491},
    {"keywords": ("비숍",), "factor": 0.996929},
    {"keywords": ("섀도어",), "factor": 0.991981},
    {"keywords": ("소울마스터", "소마"), "factor": 1.000068},
    {"keywords": ("스트라이커",), "factor": 1.005243},
    {"keywords": ("신궁",), "factor": 1.004583},
    {"keywords": ("아델",), "factor": 1.004818},
    {"keywords": ("아란",), "factor": 1.000721},
    {"keywords": ("아크",), "factor": 1.011641},
    {"keywords": ("아크메이지(불,독)", "불독"), "factor": 1.003958},
    {"keywords": ("아크메이지(썬,콜)", "썬콜"), "factor": 0.997970},
    {"keywords": ("에반",), "factor": 0.993592},
    {"keywords": ("엔젤릭버스터", "엔버"), "factor": 1.004951},
    {"keywords": ("와일드헌터", "와헌"), "factor": 1.012764},
    {"keywords": ("윈드브레이커", "윈브"), "factor": 1.010677},
    {"keywords": ("은월",), "factor": 1.003569},
    {"keywords": ("일리움",), "factor": 1.008377},
    {"keywords": ("제로",), "factor": 1.013275},
    {"keywords": ("카데나",), "factor": 1.007739},
    {"keywords": ("카이저",), "factor": 1.017017},
    {"keywords": ("카인",), "factor": 1.012999},
    {"keywords": ("칼리",), "factor": 1.011210},
    {"keywords": ("캐논슈터", "캐논"), "factor": 1.002117},
    {"keywords": ("캡틴",), "factor": 1.003511},
    {"keywords": ("키네시스",), "factor": 1.003683},
    {"keywords": ("팔라딘",), "factor": 1.002168},
    {"keywords": ("패스파인더", "패파"), "factor": 1.015147},
    {"keywords": ("팬텀",), "factor": 1.008143},
    {"keywords": ("플레임위자드", "플위"), "factor": 1.007337},
    {"keywords": ("호영",), "factor": 1.006213},
    {"keywords": ("히어로",), "factor": 0.998370},
]
SPECIAL_COMBAT_CONVERTED_MODELS = [
    {
        "keywords": ("데몬어벤져", "데벤"),
        "model": "special_combat_curve_da",
        "coefficients": (10.952153605527894, 0.03872955282535175),
    },
    {
        "keywords": ("제논",),
        "model": "special_combat_curve_xenon",
        "coefficients": (11.138032201954397, 0.03041126015592686),
    },
]
COMBAT_CONVERTED_LEGACY_JOBS: tuple[str, ...] = ()
SPECIAL_DETAIL_HYBRID_MODELS = [
    {
        "keywords": ("데몬어벤져", "데벤"),
        "model": "job_special_detail_hybrid_da",
        "coefficients": (10.833193155636305, 0.016146702169708933, 0.03582054180791547),
    },
    {
        "keywords": ("제논",),
        "model": "job_special_detail_hybrid_xenon",
        "coefficients": (11.152313062228588, 0.023871647888818334, 0.015625817240356134),
    },
]


JOB_RULES = [
    {
        "keywords": (
            "히어로",
            "팔라딘",
            "다크나이트",
            "소울마스터",
            "미하일",
            "블래스터",
            "데몬슬레이어",
            "아란",
            "카이저",
            "아델",
            "제로",
            "바이퍼",
            "캐논",
            "스트라이커",
            "은월",
            "아크",
            "렌",
        ),
        "mainStat": "STR",
        "attackType": K_ATTACK,
    },
    {
        "keywords": (
            "보우마스터",
            "신궁",
            "패스파인더",
            "윈드브레이커",
            "와일드헌터",
            "메르세데스",
            "카인",
            "캡틴",
            "메카닉",
            "엔젤릭버스터",
        ),
        "mainStat": "DEX",
        "attackType": K_ATTACK,
    },
    {
        "keywords": (
            "아크메이지",
            "비숍",
            "플레임위자드",
            "배틀메이지",
            "에반",
            "루미너스",
            "일리움",
            "라라",
            "레테",
            "키네시스",
        ),
        "mainStat": "INT",
        "attackType": K_MAGIC,
    },
    {
        "keywords": (
            "나이트로드",
            "섀도어",
            "듀얼블레이드",
            "나이트워커",
            "팬텀",
            "카데나",
            "칼리",
            "호영",
        ),
        "mainStat": "LUK",
        "attackType": K_ATTACK,
    },
]

JOB_DETAIL_RULES = [
    {"keywords": ("나이트로드", "나로"), "mainStat": "LUK", "subStats": ("DEX",), "attackType": K_ATTACK, "weaponConstant": 1.75, "mastery": 0.86, "calibratedWeaponConstant": 1.75},
    {"keywords": ("나이트워커", "나워"), "mainStat": "LUK", "subStats": ("DEX",), "attackType": K_ATTACK, "weaponConstant": 1.75, "mastery": 0.86, "calibratedWeaponConstant": 1.75},
    {"keywords": ("다크나이트", "닼나"), "mainStat": "STR", "subStats": ("DEX",), "attackType": K_ATTACK, "weaponConstant": 1.49, "mastery": 0.91, "calibratedWeaponConstant": 1.49},
    {"keywords": ("데몬슬레이어", "데슬"), "mainStat": "STR", "subStats": ("DEX",), "attackType": K_ATTACK, "weaponConstant": 1.3, "mastery": 0.91, "calibratedWeaponConstant": 1.2},
    {"keywords": ("데몬어벤져", "데벤"), "mainStat": "STR", "subStats": ("DEX",), "attackType": K_ATTACK, "weaponConstant": 1.3, "mastery": 0.91, "statMode": "demon_avenger", "detailScale": 1.8950349828348878, "calibratedWeaponConstant": 1.3},
    {"keywords": ("듀얼블레이드", "듀블"), "mainStat": "LUK", "subStats": ("DEX", "STR"), "attackType": K_ATTACK, "weaponConstant": 1.3, "mastery": 0.91, "statMode": "dual_sub", "calibratedWeaponConstant": 1.3},
    {"keywords": ("라라",), "mainStat": "INT", "subStats": ("LUK",), "attackType": K_MAGIC, "weaponConstant": 1.5, "mastery": 0.96, "calibratedWeaponConstant": 1.2},
    {"keywords": ("레테",), "mainStat": "INT", "subStats": ("LUK",), "attackType": K_MAGIC, "weaponConstant": 1.3, "mastery": 0.96, "calibratedWeaponConstant": 1.3},
    {"keywords": ("렌",), "mainStat": "STR", "subStats": ("DEX",), "attackType": K_ATTACK, "weaponConstant": 1.3, "mastery": 0.91, "calibratedWeaponConstant": 1.3},
    {"keywords": ("루미너스",), "mainStat": "INT", "subStats": ("LUK",), "attackType": K_MAGIC, "weaponConstant": 1.2, "mastery": 0.96, "calibratedWeaponConstant": 1.2},
    {"keywords": ("메르세데스",), "mainStat": "DEX", "subStats": ("STR",), "attackType": K_ATTACK, "weaponConstant": 1.3, "mastery": 0.86, "calibratedWeaponConstant": 1.5},
    {"keywords": ("메카닉",), "mainStat": "DEX", "subStats": ("STR",), "attackType": K_ATTACK, "weaponConstant": 1.5, "mastery": 0.86, "calibratedWeaponConstant": 1.5},
    {"keywords": ("미하일",), "mainStat": "STR", "subStats": ("DEX",), "attackType": K_ATTACK, "weaponConstant": 1.2, "mastery": 0.91, "calibratedWeaponConstant": 1.2},
    {"keywords": ("바이퍼",), "mainStat": "STR", "subStats": ("DEX",), "attackType": K_ATTACK, "weaponConstant": 1.7, "mastery": 0.91, "calibratedWeaponConstant": 1.7},
    {"keywords": ("배틀메이지", "배메"), "mainStat": "INT", "subStats": ("LUK",), "attackType": K_MAGIC, "weaponConstant": 1.2, "mastery": 0.96, "calibratedWeaponConstant": 1.2},
    {"keywords": ("보우마스터", "보마"), "mainStat": "DEX", "subStats": ("STR",), "attackType": K_ATTACK, "weaponConstant": 1.3, "mastery": 0.86, "calibratedWeaponConstant": 1.3},
    {"keywords": ("블래스터",), "mainStat": "STR", "subStats": ("DEX",), "attackType": K_ATTACK, "weaponConstant": 1.7, "mastery": 0.91, "calibratedWeaponConstant": 1.5},
    {"keywords": ("비숍",), "mainStat": "INT", "subStats": ("LUK",), "attackType": K_MAGIC, "weaponConstant": 1.2, "mastery": 0.96, "calibratedWeaponConstant": 1.2},
    {"keywords": ("섀도어",), "mainStat": "LUK", "subStats": ("DEX",), "attackType": K_ATTACK, "weaponConstant": 1.3, "mastery": 0.91, "calibratedWeaponConstant": 1.3},
    {"keywords": ("소울마스터", "소마"), "mainStat": "STR", "subStats": ("DEX",), "attackType": K_ATTACK, "weaponConstant": 1.34, "mastery": 0.91, "calibratedWeaponConstant": 1.34},
    {"keywords": ("스트라이커",), "mainStat": "STR", "subStats": ("DEX",), "attackType": K_ATTACK, "weaponConstant": 1.7, "mastery": 0.91, "calibratedWeaponConstant": 1.7},
    {"keywords": ("신궁",), "mainStat": "DEX", "subStats": ("STR",), "attackType": K_ATTACK, "weaponConstant": 1.35, "mastery": 0.86, "calibratedWeaponConstant": 1.35},
    {"keywords": ("아델",), "mainStat": "STR", "subStats": ("DEX",), "attackType": K_ATTACK, "weaponConstant": 1.3, "mastery": 0.91, "calibratedWeaponConstant": 1.7},
    {"keywords": ("아란",), "mainStat": "STR", "subStats": ("DEX",), "attackType": K_ATTACK, "weaponConstant": 1.49, "mastery": 0.91, "calibratedWeaponConstant": 1.49},
    {"keywords": ("아크",), "mainStat": "STR", "subStats": ("DEX",), "attackType": K_ATTACK, "weaponConstant": 1.7, "mastery": 0.91, "calibratedWeaponConstant": 1.7},
    {"keywords": ("아크메이지(불,독)", "불독"), "mainStat": "INT", "subStats": ("LUK",), "attackType": K_MAGIC, "weaponConstant": 1.2, "mastery": 0.96, "calibratedWeaponConstant": 1.2},
    {"keywords": ("아크메이지(썬,콜)", "썬콜"), "mainStat": "INT", "subStats": ("LUK",), "attackType": K_MAGIC, "weaponConstant": 1.2, "mastery": 0.96, "calibratedWeaponConstant": 1.2},
    {"keywords": ("에반",), "mainStat": "INT", "subStats": ("LUK",), "attackType": K_MAGIC, "weaponConstant": 1.2, "mastery": 0.96, "calibratedWeaponConstant": 1.2},
    {"keywords": ("엔젤릭버스터", "엔버"), "mainStat": "DEX", "subStats": ("STR",), "attackType": K_ATTACK, "weaponConstant": 1.7, "mastery": 0.91, "calibratedWeaponConstant": 1.3},
    {"keywords": ("와일드헌터", "와헌"), "mainStat": "DEX", "subStats": ("STR",), "attackType": K_ATTACK, "weaponConstant": 1.35, "mastery": 0.86, "calibratedWeaponConstant": 1.35},
    {"keywords": ("윈드브레이커", "윈브"), "mainStat": "DEX", "subStats": ("STR",), "attackType": K_ATTACK, "weaponConstant": 1.3, "mastery": 0.86, "calibratedWeaponConstant": 1.3},
    {"keywords": ("은월",), "mainStat": "STR", "subStats": ("DEX",), "attackType": K_ATTACK, "weaponConstant": 1.7, "mastery": 0.91, "calibratedWeaponConstant": 1.7},
    {"keywords": ("일리움",), "mainStat": "INT", "subStats": ("LUK",), "attackType": K_MAGIC, "weaponConstant": 1.2, "mastery": 0.96, "calibratedWeaponConstant": 1.5},
    {"keywords": ("제논",), "mainStat": "LUK", "subStats": ("STR", "DEX"), "attackType": K_ATTACK, "weaponConstant": 1.5, "mastery": 0.91, "statMode": "xenon", "detailScale": 1.0626748183675614, "calibratedWeaponConstant": 1.5},
    {"keywords": ("제로",), "mainStat": "STR", "subStats": ("DEX",), "attackType": K_ATTACK, "weaponConstant": 1.49, "mastery": 0.91, "calibratedWeaponConstant": 1.3},
    {"keywords": ("카데나",), "mainStat": "LUK", "subStats": ("DEX",), "attackType": K_ATTACK, "weaponConstant": 1.3, "mastery": 0.91, "calibratedWeaponConstant": 1.3},
    {"keywords": ("카이저",), "mainStat": "STR", "subStats": ("DEX",), "attackType": K_ATTACK, "weaponConstant": 1.34, "mastery": 0.91, "calibratedWeaponConstant": 1.34},
    {"keywords": ("카인",), "mainStat": "DEX", "subStats": ("STR",), "attackType": K_ATTACK, "weaponConstant": 1.3, "mastery": 0.86, "calibratedWeaponConstant": 1.3},
    {"keywords": ("칼리",), "mainStat": "LUK", "subStats": ("DEX",), "attackType": K_ATTACK, "weaponConstant": 1.3, "mastery": 0.91, "calibratedWeaponConstant": 1.3},
    {"keywords": ("캐논슈터", "캐논"), "mainStat": "STR", "subStats": ("DEX",), "attackType": K_ATTACK, "weaponConstant": 1.5, "mastery": 0.86, "calibratedWeaponConstant": 1.5},
    {"keywords": ("캡틴",), "mainStat": "DEX", "subStats": ("STR",), "attackType": K_ATTACK, "weaponConstant": 1.5, "mastery": 0.86, "calibratedWeaponConstant": 1.5},
    {"keywords": ("키네시스",), "mainStat": "INT", "subStats": ("LUK",), "attackType": K_MAGIC, "weaponConstant": 1.2, "mastery": 0.96, "calibratedWeaponConstant": 1.2},
    {"keywords": ("팔라딘",), "mainStat": "STR", "subStats": ("DEX",), "attackType": K_ATTACK, "weaponConstant": 1.34, "mastery": 0.91, "calibratedWeaponConstant": 1.34},
    {"keywords": ("패스파인더", "패파"), "mainStat": "DEX", "subStats": ("STR",), "attackType": K_ATTACK, "weaponConstant": 1.3, "mastery": 0.86, "calibratedWeaponConstant": 1.3},
    {"keywords": ("팬텀",), "mainStat": "LUK", "subStats": ("DEX",), "attackType": K_ATTACK, "weaponConstant": 1.3, "mastery": 0.91, "calibratedWeaponConstant": 1.3},
    {"keywords": ("플레임위자드", "플위"), "mainStat": "INT", "subStats": ("LUK",), "attackType": K_MAGIC, "weaponConstant": 1.2, "mastery": 0.96, "calibratedWeaponConstant": 1.2},
    {"keywords": ("호영",), "mainStat": "LUK", "subStats": ("DEX",), "attackType": K_ATTACK, "weaponConstant": 1.3, "mastery": 0.91, "calibratedWeaponConstant": 1.3},
    {"keywords": ("히어로",), "mainStat": "STR", "subStats": ("DEX",), "attackType": K_ATTACK, "weaponConstant": 1.34, "mastery": 0.91, "calibratedWeaponConstant": 1.34},
]

KMS_JOB_NAMES = tuple(str(rule["keywords"][0]) for rule in JOB_DETAIL_RULES)

BOSS_RULES = [
    {"name": "\ud558\ub4dc \uc720\ud53c\ud14c\ub974", "party": 188000, "solo": 430000},
    {"name": "\ub178\ub9d0 \uc720\ud53c\ud14c\ub974", "party": 241000, "solo": 520000},
    {"name": "\ud558\ub4dc \ubc1c\ub4dc\ub9ad\uc2a4", "party": 89000, "solo": 170000},
    {"name": "\uc775\uc2a4\ud2b8\ub9bc \ub300\uc801\uc790", "party": 292000, "solo": 620000},
    {"name": "\ud558\ub4dc \ub9bc\ubcf4", "party": 293000, "solo": 600000},
    {"name": "\ub178\ub9d0 \ub9bc\ubcf4", "party": 247000, "solo": 480000},
    {"name": "\uc775\uc2a4\ud2b8\ub9bc \uce74\ub9c1", "party": 203000, "solo": 360000},
    {"name": "\uc775\uc2a4\ud2b8\ub9bc \uce7c\ub85c\uc2a4", "party": 193000, "solo": 340000},
    {"name": "\ud558\ub4dc \uce74\ub9c1", "party": 176000, "solo": 300000},
    {"name": "\uce74\uc624\uc2a4 \uce7c\ub85c\uc2a4", "party": 151000, "solo": 250000},
    {"name": "\ub178\ub9d0 \uce74\ub9c1", "party": 161000, "solo": 220000},
    {"name": "\ud558\ub4dc \uc138\ub80c", "party": 105000, "solo": 170000},
    {"name": "\uac80\uc740 \ub9c8\ubc95\uc0ac", "party": 84000, "solo": 145000},
    {"name": "\ud558\ub4dc \uc9c4\ud790\ub77c", "party": 68000, "solo": 116000},
    {"name": "\ud558\ub4dc \ub4c4\ucf08", "party": 65000, "solo": 110000},
    {"name": "\uce74\uc624\uc2a4 \ub354\uc2a4\ud06c", "party": 63000, "solo": 105000},
    {"name": "\ud558\ub4dc \uc70c", "party": 54000, "solo": 93000},
    {"name": "\ud558\ub4dc \ub8e8\uc2dc\ub4dc", "party": 52000, "solo": 90000},
    {"name": "\ud558\ub4dc \ub370\ubbf8\uc548", "party": 39000, "solo": 70000},
    {"name": "\ud558\ub4dc \uc2a4\uc6b0", "party": 38000, "solo": 68000},
]
BOSS_RULE_BASE_MINUTES = 30
BOSS_RULE_TARGET_MINUTES = 20
BOSS_RULE_DEFAULT_HP_RATIO = BOSS_RULE_TARGET_MINUTES / BOSS_RULE_BASE_MINUTES


def number(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace(",", "").replace("%", "").strip()
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return default
    try:
        result = float(match.group(0))
    except ValueError:
        return default
    if math.isnan(result) or math.isinf(result):
        return default
    return result


def int_number(value: Any, default: int = 0) -> int:
    return int(round(number(value, default)))


def empty_profile() -> dict[str, dict[str, float]]:
    return {
        "flat": {
            "STR": 0.0,
            "DEX": 0.0,
            "INT": 0.0,
            "LUK": 0.0,
            K_HP: 0.0,
            K_ATTACK: 0.0,
            K_MAGIC: 0.0,
        },
        "percent": {
            "STR": 0.0,
            "DEX": 0.0,
            "INT": 0.0,
            "LUK": 0.0,
            K_HP: 0.0,
            K_ATTACK: 0.0,
            K_MAGIC: 0.0,
        },
        "combat": {
            K_DAMAGE: 0.0,
            K_BOSS: 0.0,
            K_FINAL: 0.0,
            K_IED: 0.0,
            K_CRIT_RATE: 0.0,
            K_CRIT_DAMAGE: 0.0,
            K_ELEMENTAL: 0.0,
        },
    }


def add_to_profile(profile: dict[str, dict[str, float]], group: str, key: str, value: float) -> None:
    if key in profile[group]:
        profile[group][key] += value


def merge_profiles(*profiles: dict[str, dict[str, float]]) -> dict[str, dict[str, float]]:
    result = empty_profile()
    for profile in profiles:
        for group, values in profile.items():
            for key, value in values.items():
                add_to_profile(result, group, key, value)
    return result


def subtract_profiles(
    candidate: dict[str, dict[str, float]],
    active: dict[str, dict[str, float]],
) -> dict[str, dict[str, float]]:
    result = empty_profile()
    for group, values in result.items():
        for key in values:
            values[key] = candidate[group].get(key, 0.0) - active[group].get(key, 0.0)
    return result


def stat_map(stat_response: dict[str, Any]) -> dict[str, float]:
    result: dict[str, float] = {}
    for row in stat_response.get("final_stat") or []:
        name = row.get("stat_name")
        if name:
            result[str(name)] = number(row.get("stat_value"))
    return result


def value_from(mapping: dict[str, Any], key: str, default: float = 0.0) -> float:
    for alias in STAT_NAME_ALIASES.get(key, (key,)):
        if alias in mapping:
            return number(mapping.get(alias), default)
    return default


def option_number(options: dict[str, Any], key: str) -> float:
    for alias in OPTION_ALIASES.get(key, (key,)):
        if alias in options:
            return number(options.get(alias))
    return 0.0


def parse_option_line(profile: dict[str, dict[str, float]], line: str | None) -> None:
    if not line:
        return
    value = number(line)
    if value == 0:
        return

    is_percent = "%" in line
    if "\uc62c\uc2a4\ud0ef" in line or "\uc804\uccb4 \uc2a4\ud0ef" in line:
        for stat in STAT_KEYS:
            add_to_profile(profile, "percent" if is_percent else "flat", stat, value)
        return

    stat_words = {
        "STR": ("STR", "\ud798"),
        "DEX": ("DEX", "\ubbfc\ucca9\uc131"),
        "INT": ("INT", "\uc9c0\ub825"),
        "LUK": ("LUK", "\uc6b4"),
        K_HP: ("\ucd5c\ub300 HP", "Max HP", "MAX HP", "MHP", "HP"),
    }
    for key, words in stat_words.items():
        if any(word in line for word in words):
            add_to_profile(profile, "percent" if is_percent else "flat", key, value)
            return

    if "\uacf5\uaca9\ub825\uacfc \ub9c8\ub825" in line or "\uacf5\uaca9\ub825/\ub9c8\ub825" in line:
        group = "percent" if is_percent else "flat"
        add_to_profile(profile, group, K_ATTACK, value)
        add_to_profile(profile, group, K_MAGIC, value)
    elif K_ATTACK in line:
        add_to_profile(profile, "percent" if is_percent else "flat", K_ATTACK, value)
    elif K_MAGIC in line:
        add_to_profile(profile, "percent" if is_percent else "flat", K_MAGIC, value)
    elif "\ubcf4\uc2a4 \ubaac\uc2a4\ud130" in line:
        add_to_profile(profile, "combat", K_BOSS, value)
    elif K_CRIT_DAMAGE in line:
        add_to_profile(profile, "combat", K_CRIT_DAMAGE, value)
    elif K_CRIT_RATE in line:
        add_to_profile(profile, "combat", K_CRIT_RATE, value)
    elif K_IED in line:
        add_to_profile(profile, "combat", K_IED, value)
    elif K_FINAL in line:
        add_to_profile(profile, "combat", K_FINAL, value)
    elif K_DAMAGE in line and "\uc77c\ubc18 \ubaac\uc2a4\ud130" not in line:
        add_to_profile(profile, "combat", K_DAMAGE, value)


def equipment_profile(items: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    profile = empty_profile()
    for item in items:
        total = item.get("item_total_option") or {}
        for stat in STAT_KEYS:
            add_to_profile(profile, "flat", stat, option_number(total, stat))
        add_to_profile(profile, "flat", K_HP, option_number(total, K_HP))
        add_to_profile(profile, "percent", "STR", option_number(total, "\uc62c\uc2a4\ud0ef"))
        add_to_profile(profile, "percent", "DEX", option_number(total, "\uc62c\uc2a4\ud0ef"))
        add_to_profile(profile, "percent", "INT", option_number(total, "\uc62c\uc2a4\ud0ef"))
        add_to_profile(profile, "percent", "LUK", option_number(total, "\uc62c\uc2a4\ud0ef"))
        add_to_profile(profile, "flat", K_ATTACK, option_number(total, K_ATTACK))
        add_to_profile(profile, "flat", K_MAGIC, option_number(total, K_MAGIC))
        add_to_profile(profile, "combat", K_BOSS, option_number(total, K_BOSS))
        add_to_profile(profile, "combat", K_DAMAGE, option_number(total, K_DAMAGE))
        add_to_profile(profile, "combat", K_IED, option_number(total, "ignore_monster_armor"))

        for key in (
            "potential_option_1",
            "potential_option_2",
            "potential_option_3",
            "additional_potential_option_1",
            "additional_potential_option_2",
            "additional_potential_option_3",
        ):
            parse_option_line(profile, item.get(key))
    return profile


def ability_profile(ability_preset: dict[str, Any]) -> dict[str, dict[str, float]]:
    profile = empty_profile()
    for row in ability_preset.get("ability_info") or []:
        parse_option_line(profile, row.get("ability_value"))
    return profile


def hyper_profile(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    profile = empty_profile()
    for row in rows:
        parse_option_line(profile, row.get("stat_increase"))
    return profile


def apply_profile_delta(stats: dict[str, float], delta: dict[str, dict[str, float]]) -> dict[str, float]:
    adjusted = dict(stats)
    for stat in (*STAT_KEYS, K_HP):
        adjusted[stat] = max(
            0.0,
            value_from(adjusted, stat)
            + delta["flat"].get(stat, 0.0)
            + value_from(adjusted, stat)
            * delta["percent"].get(stat, 0.0)
            * STAT_PERCENT_EFFECT_RATIO
            / 100,
        )
    for attack_key in (K_ATTACK, K_MAGIC):
        adjusted[attack_key] = max(
            0.0,
            value_from(adjusted, attack_key)
            + delta["flat"].get(attack_key, 0.0)
            + value_from(adjusted, attack_key)
            * delta["percent"].get(attack_key, 0.0)
            * ATTACK_PERCENT_EFFECT_RATIO
            / 100,
        )
    for key, value in delta["combat"].items():
        if value:
            adjusted[key] = value_from(adjusted, key) + value
    adjusted[K_IED] = max(0.0, min(100.0, value_from(adjusted, K_IED)))
    adjusted[K_CRIT_RATE] = max(0.0, value_from(adjusted, K_CRIT_RATE))
    return adjusted


def stat_formula(base: float, percent: float = 0.0, static: float = 0.0) -> float:
    return base * (1 + percent / 100) + static


def stat_coefficient(stats: dict[str, float], key: str) -> dict[str, float]:
    base = value_from(stats, f"{key}_base", value_from(stats, key))
    percent = value_from(stats, f"{key}_percent", value_from(stats, f"{key}_multiplier"))
    static = value_from(stats, f"{key}_static")
    return {"base": base, "percent": percent, "static": static, "value": stat_formula(base, percent, static)}


def attack_coefficient(stats: dict[str, float], key: str) -> dict[str, float]:
    base = value_from(stats, key)
    percent = value_from(stats, f"{key}_percent", value_from(stats, f"{key}_multiplier"))
    return {"base": base, "percent": percent, "value": base * (1 + percent / 100)}


def job_rule(character_class: str | None) -> dict[str, Any] | None:
    text = str(character_class or "")
    best_rule = None
    best_length = 0
    for rule in JOB_RULES:
        for keyword in rule["keywords"]:
            if keyword in text and len(keyword) > best_length:
                best_rule = rule
                best_length = len(keyword)
    return best_rule


def job_detail_rule(character_class: str | None) -> dict[str, Any] | None:
    text = str(character_class or "")
    best_rule = None
    best_length = 0
    for rule in JOB_DETAIL_RULES:
        for keyword in rule["keywords"]:
            if keyword in text and len(keyword) > best_length:
                best_rule = rule
                best_length = len(keyword)
    return best_rule


def job_converted_multiplier(character_class: str | None) -> float:
    text = str(character_class or "")
    best = 1.0
    best_length = 0
    for row in JOB_CONVERTED_MULTIPLIERS:
        for keyword in row["keywords"]:
            if keyword in text and len(keyword) > best_length:
                best = float(row["multiplier"])
                best_length = len(keyword)
    return best


def job_calibration_evidence(character_class: str | None) -> dict[str, Any]:
    text = str(character_class or "")
    detail_rule = job_detail_rule(character_class)
    primary = primary_job_name(detail_rule, character_class)
    best_job = primary if primary in CALIBRATION_EVIDENCE else ""
    best_length = len(best_job)
    for job in CALIBRATION_EVIDENCE:
        if job in text and len(job) > best_length:
            best_job = job
            best_length = len(job)
    if not best_job:
        return {}

    evidence = dict(CALIBRATION_EVIDENCE[best_job])
    evidence["job"] = best_job
    estimated = float(evidence["rawConverted"]) * float(evidence["multiplier"])
    origin = float(evidence["originConverted"])
    evidence["estimatedConverted"] = round(estimated)
    evidence["sampleErrorPercent"] = round(abs(estimated - origin) / origin * 100, 4) if origin else 0.0
    return evidence


def combat_converted_job_factor(character_class: str | None) -> tuple[float, bool]:
    text = str(character_class or "")
    best = 1.0
    best_length = 0
    matched = False
    for row in COMBAT_CONVERTED_JOB_FACTORS:
        for keyword in row["keywords"]:
            if keyword in text and len(keyword) > best_length:
                best = float(row["factor"])
                best_length = len(keyword)
                matched = True
    return best, matched


def special_combat_converted_model(character_class: str | None) -> dict[str, Any] | None:
    text = str(character_class or "")
    best: dict[str, Any] | None = None
    best_length = 0
    for row in SPECIAL_COMBAT_CONVERTED_MODELS:
        for keyword in row["keywords"]:
            if keyword in text and len(keyword) > best_length:
                best = row
                best_length = len(keyword)
    return best


def special_detail_hybrid_model(character_class: str | None) -> dict[str, Any] | None:
    text = str(character_class or "")
    best: dict[str, Any] | None = None
    best_length = 0
    for row in SPECIAL_DETAIL_HYBRID_MODELS:
        for keyword in row["keywords"]:
            if keyword in text and len(keyword) > best_length:
                best = row
                best_length = len(keyword)
    return best


def uses_legacy_converted_model(character_class: str | None) -> bool:
    text = str(character_class or "")
    return any(keyword in text for keyword in COMBAT_CONVERTED_LEGACY_JOBS)


def table_matches_job(rows: list[dict[str, Any]], character_class: str | None) -> bool:
    text = str(character_class or "")
    return any(keyword in text for row in rows for keyword in row["keywords"])


def primary_job_name(rule: dict[str, Any] | None, fallback: str | None = None) -> str:
    if rule:
        return str(rule["keywords"][0])
    return str(fallback or "")


def calculation_coverage(character_class: str | None) -> dict[str, Any]:
    detail_missing = [job for job in KMS_JOB_NAMES if not job_detail_rule(job)]
    multiplier_missing = [job for job in KMS_JOB_NAMES if not table_matches_job(JOB_CONVERTED_MULTIPLIERS, job)]
    combat_missing = [
        job
        for job in KMS_JOB_NAMES
        if not (special_combat_converted_model(job) or table_matches_job(COMBAT_CONVERTED_JOB_FACTORS, job))
    ]
    detail_rule = job_detail_rule(character_class)
    basic_rule = job_rule(character_class)
    special_detail = special_detail_hybrid_model(character_class)
    special_combat = special_combat_converted_model(character_class)
    current_job = primary_job_name(detail_rule or basic_rule, character_class)
    rule_weapon_constant = float((detail_rule or {}).get("weaponConstant") or DEFAULT_WEAPON_CONSTANT)
    combat_job_factor, combat_job_matched = combat_converted_job_factor(character_class)
    calibration = job_calibration_evidence(character_class)
    return {
        "targetJobs": len(KMS_JOB_NAMES),
        "coveredDetailJobs": len(KMS_JOB_NAMES) - len(detail_missing),
        "coveredMultiplierJobs": len(KMS_JOB_NAMES) - len(multiplier_missing),
        "coveredCombatJobs": len(KMS_JOB_NAMES) - len(combat_missing),
        "missingDetailJobs": detail_missing,
        "missingMultiplierJobs": multiplier_missing,
        "missingCombatJobs": combat_missing,
        "current": {
            "inputClass": str(character_class or ""),
            "job": current_job,
            "detailRuleApplied": bool(detail_rule),
            "basicRuleApplied": bool(basic_rule),
            "mainStat": str((detail_rule or basic_rule or {}).get("mainStat") or ""),
            "attackType": str((detail_rule or basic_rule or {}).get("attackType") or ""),
            "statMode": str((detail_rule or {}).get("statMode") or "single"),
            "weaponConstant": rule_weapon_constant,
            "calibratedWeaponConstant": float((detail_rule or {}).get("calibratedWeaponConstant") or rule_weapon_constant),
            "mastery": float((detail_rule or {}).get("mastery") or DEFAULT_MASTERY),
            "jobConvertedMultiplier": job_converted_multiplier(character_class),
            "combatPowerJobFactor": combat_job_factor,
            "combatPowerJobFactorMatched": bool(combat_job_matched or special_combat),
            "calibrationConfidence": str(calibration.get("confidence") or ""),
            "calibrationEvidence": calibration,
            "specialDetailModel": str((special_detail or {}).get("model") or ""),
            "specialCombatModel": str((special_combat or {}).get("model") or ""),
        },
    }


def formula_diagnostics(
    coverage: dict[str, Any],
    converted: dict[str, Any],
    character_class: str | None,
) -> dict[str, Any]:
    current = coverage.get("current") or {}
    detail_matched = bool(current.get("detailRuleApplied"))
    multiplier_matched = table_matches_job(JOB_CONVERTED_MULTIPLIERS, character_class)
    combat_matched = bool(current.get("combatPowerJobFactorMatched"))
    evidence_matched = bool(current.get("calibrationEvidence"))
    missing_tables = []
    if not detail_matched:
        missing_tables.append("직업 상세식")
    if not multiplier_matched:
        missing_tables.append("환산 보정")
    if not combat_matched:
        missing_tables.append("전투력 모델")
    if not evidence_matched:
        missing_tables.append("보정 표본")

    if detail_matched and multiplier_matched and combat_matched and evidence_matched:
        status = "complete"
        message = "직업별 상세식, 환산 보정, 전투력 모델이 모두 적용되었습니다."
    elif detail_matched:
        status = "partial"
        message = "직업 상세식은 적용되었지만 일부 보정 표가 부족합니다."
    else:
        status = "fallback"
        message = "지원되지 않는 직업명입니다. 가장 높은 스탯과 일반 무기상수 기준으로 임시 계산했습니다."

    return {
        "status": status,
        "message": message,
        "inputClass": str(character_class or ""),
        "matchedJob": current.get("job") or "",
        "detailRuleApplied": detail_matched,
        "convertedMultiplierApplied": multiplier_matched,
        "combatModelApplied": combat_matched,
        "calibrationEvidenceApplied": evidence_matched,
        "missingTables": missing_tables,
        "knownJobCount": coverage.get("targetJobs") or 0,
        "knownJobsCovered": not (
            coverage.get("missingDetailJobs")
            or coverage.get("missingMultiplierJobs")
            or coverage.get("missingCombatJobs")
        ),
        "fallbackBasis": {
            "mainStat": converted.get("mainStat"),
            "attackType": converted.get("attackType"),
            "weaponConstant": converted.get("damageFormula", {}).get("weaponConstant"),
            "mastery": converted.get("damageFormula", {}).get("mastery"),
        },
    }


def primary_metric_confidence(
    formula_quality: dict[str, Any],
    api_quality: dict[str, Any],
    coverage: dict[str, Any],
) -> dict[str, Any]:
    score = 100.0
    reasons = []

    formula_status = str(formula_quality.get("status") or "")
    if formula_status == "fallback":
        score -= 45
        reasons.append("미지원 직업 공식으로 임시 계산 중입니다.")
    elif formula_status == "partial":
        score -= 20
        reasons.append("직업 공식의 일부 보정 표가 부족합니다.")

    if not formula_quality.get("knownJobsCovered"):
        score -= 15
        reasons.append("KMS 직업 테이블에 누락된 공식이 있습니다.")

    required_total = int_number(api_quality.get("requiredTotal"))
    required_present = int_number(api_quality.get("requiredPresent"))
    if required_present < required_total:
        score -= 35
        reasons.append("필수 Nexon API 데이터가 일부 누락되었습니다.")
    elif int_number(api_quality.get("warningCount")):
        penalty = min(20, int_number(api_quality.get("warningCount")) * 5)
        score -= penalty
        reasons.append("선택 Nexon API 조회 경고가 있습니다.")

    missing_optional_count = len(api_quality.get("missingOptionalSections") or [])
    if missing_optional_count:
        score -= min(10, missing_optional_count)
        reasons.append("선택 API 데이터 일부가 없어 보조 정보 정확도가 낮아질 수 있습니다.")

    current = coverage.get("current") or {}
    calibration = current.get("calibrationEvidence") or {}
    sample_error = float(calibration.get("sampleErrorPercent") or 0.0)
    if sample_error > 0.5:
        score -= min(15, sample_error)
        reasons.append(f"직업 보정 표본 오차가 {sample_error:.2f}%입니다.")

    score = max(0, min(100, round(score)))
    if score >= 90:
        level = "high"
        label = "높음"
    elif score >= 70:
        level = "medium"
        label = "보통"
    elif score >= 50:
        level = "low"
        label = "낮음"
    else:
        level = "critical"
        label = "주의"

    return {
        "score": score,
        "level": level,
        "label": label,
        "reasons": reasons or ["직업 공식과 필수 API 데이터가 정상 적용되었습니다."],
        "calibrationSampleErrorPercent": round(sample_error, 4),
    }


def combat_power_converted_score(stats: dict[str, float], character_class: str | None) -> dict[str, Any]:
    combat_power = exact_combat_power(stats)
    if combat_power <= 0:
        return {
            "applied": False,
            "combatPower": combat_power,
            "jobFactor": 1.0,
            "matched": False,
            "model": "legacy_damage_factor",
            "converted": 0.0,
        }

    special_model = special_combat_converted_model(character_class)
    if special_model:
        a0, a1 = special_model["coefficients"]
        converted = math.exp(a0 + a1 * math.log(combat_power))
        return {
            "applied": True,
            "combatPower": combat_power,
            "jobFactor": 1.0,
            "matched": True,
            "model": special_model["model"],
            "converted": converted,
        }

    factor, matched = combat_converted_job_factor(character_class)
    if uses_legacy_converted_model(character_class):
        return {
            "applied": False,
            "combatPower": combat_power,
            "jobFactor": factor,
            "matched": matched,
            "model": "legacy_damage_factor",
            "converted": 0.0,
        }

    x = math.log(combat_power)
    a0, a1, a2, a3 = COMBAT_CONVERTED_LOG_COEFFICIENTS
    converted = math.exp(a0 + a1 * x + a2 * x * x + a3 * x * x * x) * factor
    return {
        "applied": True,
        "combatPower": combat_power,
        "jobFactor": factor,
        "matched": matched,
        "model": "combat_power_curve" if matched else "combat_power_curve_generic",
        "converted": converted,
    }


def special_job_note(character_class: str | None) -> str:
    text = str(character_class or "")
    if "제논" in text:
        return "제논은 STR/DEX/LUK 복합 주스탯이라 현재 단일 주스탯 환산과 차이가 날 수 있습니다."
    if "데몬어벤져" in text:
        return "데몬어벤져는 HP 기반 직업이라 현재 일반 주스탯 환산과 차이가 날 수 있습니다."
    return ""


def choose_main_stat(stats: dict[str, float], character_class: str | None = None) -> str:
    detail_rule = job_detail_rule(character_class)
    if detail_rule:
        return str(detail_rule["mainStat"])
    rule = job_rule(character_class)
    if rule:
        return str(rule["mainStat"])
    return max(STAT_KEYS, key=lambda key: stat_coefficient(stats, key)["value"])


def choose_sub_stat(stats: dict[str, float], main_stat: str, character_class: str | None = None) -> str:
    detail_rule = job_detail_rule(character_class)
    if detail_rule:
        return " + ".join(str(stat) for stat in detail_rule.get("subStats", ()) if stat != main_stat) or "-"
    return max([key for key in STAT_KEYS if key != main_stat], key=lambda key: stat_coefficient(stats, key)["value"])


def choose_attack_type(stats: dict[str, float], character_class: str | None = None) -> str:
    detail_rule = job_detail_rule(character_class)
    if detail_rule:
        return str(detail_rule["attackType"])
    rule = job_rule(character_class)
    if rule:
        return str(rule["attackType"])
    attack = attack_coefficient(stats, K_ATTACK)["value"]
    magic = attack_coefficient(stats, K_MAGIC)["value"]
    return K_MAGIC if magic > attack else K_ATTACK


def main_weapon(item_response: dict[str, Any]) -> dict[str, Any]:
    for item in item_response.get("item_equipment") or []:
        if item.get("item_equipment_slot") == "\ubb34\uae30":
            return item
    return {}


def weapon_part(item_response: dict[str, Any]) -> str:
    weapon = main_weapon(item_response)
    return str(weapon.get("item_equipment_part") or weapon.get("item_name") or "")


def weapon_constant(item_response: dict[str, Any], character_class: str | None = None) -> float:
    part = weapon_part(item_response)
    for name, constant in WEAPON_CONSTANT_BY_PART.items():
        if name in part:
            return constant
    detail_rule = job_detail_rule(character_class)
    if detail_rule:
        return float(detail_rule.get("weaponConstant", DEFAULT_WEAPON_CONSTANT))
    return DEFAULT_WEAPON_CONSTANT


def mastery(item_response: dict[str, Any], character_class: str | None = None) -> float:
    part = weapon_part(item_response)
    for name, value in MASTERY_BY_PART.items():
        if name in part:
            return value
    detail_rule = job_detail_rule(character_class)
    if detail_rule:
        return float(detail_rule.get("mastery", DEFAULT_MASTERY))
    return DEFAULT_MASTERY


def base_stat_factor(
    stats: dict[str, float],
    character_class: str | None,
    main_key: str,
    sub_key: str,
) -> dict[str, Any]:
    detail_rule = job_detail_rule(character_class)
    mode = str((detail_rule or {}).get("statMode") or "single")
    coefficients = {key: stat_coefficient(stats, key) for key in STAT_KEYS}

    if mode == "xenon":
        weighted = sum(coefficients[key]["value"] for key in ("STR", "DEX", "LUK")) * 3.5
        return {
            "mode": mode,
            "main": coefficients[main_key],
            "sub": {key: coefficients[key] for key in ("STR", "DEX")},
            "weights": {"STR": 3.5, "DEX": 3.5, "LUK": 3.5},
            "baseStatFactor": weighted,
        }

    if mode == "demon_avenger":
        hp = value_from(stats, K_HP)
        weighted = hp / 3.5 + coefficients["STR"]["value"] * 4 + coefficients["DEX"]["value"]
        return {
            "mode": mode,
            "main": coefficients["STR"],
            "sub": {"DEX": coefficients["DEX"], K_HP: {"base": hp, "percent": 0.0, "static": 0.0, "value": hp}},
            "weights": {K_HP: 1 / 3.5, "STR": 4.0, "DEX": 1.0},
            "baseStatFactor": weighted,
        }

    sub_stats = tuple((detail_rule or {}).get("subStats") or (sub_key,))
    weighted = coefficients[main_key]["value"] * 4 + sum(
        coefficients[key]["value"] for key in sub_stats if key in coefficients and key != main_key
    )
    return {
        "mode": mode,
        "main": coefficients[main_key],
        "sub": {key: coefficients[key] for key in sub_stats if key in coefficients and key != main_key},
        "weights": {main_key: 4.0, **{key: 1.0 for key in sub_stats if key in coefficients and key != main_key}},
        "baseStatFactor": weighted,
    }


def detailed_scale_multiplier(character_class: str | None, weapon_const: float) -> float:
    detail_rule = job_detail_rule(character_class)
    if detail_rule and "detailScale" in detail_rule:
        return float(detail_rule["detailScale"])

    scale = job_converted_multiplier(character_class)
    calibrated_weapon_const = float((detail_rule or {}).get("calibratedWeaponConstant") or weapon_const or DEFAULT_WEAPON_CONSTANT)
    if weapon_const > 0 and calibrated_weapon_const > 0:
        scale *= math.sqrt(calibrated_weapon_const / weapon_const)
    return scale


def armor_factor(ignored_defence: float, armor: int = ARMOR) -> float:
    return max(0.0, 1 - 0.0001 * armor * (100 - ignored_defence))


def critical_factor(critical_damage: float, critical_rate: float) -> float:
    return 1 + (35 + critical_damage) * min(100, critical_rate) * 0.0001


def elemental_factor(elemental_resistance: float | None) -> float:
    if elemental_resistance is None:
        return 1.0
    return 0.5 * (1 + min(100, elemental_resistance) * 0.01)


def exact_combat_power(stats: dict[str, float]) -> int:
    return int_number(value_from(stats, K_COMBAT))


def converted_score(
    stats: dict[str, float],
    item_response: dict[str, Any],
    armor: int = ARMOR,
    character_class: str | None = None,
    use_combat_model: bool = False,
) -> dict[str, Any]:
    main_key = choose_main_stat(stats, character_class)
    sub_key = choose_sub_stat(stats, main_key, character_class)
    attack_key = choose_attack_type(stats, character_class)

    main = stat_coefficient(stats, main_key)
    sub = stat_coefficient(stats, sub_key) if sub_key in STAT_KEYS else {"base": 0.0, "percent": 0.0, "static": 0.0, "value": 0.0}
    attack = attack_coefficient(stats, attack_key)
    damage = value_from(stats, K_DAMAGE)
    boss_damage = value_from(stats, K_BOSS)
    final_damage = value_from(stats, K_FINAL)
    ignored = value_from(stats, K_IED)
    crit_rate = value_from(stats, K_CRIT_RATE)
    crit_damage = value_from(stats, K_CRIT_DAMAGE)
    elemental = value_from(stats, K_ELEMENTAL, default=-1)
    elemental = None if elemental < 0 else elemental

    base_stat = base_stat_factor(stats, character_class, main_key, sub_key)
    base_stat_factor_value = base_stat["baseStatFactor"]
    boss_damage_total = boss_damage + damage * REGULAR_DAMAGE_BOSS_WEIGHT
    general_damage_factor = (1 + boss_damage_total / 100) * (1 + final_damage / 100)
    defence_factor = armor_factor(ignored, armor)
    crit_factor = critical_factor(crit_damage, crit_rate)
    elem_factor = elemental_factor(elemental)
    weapon_const = weapon_constant(item_response, character_class)
    mastery_value = mastery(item_response, character_class)
    mastery_average = (1 + mastery_value) / 2
    damage_factor = (
        general_damage_factor
        * defence_factor
        * crit_factor
        * base_stat_factor_value
        * attack["value"]
        * elem_factor
        * weapon_const
        * 0.01
        * mastery_average
    )
    raw_converted_stat = math.sqrt(max(0.0, damage_factor)) * CONVERTED_STAT_SCALE
    job_multiplier = detailed_scale_multiplier(character_class, weapon_const)
    detailed_converted_stat = raw_converted_stat * job_multiplier
    combat_converted = combat_power_converted_score(stats, character_class)
    special_hybrid_model = special_detail_hybrid_model(character_class)
    special_hybrid_converted = 0.0
    special_hybrid_applied = False
    if special_hybrid_model and raw_converted_stat > 0 and exact_combat_power(stats) > 0:
        a0, a1, a2 = special_hybrid_model["coefficients"]
        special_hybrid_converted = math.exp(a0 + a1 * math.log(raw_converted_stat) + a2 * math.log(exact_combat_power(stats)))
        special_hybrid_applied = True

    if use_combat_model and combat_converted["applied"]:
        converted_stat = combat_converted["converted"]
        converted_model = combat_converted.get("model", "combat_power_curve")
    elif special_hybrid_applied:
        converted_stat = special_hybrid_converted
        converted_model = str(special_hybrid_model["model"])
    else:
        converted_stat = detailed_converted_stat
        converted_model = "job_detailed_damage_factor"

    return {
        "armor": armor,
        "mainStat": main_key,
        "subStat": sub_key,
        "attackType": attack_key,
        "jobRuleApplied": bool(job_detail_rule(character_class) or job_rule(character_class)),
        "jobDetailRuleApplied": bool(job_detail_rule(character_class)),
        "jobNote": special_job_note(character_class),
        "jobConvertedMultiplier": job_multiplier,
        "convertedModel": converted_model,
        "combatPowerConverted": combat_converted["converted"],
        "combatPowerJobFactor": combat_converted["jobFactor"],
        "specialHybridConverted": special_hybrid_converted,
        "legacyConverted": detailed_converted_stat,
        "detailedConverted": detailed_converted_stat,
        "rawConverted": raw_converted_stat,
        "baseStatFormula": {"main": main, "sub": sub, **base_stat},
        "attackFormula": attack,
        "damageFormula": {
            "damage": damage,
            "bossDamage": boss_damage,
            "bossDamageTotal": boss_damage_total,
            "regularDamageBossWeight": REGULAR_DAMAGE_BOSS_WEIGHT,
            "finalDamage": final_damage,
            "ignoredDefence": ignored,
            "criticalRate": crit_rate,
            "criticalDamage": crit_damage,
            "elementalResistance": elemental,
            "weaponConstant": weapon_const,
            "mastery": mastery_value,
            "masteryAverage": mastery_average,
            "generalDamageFactor": general_damage_factor,
            "armorFactor": defence_factor,
            "criticalFactor": crit_factor,
            "elementalFactor": elem_factor,
        },
        "baseStatFactor": base_stat_factor_value,
        "attack": attack["value"],
        "damageFactor": damage_factor,
        "armorFactor": defence_factor,
        "converted": converted_stat,
    }


def available_item_presets(item_response: dict[str, Any]) -> dict[int, list[dict[str, Any]]]:
    result = {}
    for idx in (1, 2, 3):
        items = item_response.get(f"item_equipment_preset_{idx}") or []
        if items:
            result[idx] = items
    active = int_number(item_response.get("preset_no"), 0)
    if active and active not in result and item_response.get("item_equipment"):
        result[active] = item_response.get("item_equipment") or []
    return result


def available_ability_presets(ability_response: dict[str, Any]) -> dict[int, dict[str, Any]]:
    result = {}
    for idx in (1, 2, 3):
        preset = ability_response.get(f"ability_preset_{idx}") or {}
        if preset.get("ability_info"):
            result[idx] = preset
    active = int_number(ability_response.get("preset_no"), 0)
    if active and active not in result:
        result[active] = {"ability_info": ability_response.get("ability_info") or []}
    return result


def available_hyper_presets(hyper_response: dict[str, Any]) -> dict[int, list[dict[str, Any]]]:
    result = {}
    for idx in (1, 2, 3):
        rows = hyper_response.get(f"hyper_stat_preset_{idx}") or []
        if rows:
            result[idx] = rows
    return result


def optimize_presets(
    raw: dict[str, Any],
    stats: dict[str, float],
    character_class: str | None = None,
    score_multiplier: float = 1.0,
    basis: str = "\ud658\uc0b0(380)",
) -> dict[str, Any]:
    item_response = raw.get("itemEquipment") or {}
    ability_response = raw.get("ability") or {}
    hyper_response = raw.get("hyperStat") or {}
    item_presets = available_item_presets(item_response)
    ability_presets = available_ability_presets(ability_response)
    hyper_presets = available_hyper_presets(hyper_response)

    active_item = int_number(item_response.get("preset_no"), 0) or next(iter(item_presets), 1)
    active_ability = int_number(ability_response.get("preset_no"), 0) or next(iter(ability_presets), 1)
    active_hyper = int_number(hyper_response.get("use_preset_no"), 0) or next(iter(hyper_presets), 1)

    active_profile = merge_profiles(
        equipment_profile(item_presets.get(active_item, item_response.get("item_equipment") or [])),
        ability_profile(ability_presets.get(active_ability, {"ability_info": ability_response.get("ability_info") or []})),
        hyper_profile(hyper_presets.get(active_hyper, [])),
    )

    candidates = []
    for item_no, items in item_presets.items():
        for ability_no, ability in ability_presets.items() or [(active_ability, {})]:
            for hyper_no, hyper in hyper_presets.items() or [(active_hyper, [])]:
                candidate_profile = merge_profiles(equipment_profile(items), ability_profile(ability), hyper_profile(hyper))
                adjusted_stats = apply_profile_delta(stats, subtract_profiles(candidate_profile, active_profile))
                item_payload = {"item_equipment": items}
                converted = converted_score(
                    adjusted_stats,
                    item_payload,
                    character_class=character_class,
                    use_combat_model=False,
                )
                unified_converted = converted["converted"] * score_multiplier
                candidates.append(
                    {
                        "itemPreset": item_no,
                        "abilityPreset": ability_no,
                        "hyperPreset": hyper_no,
                        "converted": round(unified_converted),
                        "rawConverted": round(converted["converted"]),
                        "damageFactor": round(converted["damageFactor"]),
                        "mainStat": converted["mainStat"],
                        "attackType": converted["attackType"],
                        "isCurrent": item_no == active_item and ability_no == active_ability and hyper_no == active_hyper,
                    }
                )

    candidates.sort(key=lambda row: row["converted"], reverse=True)
    current = next((row for row in candidates if row["isCurrent"]), candidates[0] if candidates else None)
    best = candidates[0] if candidates else None
    if current:
        for row in candidates:
            row["delta"] = row["converted"] - current["converted"]

    return {
        "active": {"itemPreset": active_item, "abilityPreset": active_ability, "hyperPreset": active_hyper},
        "basis": basis,
        "scoreMultiplier": round(score_multiplier, 6),
        "best": best,
        "current": current,
        "top": candidates[:9],
        "all": candidates,
        "candidateCount": len(candidates),
    }


def boss_time_adjustment(hp_ratio: float | None = None) -> float:
    ratio = BOSS_RULE_DEFAULT_HP_RATIO if hp_ratio is None else hp_ratio
    return math.sqrt(max(0.0, ratio) * BOSS_RULE_BASE_MINUTES / BOSS_RULE_TARGET_MINUTES)


def boss_status(
    converted: float,
    party_min: float,
    solo_min: float,
    hp_ratio: float | None = None,
) -> dict[str, Any]:
    adjustment = boss_time_adjustment(hp_ratio)
    base_party_min = party_min
    base_solo_min = solo_min
    party_min *= adjustment
    solo_min *= adjustment
    party_ratio = converted / party_min * 100 if party_min else 0
    solo_ratio = converted / solo_min * 100 if solo_min else 0
    party_gap = converted - party_min
    solo_gap = converted - solo_min
    if party_ratio < 100:
        label = "\ubd88\uac00\ub2a5"
        tone = "no"
        target_label = "\ud30c\ud2f0\ucef7"
        target_gap = party_gap
    elif solo_ratio < 80:
        label = "\ud30c\ud2f0\uac00\ub2a5"
        tone = "party"
        target_label = "\uc194\ud50c\ucef7"
        target_gap = solo_gap
    elif solo_ratio < 100:
        label = "\uc194\ud50c \ucd5c\uc18c\ucef7"
        tone = "near"
        target_label = "\uc194\ud50c\ucef7"
        target_gap = solo_gap
    elif solo_ratio < 160:
        label = "\uc194\ud50c \uac00\ub2a5"
        tone = "solo"
        target_label = "\uc194\ud50c\ucef7"
        target_gap = solo_gap
    else:
        label = "\uc194\ud50c \uc5ec\uc720"
        tone = "easy"
        target_label = "\uc194\ud50c\ucef7"
        target_gap = solo_gap

    if target_gap < 0:
        gap_label = f"{target_label}\uae4c\uc9c0 {abs(round(target_gap)):,} \ubd80\uc871"
    else:
        gap_label = f"{target_label}\ubcf4\ub2e4 {round(target_gap):,} \ucd08\uacfc"

    return {
        "status": label,
        "tone": tone,
        "currentConverted": round(converted),
        "partyRequired": round(party_min),
        "soloRequired": round(solo_min),
        "basePartyRequired": round(base_party_min),
        "baseSoloRequired": round(base_solo_min),
        "baseMinutes": BOSS_RULE_BASE_MINUTES,
        "targetMinutes": BOSS_RULE_TARGET_MINUTES,
        "hpRatio": round(BOSS_RULE_DEFAULT_HP_RATIO if hp_ratio is None else hp_ratio, 4),
        "timeAdjustment": round(adjustment, 4),
        "partyGap": round(party_gap),
        "soloGap": round(solo_gap),
        "partyRatio": round(party_ratio, 1),
        "soloRatio": round(solo_ratio, 1),
        "partyPossible": party_ratio >= 100,
        "soloPossible": solo_ratio >= 100,
        "gapLabel": gap_label,
    }


def build_boss_board(converted: float) -> list[dict[str, Any]]:
    result = []
    for boss in BOSS_RULES:
        status = boss_status(converted, boss["party"], boss["solo"], boss.get("hpRatio"))
        result.append({**boss, **status})
    return result


def build_calculation_audit(
    converted: dict[str, Any],
    hexa_converted: dict[str, Any],
    coverage: dict[str, Any],
    unified_converted: float,
    unified_multiplier: float,
) -> dict[str, Any]:
    current = coverage.get("current") or {}
    damage = converted.get("damageFormula") or {}
    base_stat = converted.get("baseStatFormula") or {}
    main = base_stat.get("main") or {}
    attack = converted.get("attackFormula") or {}
    stat_effect = hexa_converted.get("statEffect") or {}
    skill_effect = hexa_converted.get("skillEffect") or {}
    calibration = current.get("calibrationEvidence") or {}

    rows = [
        {
            "label": "대표 지표",
            "value": f"{round(unified_converted):,}",
            "detail": f"{hexa_converted.get('model') or 'hexa_adjusted'} · 배율 {unified_multiplier:.6f}",
        },
        {
            "label": "직업 상세식",
            "value": str(current.get("job") or "-"),
            "detail": f"{current.get('mainStat') or '-'} / {current.get('attackType') or '-'} · {current.get('statMode') or 'single'}",
        },
        {
            "label": "무기/숙련도",
            "value": f"{float(damage.get('weaponConstant') or 0):.2f} / {float(damage.get('mastery') or 0):.2f}",
            "detail": f"보정상수 {float(current.get('calibratedWeaponConstant') or 0):.2f} · 평균숙련 {float(damage.get('masteryAverage') or 0):.3f}",
        },
        {
            "label": "직업 샘플 배율",
            "value": f"{float(current.get('jobConvertedMultiplier') or 0):.6f}",
            "detail": f"원본 사이트 샘플 기준 · 전투력계수 {float(current.get('combatPowerJobFactor') or 0):.6f}",
        },
        {
            "label": "보정 표본",
            "value": str(calibration.get("confidence") or "unknown"),
            "detail": (
                f"{calibration.get('job') or '-'} rank {calibration.get('sampleRank') or '-'} · "
                f"원본 {int(calibration.get('originConverted') or 0):,} · "
                f"표본오차 {float(calibration.get('sampleErrorPercent') or 0):.4f}%"
            ),
        },
        {
            "label": "최종 상세 배율",
            "value": f"{float(converted.get('jobConvertedMultiplier') or 0):.6f}",
            "detail": f"직업 배율에 무기상수 보정 반영 · 모델 {converted.get('convertedModel') or '-'}",
        },
        {
            "label": "주스탯 공식",
            "value": f"{float(main.get('value') or 0):,.0f}",
            "detail": f"기본 {float(main.get('base') or 0):,.0f} · {float(main.get('percent') or 0):.1f}% · 미적용 {float(main.get('static') or 0):,.0f}",
        },
        {
            "label": "공격 공식",
            "value": f"{float(attack.get('value') or 0):,.0f}",
            "detail": f"기본 {float(attack.get('base') or 0):,.1f} · {float(attack.get('percent') or 0):.1f}%",
        },
        {
            "label": "방어/크리/속성",
            "value": f"{float(damage.get('armorFactor') or 0):.4f}",
            "detail": f"크리 {float(damage.get('criticalFactor') or 0):.4f} · 속성 {float(damage.get('elementalFactor') or 0):.4f}",
        },
        {
            "label": "HEXA 스킬",
            "value": f"Lv.{int(skill_effect.get('totalLevel') or 0)}",
            "detail": f"스킬효율 {float(skill_effect.get('effectRate') or 0) * 100:.2f}% · 완성도 {float(hexa_converted.get('completionRatio') or 0) * 100:.2f}%",
        },
        {
            "label": "HEXA 스탯",
            "value": f"{int(stat_effect.get('count') or 0)}개",
            "detail": (
                f"적용옵션 {len(stat_effect.get('details') or [])}개 · "
                f"스탯기여 +{float(hexa_converted.get('statConvertedGain') or 0):,.0f} · "
                f"HEXA보정차 {float(hexa_converted.get('gap') or 0):,.0f}"
            ),
        },
    ]
    return {
        "formula": "sqrt(damage_factor) * 4 * job_multiplier, then HEXA adjustment",
        "rows": rows,
        "damageFactor": round(float(converted.get("damageFactor") or 0), 4),
        "rawConverted": round(float(converted.get("rawConverted") or 0)),
        "detailedConverted": round(float(converted.get("detailedConverted") or 0)),
        "hexaConverted": round(float(hexa_converted.get("converted") or 0)),
        "unifiedConverted": round(unified_converted),
    }


def potential_lines(item: dict[str, Any], additional: bool = False) -> list[str]:
    prefix = "additional_potential_option" if additional else "potential_option"
    return [str(item.get(f"{prefix}_{idx}") or "") for idx in (1, 2, 3) if item.get(f"{prefix}_{idx}")]


def profile_from_lines(lines: list[str]) -> dict[str, dict[str, float]]:
    profile = empty_profile()
    for line in lines:
        parse_option_line(profile, line)
    return profile


def option_profile(options: dict[str, Any]) -> dict[str, dict[str, float]]:
    profile = empty_profile()
    for stat in (*STAT_KEYS, K_HP):
        add_to_profile(profile, "flat", stat, option_number(options, stat))
    add_to_profile(profile, "flat", K_ATTACK, option_number(options, K_ATTACK))
    add_to_profile(profile, "flat", K_MAGIC, option_number(options, K_MAGIC))
    all_stat = option_number(options, "\uc62c\uc2a4\ud0ef")
    for stat in STAT_KEYS:
        add_to_profile(profile, "percent", stat, all_stat)
    add_to_profile(profile, "combat", K_BOSS, option_number(options, K_BOSS))
    add_to_profile(profile, "combat", K_DAMAGE, option_number(options, K_DAMAGE))
    add_to_profile(profile, "combat", K_IED, option_number(options, "ignore_monster_armor"))
    return profile


def has_option_payload(options: dict[str, Any]) -> bool:
    return isinstance(options, dict) and any(value not in (None, "") for value in options.values())


def grade_target_percent(grade: str, weapon_like: bool = False) -> float:
    text = str(grade or "")
    if "\ub808\uc804\ub4dc\ub9ac" in text or "legendary" in text.lower():
        return 21.0 if weapon_like else 27.0
    if "\uc720\ub2c8\ud06c" in text or "unique" in text.lower():
        return 12.0 if weapon_like else 18.0
    if "\uc5d0\ud53d" in text or "epic" in text.lower():
        return 9.0
    return 9.0


def item_upgrade_stat_targets(character_class: str, main_stat: str) -> list[str]:
    detail_rule = job_detail_rule(character_class)
    mode = str((detail_rule or {}).get("statMode") or "single")
    if mode == "demon_avenger":
        return [K_HP]
    if mode == "xenon":
        return ["STR", "DEX", "LUK"]
    return [main_stat]


def target_label(targets: list[str]) -> str:
    if targets == ["STR", "DEX", "LUK"]:
        return "STR/DEX/LUK"
    return " / ".join(targets)


def starforce_target_bonus_label(targets: list[str]) -> str:
    if targets == [K_HP]:
        return f"{K_HP} +210"
    return f"{target_label(targets)} +7"


def source_target_flat(source: str, key: str, weapon_like: bool = False) -> float:
    if source == "flame":
        if key == K_HP:
            return 3500.0
        if key in (K_ATTACK, K_MAGIC):
            return 80.0 if weapon_like else 16.0
        return 110.0
    if source == "scroll":
        if key == K_HP:
            return 2500.0
        if key in (K_ATTACK, K_MAGIC):
            return 40.0 if weapon_like else 10.0
        return 70.0
    return 0.0


def source_profile_gap(
    profile: dict[str, dict[str, float]],
    source: str,
    keys: list[str],
    weapon_like: bool = False,
) -> tuple[float, float]:
    targets = [source_target_flat(source, key, weapon_like) for key in keys]
    currents = [profile["flat"].get(key, 0.0) for key in keys]
    gaps = [max(0.0, target - current) for target, current in zip(targets, currents)]
    if not gaps:
        return 0.0, 0.0
    return min(gaps), sum(targets) / len(targets)


def weakness_row(label: str, current: float, target: float, unit: str = "") -> dict[str, Any]:
    gap = max(0.0, target - current)
    score = gap / target * 100 if target else 0.0
    return {
        "label": label,
        "current": round(current, 2),
        "target": round(target, 2),
        "gap": round(gap, 2),
        "unit": unit,
        "score": round(score, 1),
    }


def item_weakness_breakdown(
    item: dict[str, Any],
    character_class: str,
    main_stat: str,
    attack_type: str,
) -> list[dict[str, Any]]:
    weapon_like = is_weapon_like_item(item)
    stat_targets = item_upgrade_stat_targets(character_class, main_stat)
    potential_profile = profile_from_lines(potential_lines(item))
    additional_profile = profile_from_lines(potential_lines(item, additional=True))
    flame_options = item.get("item_add_option") or {}
    scroll_options = item.get("item_etc_option") or {}
    flame_profile = option_profile(flame_options)
    scroll_profile = option_profile(scroll_options)
    weaknesses: list[dict[str, Any]] = []

    if weapon_like:
        target_attack_percent = grade_target_percent(str(item.get("potential_option_grade") or ""), True)
        current_attack_percent = potential_profile["percent"].get(attack_type, 0.0)
        weaknesses.append(weakness_row(f"잠재 {attack_type}%", current_attack_percent, target_attack_percent, "%"))
        if "엠블렘" not in str(item.get("item_equipment_slot") or ""):
            current_boss = potential_profile["combat"].get(K_BOSS, 0.0)
            weaknesses.append(weakness_row("잠재 보공", current_boss, 30.0, "%"))
        if has_option_payload(flame_options):
            flame_target = source_target_flat("flame", attack_type, True)
            weaknesses.append(weakness_row(f"추옵 {attack_type}", flame_profile["flat"].get(attack_type, 0.0), flame_target))
        if has_option_payload(scroll_options):
            scroll_target = source_target_flat("scroll", attack_type, True)
            weaknesses.append(weakness_row(f"작 {attack_type}", scroll_profile["flat"].get(attack_type, 0.0), scroll_target))
    else:
        target_stat_percent = grade_target_percent(str(item.get("potential_option_grade") or ""))
        current_stat_percent = min(potential_profile["percent"].get(key, 0.0) for key in stat_targets)
        weaknesses.append(weakness_row(f"잠재 {target_label(stat_targets)}%", current_stat_percent, target_stat_percent, "%"))
        if has_option_payload(flame_options):
            flame_gap, flame_target = source_profile_gap(flame_profile, "flame", stat_targets, False)
            weaknesses.append(weakness_row(f"추옵 {target_label(stat_targets)}", max(0.0, flame_target - flame_gap), flame_target))
        if has_option_payload(scroll_options):
            scroll_gap, scroll_target = source_profile_gap(scroll_profile, "scroll", stat_targets, False)
            weaknesses.append(weakness_row(f"작 {target_label(stat_targets)}", max(0.0, scroll_target - scroll_gap), scroll_target))

    current_add_attack = additional_profile["flat"].get(attack_type, 0.0)
    weaknesses.append(weakness_row(f"에디 {attack_type}", current_add_attack, 10.0))

    starforce = int_number(item.get("starforce"))
    if starforce:
        weaknesses.append(weakness_row("스타포스", starforce, 22.0, "성"))

    return sorted((row for row in weaknesses if row["gap"] > 0), key=lambda row: row["score"], reverse=True)


def is_weapon_like_item(item: dict[str, Any]) -> bool:
    text = " ".join(
        str(item.get(key) or "")
        for key in ("item_equipment_slot", "item_equipment_part", "item_name")
    )
    return any(keyword in text for keyword in ("\ubb34\uae30", "\ubcf4\uc870\ubb34\uae30", "\uc5e0\ube14\ub818"))


def item_upgrade_gain(
    stats: dict[str, float],
    item_response: dict[str, Any],
    character_class: str,
    current_converted: float,
    delta: dict[str, dict[str, float]],
    score_multiplier: float = 1.0,
) -> float:
    adjusted = apply_profile_delta(stats, delta)
    converted = converted_score(
        adjusted,
        item_response,
        character_class=character_class,
        use_combat_model=False,
    )
    return max(0.0, converted["converted"] * score_multiplier - current_converted)


def gain_scenario(
    stats: dict[str, float],
    item_response: dict[str, Any],
    character_class: str,
    current_converted: float,
    group: str,
    key: str,
    value: float,
    score_multiplier: float = 1.0,
) -> float:
    delta = empty_profile()
    add_to_profile(delta, group, key, value)
    return item_upgrade_gain(stats, item_response, character_class, current_converted, delta, score_multiplier)


def gain_multi_scenario(
    stats: dict[str, float],
    item_response: dict[str, Any],
    character_class: str,
    current_converted: float,
    group: str,
    keys: list[str],
    value: float,
    score_multiplier: float = 1.0,
) -> float:
    delta = empty_profile()
    for key in keys:
        add_to_profile(delta, group, key, value)
    return item_upgrade_gain(stats, item_response, character_class, current_converted, delta, score_multiplier)


def best_item_upgrade_scenarios(
    item: dict[str, Any],
    stats: dict[str, float],
    item_response: dict[str, Any],
    character_class: str,
    main_stat: str,
    attack_type: str,
    current_converted: float,
    score_multiplier: float = 1.0,
) -> list[dict[str, Any]]:
    scenarios: list[dict[str, Any]] = []
    weapon_like = is_weapon_like_item(item)
    potential_profile = profile_from_lines(potential_lines(item))
    additional_profile = profile_from_lines(potential_lines(item, additional=True))
    flame_options = item.get("item_add_option") or {}
    scroll_options = item.get("item_etc_option") or {}
    flame_profile = option_profile(flame_options)
    scroll_profile = option_profile(scroll_options)
    stat_targets = item_upgrade_stat_targets(character_class, main_stat)

    if weapon_like:
        target_attack_percent = grade_target_percent(str(item.get("potential_option_grade") or ""), True)
        current_attack_percent = potential_profile["percent"].get(attack_type, 0.0)
        attack_gap = min(12.0, max(0.0, target_attack_percent - current_attack_percent))
        if attack_gap > 0:
            gain = gain_scenario(stats, item_response, character_class, current_converted, "percent", attack_type, attack_gap, score_multiplier)
            scenarios.append(
                {
                    "type": "\uc7a0\uc7ac\uc635\uc158",
                    "action": f"{attack_type} {attack_gap:g}% \ubcf4\uac15",
                    "gain": gain,
                    "reason": "\ubb34\uae30\ub958 \uc7a0\uc7ac\uc758 \uacf5\ub9c8% \ubd80\uc871\ubd84",
                }
            )

        boss_gap = min(30.0, max(0.0, 30.0 - potential_profile["combat"].get(K_BOSS, 0.0)))
        if boss_gap > 0 and "\uc5e0\ube14\ub818" not in str(item.get("item_equipment_slot") or ""):
            gain = gain_scenario(stats, item_response, character_class, current_converted, "combat", K_BOSS, boss_gap, score_multiplier)
            scenarios.append(
                {
                    "type": "\uc7a0\uc7ac\uc635\uc158",
                    "action": f"\ubcf4\uacf5 {boss_gap:g}% \ubcf4\uac15",
                    "gain": gain,
                    "reason": "\ubb34\uae30/\ubcf4\uc870\ubb34\uae30 \ubcf4\uc2a4 \ud6a8\uc728 \ubd80\uc871\ubd84",
                }
            )

        flame_attack_gap, _ = source_profile_gap(flame_profile, "flame", [attack_type], True)
        if has_option_payload(flame_options) and flame_attack_gap > 0:
            value = min(20.0, flame_attack_gap)
            gain = gain_scenario(stats, item_response, character_class, current_converted, "flat", attack_type, value, score_multiplier)
            scenarios.append(
                {
                    "type": "\ucd94\uc635",
                    "action": f"{attack_type} +{value:g} \ubcf4\uac15",
                    "gain": gain,
                    "reason": "\ubb34\uae30 \ucd94\uac00\uc635\uc158 \uacf5\ub9c8 \ubd80\uc871\ubd84",
                }
            )

        scroll_attack_gap, _ = source_profile_gap(scroll_profile, "scroll", [attack_type], True)
        if has_option_payload(scroll_options) and scroll_attack_gap > 0:
            value = min(10.0, scroll_attack_gap)
            gain = gain_scenario(stats, item_response, character_class, current_converted, "flat", attack_type, value, score_multiplier)
            scenarios.append(
                {
                    "type": "\uc791/\uc8fc\ubb38\uc11c",
                    "action": f"{attack_type} +{value:g} \ubcf4\uac15",
                    "gain": gain,
                    "reason": "\ubb34\uae30 \uc791/\uc8fc\ubb38\uc11c \uacf5\ub9c8 \ubd80\uc871\ubd84",
                }
            )
    else:
        target_main_percent = grade_target_percent(str(item.get("potential_option_grade") or ""))
        current_main_percent = min(potential_profile["percent"].get(key, 0.0) for key in stat_targets)
        main_gap = min(12.0, max(0.0, target_main_percent - current_main_percent))
        if main_gap > 0:
            gain = gain_multi_scenario(
                stats,
                item_response,
                character_class,
                current_converted,
                "percent",
                stat_targets,
                main_gap,
                score_multiplier,
            )
            scenarios.append(
                {
                    "type": "\uc7a0\uc7ac\uc635\uc158",
                    "action": f"{target_label(stat_targets)} {main_gap:g}% \ubcf4\uac15",
                    "gain": gain,
                    "reason": "\uc9c1\uc5c5 \uae30\uc900 \uc7a5\ube44 \uc7a0\uc7ac% \ubd80\uc871\ubd84",
                }
            )

        flame_stat_gap, _ = source_profile_gap(flame_profile, "flame", stat_targets, False)
        if has_option_payload(flame_options) and flame_stat_gap > 0:
            value = min(25.0, flame_stat_gap)
            gain = gain_multi_scenario(
                stats,
                item_response,
                character_class,
                current_converted,
                "flat",
                stat_targets,
                value,
                score_multiplier,
            )
            scenarios.append(
                {
                    "type": "\ucd94\uc635",
                    "action": f"{target_label(stat_targets)} +{value:g} \ubcf4\uac15",
                    "gain": gain,
                    "reason": "\uc7a5\ube44 \ucd94\uac00\uc635\uc158 \uc8fc\uc694 \uc2a4\ud0ef \ubd80\uc871\ubd84",
                }
            )

        scroll_stat_gap, _ = source_profile_gap(scroll_profile, "scroll", stat_targets, False)
        if has_option_payload(scroll_options) and scroll_stat_gap > 0:
            value = min(15.0, scroll_stat_gap)
            gain = gain_multi_scenario(
                stats,
                item_response,
                character_class,
                current_converted,
                "flat",
                stat_targets,
                value,
                score_multiplier,
            )
            scenarios.append(
                {
                    "type": "\uc791/\uc8fc\ubb38\uc11c",
                    "action": f"{target_label(stat_targets)} +{value:g} \ubcf4\uac15",
                    "gain": gain,
                    "reason": "\uc7a5\ube44 \uc791/\uc8fc\ubb38\uc11c \uc8fc\uc694 \uc2a4\ud0ef \ubd80\uc871\ubd84",
                }
            )

    add_attack = additional_profile["flat"].get(attack_type, 0.0)
    add_attack_gap = min(10.0, max(0.0, 10.0 - add_attack))
    if add_attack_gap > 0:
        gain = gain_scenario(stats, item_response, character_class, current_converted, "flat", attack_type, add_attack_gap, score_multiplier)
        scenarios.append(
            {
                "type": "\uc5d0\ub514\uc154\ub110",
                "action": f"{attack_type} +{add_attack_gap:g} \ubcf4\uac15",
                "gain": gain,
                "reason": "\uc5d0\ub514\uc154\ub110 \uacf5\ub9c8 \uae30\uc900 \ubd80\uc871\ubd84",
            }
        )

    starforce = int_number(item.get("starforce"))
    if 0 < starforce < 22:
        delta = empty_profile()
        for key in stat_targets:
            add_to_profile(delta, "flat", key, 210.0 if key == K_HP else 7.0)
        add_to_profile(delta, "flat", attack_type, 2.0)
        gain = item_upgrade_gain(stats, item_response, character_class, current_converted, delta, score_multiplier)
        scenarios.append(
            {
                "type": "\uc2a4\ud0c0\ud3ec\uc2a4",
                "action": f"{starforce + 1}\uc131 \uc2dc\ub3c4",
                "gain": gain,
                "reason": f"1\uc131 \uc0c1\uc2b9 \uac00\uc815: {starforce_target_bonus_label(stat_targets)}, \uacf5\ub9c8 +2",
            }
        )

    return sorted(scenarios, key=lambda row: row["gain"], reverse=True)


def item_contribution(
    item: dict[str, Any],
    all_items: list[dict[str, Any]],
    stats: dict[str, float],
    character_class: str,
    current_converted: float,
    score_multiplier: float = 1.0,
) -> float:
    profile = equipment_profile([item])
    adjusted = apply_profile_delta(stats, subtract_profiles(empty_profile(), profile))
    remaining_items = [candidate for candidate in all_items if candidate is not item]
    item_payload = {"item_equipment": remaining_items or all_items}
    converted = converted_score(
        adjusted,
        item_payload,
        character_class=character_class,
        use_combat_model=False,
    )
    return max(0.0, current_converted - converted["converted"] * score_multiplier)


def build_upgrade_category_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    categories: dict[str, dict[str, Any]] = {}
    for row in rows:
        for scenario in row.get("scenarios") or []:
            gain = float(scenario.get("gain") or 0.0)
            if gain <= 0:
                continue
            label = str(scenario.get("type") or "기타")
            bucket = categories.setdefault(
                label,
                {
                    "type": label,
                    "totalGain": 0.0,
                    "candidateCount": 0,
                    "bestGain": 0.0,
                    "bestItem": "",
                    "bestAction": "",
                },
            )
            bucket["totalGain"] += gain
            bucket["candidateCount"] += 1
            if gain > bucket["bestGain"]:
                bucket["bestGain"] = gain
                bucket["bestItem"] = row.get("name") or "-"
                bucket["bestAction"] = scenario.get("action") or row.get("recommendedAction") or "-"

    total_gain = sum(row["totalGain"] for row in categories.values())
    result = []
    for row in categories.values():
        result.append(
            {
                "type": row["type"],
                "totalGain": round(row["totalGain"]),
                "sharePercent": round(row["totalGain"] / total_gain * 100, 1) if total_gain else 0.0,
                "candidateCount": row["candidateCount"],
                "bestGain": round(row["bestGain"]),
                "bestItem": row["bestItem"],
                "bestAction": row["bestAction"],
            }
        )
    return sorted(result, key=lambda row: (row["totalGain"], row["bestGain"]), reverse=True)


def build_upgrade_slot_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    slots: dict[str, dict[str, Any]] = {}
    for row in rows:
        gain = float(row.get("expectedGain") or 0.0)
        if gain <= 0:
            continue
        slot = str(row.get("slot") or row.get("part") or "기타")
        bucket = slots.setdefault(
            slot,
            {
                "slot": slot,
                "totalGain": 0.0,
                "candidateCount": 0,
                "bestGain": 0.0,
                "bestItem": "",
                "bestType": "",
                "bestAction": "",
                "topWeakness": "",
                "priorityScore": 0.0,
            },
        )
        bucket["totalGain"] += gain
        bucket["priorityScore"] += float(row.get("priorityScore") or 0.0)
        bucket["candidateCount"] += 1
        if gain > bucket["bestGain"]:
            bucket["bestGain"] = gain
            bucket["bestItem"] = row.get("name") or "-"
            bucket["bestType"] = row.get("recommendedType") or "-"
            bucket["bestAction"] = row.get("recommendedAction") or "-"
            weaknesses = row.get("weaknesses") or []
            bucket["topWeakness"] = weaknesses[0]["label"] if weaknesses else ""

    total_gain = sum(row["totalGain"] for row in slots.values())
    result = []
    for row in slots.values():
        result.append(
            {
                "slot": row["slot"],
                "totalGain": round(row["totalGain"]),
                "sharePercent": round(row["totalGain"] / total_gain * 100, 1) if total_gain else 0.0,
                "candidateCount": row["candidateCount"],
                "bestGain": round(row["bestGain"]),
                "bestItem": row["bestItem"],
                "bestType": row["bestType"],
                "bestAction": row["bestAction"],
                "topWeakness": row["topWeakness"],
                "priorityScore": round(row["priorityScore"]),
            }
        )
    return sorted(result, key=lambda row: (row["priorityScore"], row["totalGain"], row["bestGain"]), reverse=True)


def build_repair_checklist(rows: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    checklist = []
    for index, row in enumerate(rows[:limit], 1):
        scenario = (row.get("scenarios") or [{}])[0]
        weakness = (row.get("weaknesses") or [{}])[0]
        slot = str(row.get("slot") or row.get("part") or "-")
        item_name = str(row.get("name") or "-")
        action_type = str(scenario.get("type") or row.get("recommendedType") or "-")
        action = str(scenario.get("action") or row.get("recommendedAction") or "-")
        gain = int_number(scenario.get("gain"), int_number(row.get("expectedGain")))
        description = f"{slot} {item_name}: {action_type} - {action}"
        if weakness.get("label"):
            description += f" ({weakness['label']} 부족)"
        checklist.append(
            {
                "rank": index,
                "slot": slot,
                "item": item_name,
                "type": action_type,
                "action": action,
                "description": description,
                "reason": row.get("reason") or "",
                "expectedGain": gain,
                "expectedGainPercent": row.get("expectedGainPercent") or 0,
                "priorityScore": row.get("priorityScore") or 0,
                "weakness": weakness,
                "currentState": row.get("currentState") or "",
            }
        )
    return checklist


def build_upgrade_efficiency_profile(
    stats: dict[str, float],
    item_response: dict[str, Any],
    character_class: str,
    current_converted: float,
    main_stat: str,
    attack_type: str,
    stat_targets: list[str],
    score_multiplier: float = 1.0,
) -> list[dict[str, Any]]:
    stat_unit = 1000.0 if stat_targets == [K_HP] else 10.0
    entries = [
        {
            "type": "주스탯",
            "action": f"{target_label(stat_targets)} +{stat_unit:g}",
            "gain": gain_multi_scenario(
                stats,
                item_response,
                character_class,
                current_converted,
                "flat",
                stat_targets,
                stat_unit,
                score_multiplier,
            ),
            "unit": stat_unit,
        },
        {
            "type": "주스탯%",
            "action": f"{target_label(stat_targets)} +1%",
            "gain": gain_multi_scenario(
                stats,
                item_response,
                character_class,
                current_converted,
                "percent",
                stat_targets,
                1.0,
                score_multiplier,
            ),
            "unit": 1.0,
        },
        {
            "type": "공격 계수",
            "action": f"{attack_type} +1",
            "gain": gain_scenario(
                stats,
                item_response,
                character_class,
                current_converted,
                "flat",
                attack_type,
                1.0,
                score_multiplier,
            ),
            "unit": 1.0,
        },
        {
            "type": "공격%",
            "action": f"{attack_type} +1%",
            "gain": gain_scenario(
                stats,
                item_response,
                character_class,
                current_converted,
                "percent",
                attack_type,
                1.0,
                score_multiplier,
            ),
            "unit": 1.0,
        },
        {
            "type": "보스",
            "action": "보공 +1%",
            "gain": gain_scenario(
                stats,
                item_response,
                character_class,
                current_converted,
                "combat",
                K_BOSS,
                1.0,
                score_multiplier,
            ),
            "unit": 1.0,
        },
        {
            "type": "최종뎀",
            "action": "최종 데미지 +1%",
            "gain": gain_scenario(
                stats,
                item_response,
                character_class,
                current_converted,
                "combat",
                K_FINAL,
                1.0,
                score_multiplier,
            ),
            "unit": 1.0,
        },
    ]

    starforce_delta = empty_profile()
    for key in stat_targets:
        add_to_profile(starforce_delta, "flat", key, 210.0 if key == K_HP else 7.0)
    add_to_profile(starforce_delta, "flat", attack_type, 2.0)
    entries.append(
        {
            "type": "스타포스",
            "action": f"1성 기준: {starforce_target_bonus_label(stat_targets)}, {attack_type} +2",
            "gain": item_upgrade_gain(stats, item_response, character_class, current_converted, starforce_delta, score_multiplier),
            "unit": 1.0,
        }
    )

    result = []
    for entry in entries:
        gain = float(entry.get("gain") or 0.0)
        if gain <= 0:
            continue
        result.append(
            {
                "type": entry["type"],
                "action": entry["action"],
                "gain": round(gain),
                "gainPercent": round(gain / current_converted * 100, 3) if current_converted else 0.0,
                "unit": entry["unit"],
            }
        )
    return sorted(result, key=lambda row: row["gain"], reverse=True)


def build_item_upgrade_plan(
    stats: dict[str, float],
    item_response: dict[str, Any],
    converted: dict[str, Any],
    character_class: str,
    current_converted_override: float | None = None,
    score_multiplier: float = 1.0,
    basis: str = "\ud658\uc0b0(380)",
    top_limit: int = 8,
    include_all: bool = True,
) -> dict[str, Any]:
    items = item_response.get("item_equipment") or []
    current_converted = float(current_converted_override if current_converted_override is not None else converted.get("converted") or 0.0)
    main_stat = str(converted.get("mainStat") or choose_main_stat(stats, character_class))
    attack_type = str(converted.get("attackType") or choose_attack_type(stats, character_class))
    stat_targets = item_upgrade_stat_targets(character_class, main_stat)
    rows = []

    for item in items:
        scenarios = best_item_upgrade_scenarios(
            item,
            stats,
            item_response,
            character_class,
            main_stat,
            attack_type,
            current_converted,
            score_multiplier,
        )
        scenarios = [scenario for scenario in scenarios if scenario["gain"] > 0]
        if not scenarios:
            continue
        best = scenarios[0]
        contribution = item_contribution(item, items, stats, character_class, current_converted, score_multiplier)
        starforce = int_number(item.get("starforce"))
        grade = str(item.get("potential_option_grade") or "-")
        additional_grade = str(item.get("additional_potential_option_grade") or "-")
        potential_summary = " / ".join(potential_lines(item)) or "잠재 없음"
        additional_summary = " / ".join(potential_lines(item, additional=True)) or "에디 없음"
        weaknesses = item_weakness_breakdown(item, character_class, main_stat, attack_type)
        rows.append(
            {
                "slot": item.get("item_equipment_slot") or item.get("item_equipment_part") or "-",
                "part": item.get("item_equipment_part") or "-",
                "name": item.get("item_name") or "-",
                "icon": item.get("item_icon") or "",
                "starforce": starforce,
                "grade": grade,
                "additionalGrade": additional_grade,
                "currentState": f"{starforce}성 / 잠재 {grade} / 에디 {additional_grade}",
                "upgradeTargets": stat_targets,
                "potentialSummary": potential_summary,
                "additionalPotentialSummary": additional_summary,
                "weaknesses": weaknesses[:4],
                "recommendedType": best["type"],
                "recommendedAction": best["action"],
                "reason": best["reason"],
                "scoreBasis": basis,
                "expectedGain": round(best["gain"]),
                "expectedGainPercent": round(best["gain"] / current_converted * 100, 2) if current_converted else 0.0,
                "contribution": round(contribution),
                "priorityScore": round(best["gain"] + contribution * 0.05),
                "scenarios": [
                    {
                        "type": scenario["type"],
                        "action": scenario["action"],
                        "gain": round(scenario["gain"]),
                        "gainPercent": round(scenario["gain"] / current_converted * 100, 2) if current_converted else 0.0,
                        "reason": scenario.get("reason") or "",
                    }
                    for scenario in scenarios[:3]
                    if scenario["gain"] > 0
                ],
            }
        )

    rows.sort(key=lambda row: (row["priorityScore"], row["expectedGain"], -row["contribution"]), reverse=True)
    category_summary = build_upgrade_category_summary(rows)
    slot_summary = build_upgrade_slot_summary(rows)
    repair_checklist = build_repair_checklist(rows)
    efficiency_profile = build_upgrade_efficiency_profile(
        stats,
        item_response,
        character_class,
        current_converted,
        main_stat,
        attack_type,
        stat_targets,
        score_multiplier,
    )
    return {
        "basis": basis,
        "scoreMultiplier": round(score_multiplier, 6),
        "currentConverted": round(current_converted),
        "mainStat": main_stat,
        "attackType": attack_type,
        "upgradeTargets": stat_targets,
        "categorySummary": category_summary,
        "primaryCategory": category_summary[0] if category_summary else None,
        "efficiencyProfile": efficiency_profile,
        "primaryEfficiency": efficiency_profile[0] if efficiency_profile else None,
        "slotSummary": slot_summary,
        "primarySlot": slot_summary[0] if slot_summary else None,
        "repairFocus": {
            "slot": (slot_summary[0] or {}).get("slot") if slot_summary else "",
            "category": (category_summary[0] or {}).get("type") if category_summary else "",
            "expectedGain": (slot_summary[0] or {}).get("totalGain") if slot_summary else 0,
            "description": (repair_checklist[0] or {}).get("description") if repair_checklist else "",
        },
        "repairChecklist": repair_checklist,
        "method": "\uc7a5\ube44\ubcc4 \uac1c\uc120 \uc2dc\ub098\ub9ac\uc624\ub97c \ud658\uc0b0 \uc0c1\uc2b9\ub7c9\uc73c\ub85c \uc7ac\uacc4\uc0b0",
        "top": rows[:top_limit],
        "all": rows if include_all else [],
    }


def build_preset_upgrade_plans(
    raw: dict[str, Any],
    stats: dict[str, float],
    character_class: str,
    score_multiplier: float = 1.0,
    basis: str = "\ud658\uc0b0(380)",
) -> list[dict[str, Any]]:
    item_response = raw.get("itemEquipment") or {}
    ability_response = raw.get("ability") or {}
    hyper_response = raw.get("hyperStat") or {}
    item_presets = available_item_presets(item_response)
    ability_presets = available_ability_presets(ability_response)
    hyper_presets = available_hyper_presets(hyper_response)

    active_item = int_number(item_response.get("preset_no"), 0) or next(iter(item_presets), 1)
    active_ability = int_number(ability_response.get("preset_no"), 0) or next(iter(ability_presets), 1)
    active_hyper = int_number(hyper_response.get("use_preset_no"), 0) or next(iter(hyper_presets), 1)
    active_profile = merge_profiles(
        equipment_profile(item_presets.get(active_item, item_response.get("item_equipment") or [])),
        ability_profile(ability_presets.get(active_ability, {"ability_info": ability_response.get("ability_info") or []})),
        hyper_profile(hyper_presets.get(active_hyper, [])),
    )

    plans = []
    for item_no, items in item_presets.items():
        for ability_no, ability in ability_presets.items() or [(active_ability, {})]:
            for hyper_no, hyper in hyper_presets.items() or [(active_hyper, [])]:
                candidate_profile = merge_profiles(equipment_profile(items), ability_profile(ability), hyper_profile(hyper))
                adjusted_stats = apply_profile_delta(stats, subtract_profiles(candidate_profile, active_profile))
                item_payload = {"item_equipment": items}
                converted = converted_score(
                    adjusted_stats,
                    item_payload,
                    character_class=character_class,
                    use_combat_model=False,
                )
                converted_value = converted["converted"] * score_multiplier
                plan = build_item_upgrade_plan(
                    adjusted_stats,
                    item_payload,
                    converted,
                    character_class,
                    current_converted_override=converted_value,
                    score_multiplier=score_multiplier,
                    basis=basis,
                    top_limit=5,
                    include_all=False,
                )
                plan["presetSelection"] = {
                    "itemPreset": item_no,
                    "abilityPreset": ability_no,
                    "hyperPreset": hyper_no,
                    "isCurrent": item_no == active_item and ability_no == active_ability and hyper_no == active_hyper,
                }
                plans.append(
                    {
                        "itemPreset": item_no,
                        "abilityPreset": ability_no,
                        "hyperPreset": hyper_no,
                        "converted": round(converted_value),
                        "isCurrent": item_no == active_item and ability_no == active_ability and hyper_no == active_hyper,
                        "plan": plan,
                    }
                )

    plans.sort(key=lambda row: (not row["isCurrent"], row["itemPreset"], row["abilityPreset"], row["hyperPreset"]))
    return plans


def summarize_item(item: dict[str, Any], main_stat: str, attack_type: str) -> dict[str, Any]:
    total = item.get("item_total_option") or {}
    base = item.get("item_base_option") or {}
    potentials = [item.get("potential_option_1"), item.get("potential_option_2"), item.get("potential_option_3")]
    add_potentials = [
        item.get("additional_potential_option_1"),
        item.get("additional_potential_option_2"),
        item.get("additional_potential_option_3"),
    ]
    return {
        "slot": item.get("item_equipment_slot") or item.get("item_equipment_part") or "-",
        "part": item.get("item_equipment_part") or "-",
        "name": item.get("item_name") or "-",
        "icon": item.get("item_icon") or "",
        "description": item.get("item_description") or "",
        "starforce": int_number(item.get("starforce")),
        "scrollUpgrade": int_number(item.get("scroll_upgrade")),
        "grade": item.get("potential_option_grade") or "",
        "additionalGrade": item.get("additional_potential_option_grade") or "",
        "mainOption": int_number(option_number(total, main_stat)),
        "attackOption": int_number(option_number(total, attack_type)),
        "baseAttack": int_number(option_number(base, attack_type)),
        "bossDamage": option_number(total, K_BOSS),
        "damage": option_number(total, K_DAMAGE),
        "allStat": option_number(total, "\uc62c\uc2a4\ud0ef"),
        "potentials": [line for line in potentials if line],
        "additionalPotentials": [line for line in add_potentials if line],
    }


def summarize_items(item_response: dict[str, Any], main_stat: str, attack_type: str) -> dict[str, Any]:
    items = item_response.get("item_equipment") or []
    summarized = [summarize_item(item, main_stat, attack_type) for item in items]
    return {"items": summarized, "count": len(summarized), "starforceTotal": sum(item["starforce"] for item in summarized)}


def summarize_symbols(symbol_response: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "name": symbol.get("symbol_name") or "-",
            "icon": symbol.get("symbol_icon") or "",
            "level": int_number(symbol.get("symbol_level")),
            "growth": symbol.get("symbol_growth_count") or "",
        }
        for symbol in symbol_response.get("symbol") or []
    ]


def summarize_ability(ability_response: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"grade": str(row.get("ability_grade") or ""), "value": str(row.get("ability_value") or "")}
        for row in ability_response.get("ability_info") or []
    ]


def summarize_hyper_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        name = (
            row.get("stat_type")
            or row.get("stat_name")
            or row.get("hyper_stat_type")
            or row.get("hyper_stat_name")
            or "-"
        )
        result.append(
            {
                "name": str(name),
                "level": int_number(row.get("stat_level") or row.get("hyper_stat_level")),
                "point": int_number(row.get("stat_point") or row.get("hyper_stat_point")),
                "increase": str(row.get("stat_increase") or row.get("hyper_stat_increase") or ""),
            }
        )
    return result


def build_preset_views(
    raw: dict[str, Any],
    main_stat: str,
    attack_type: str,
    preset_optimization: dict[str, Any],
) -> dict[str, Any]:
    item_response = raw.get("itemEquipment") or {}
    ability_response = raw.get("ability") or {}
    hyper_response = raw.get("hyperStat") or {}
    active = preset_optimization.get("active") or {}

    item_presets = available_item_presets(item_response)
    ability_presets = available_ability_presets(ability_response)
    hyper_presets = available_hyper_presets(hyper_response)

    equipment = []
    for preset_no, items in sorted(item_presets.items()):
        summarized = summarize_items({"item_equipment": items}, main_stat, attack_type)
        equipment.append(
            {
                "no": preset_no,
                "active": preset_no == active.get("itemPreset"),
                "items": summarized["items"],
                "count": summarized["count"],
                "starforceTotal": summarized["starforceTotal"],
            }
        )

    ability = []
    for preset_no, preset in sorted(ability_presets.items()):
        rows = summarize_ability(preset)
        ability.append(
            {
                "no": preset_no,
                "active": preset_no == active.get("abilityPreset"),
                "abilities": rows,
                "count": len(rows),
            }
        )

    hyper = []
    for preset_no, rows in sorted(hyper_presets.items()):
        summarized = summarize_hyper_rows(rows)
        hyper.append(
            {
                "no": preset_no,
                "active": preset_no == active.get("hyperPreset"),
                "rows": summarized,
                "count": len(summarized),
            }
        )

    return {
        "active": active,
        "equipment": equipment,
        "ability": ability,
        "hyper": hyper,
        "combinations": preset_optimization.get("all") or [],
    }


def pick_list(payload: dict[str, Any], *keys: str) -> list[dict[str, Any]]:
    for key in keys:
        rows = payload.get(key)
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    return []


def hexa_main_multiplier(level: int) -> int:
    if level < 0:
        return 0
    if level >= len(HEXA_MAIN_LEVEL_MULTIPLIER):
        return HEXA_MAIN_LEVEL_MULTIPLIER[-1]
    return HEXA_MAIN_LEVEL_MULTIPLIER[level]


def hexa_stat_basis(core_name: str, main_stat: str, attack_type: str) -> tuple[str, str, float] | None:
    if not core_name:
        return None
    if "\uc8fc\ub825" in core_name:
        return "flat", main_stat, 100.0
    if "\uacf5\uaca9\ub825" in core_name and "\ub9c8\ub825" in core_name:
        return "flat", attack_type, 5.0
    if "\uacf5\uaca9\ub825" in core_name:
        return "flat", K_ATTACK, 5.0
    if "\ub9c8\ub825" in core_name:
        return "flat", K_MAGIC, 5.0
    if "\ud06c\ub9ac" in core_name:
        return "combat", K_CRIT_DAMAGE, 0.35
    if "\ubcf4\uc2a4" in core_name:
        return "combat", K_BOSS, 1.0
    if "\ubc29\uc5b4" in core_name or "\ubb34\uc2dc" in core_name:
        return "combat", K_IED, 1.0
    if "\ub370\ubbf8\uc9c0" in core_name:
        return "combat", K_DAMAGE, 0.75
    return None


def hexa_stat_profile(
    hexa_stat_response: dict[str, Any],
    main_stat: str,
    attack_type: str,
) -> dict[str, Any]:
    profile = empty_profile()
    details = []
    rows = (
        pick_list(hexa_stat_response, "character_hexa_stat_core")
        + pick_list(hexa_stat_response, "character_hexa_stat_core_2")
        + pick_list(hexa_stat_response, "character_hexa_stat_core_3")
    )

    for row in rows:
        entries = (
            ("main", row.get("main_stat_name"), int_number(row.get("main_stat_level")), True),
            ("sub1", row.get("sub_stat_name_1"), int_number(row.get("sub_stat_level_1")), False),
            ("sub2", row.get("sub_stat_name_2"), int_number(row.get("sub_stat_level_2")), False),
        )
        for slot, name, level, is_main in entries:
            basis = hexa_stat_basis(str(name or ""), main_stat, attack_type)
            if not basis or level <= 0:
                continue
            group, key, per_level = basis
            multiplier = hexa_main_multiplier(level) if is_main else level
            value = per_level * multiplier
            add_to_profile(profile, group, key, value)
            details.append(
                {
                    "slot": slot,
                    "name": name,
                    "level": level,
                    "target": key,
                    "value": value,
                }
            )

    return {"profile": profile, "details": details, "count": len(rows)}


def remove_hexa_profile(stats: dict[str, float], profile: dict[str, dict[str, float]]) -> dict[str, float]:
    adjusted = dict(stats)
    for key, value in profile["flat"].items():
        if not value:
            continue
        adjusted[key] = max(0.0, value_from(adjusted, key) - value)

    for key, value in profile["combat"].items():
        if not value:
            continue
        current = value_from(adjusted, key)
        if key == K_IED and 0 < value < 100:
            source = value / 100
            adjusted[key] = max(0.0, min(100.0, (1 - (1 - current / 100) / (1 - source)) * 100))
        else:
            adjusted[key] = max(0.0, current - value)
    return adjusted


def nested_level_candidates(value: Any) -> list[int]:
    if isinstance(value, dict):
        result = []
        for key, child in value.items():
            if "level" in str(key).lower():
                level = int_number(child)
                if level > 0:
                    result.append(level)
            result.extend(nested_level_candidates(child))
        return result
    if isinstance(value, list):
        result = []
        for child in value:
            result.extend(nested_level_candidates(child))
        return result
    return []


def row_level(row: dict[str, Any]) -> int:
    direct = (
        row.get("hexa_core_level")
        or row.get("skill_level")
        or row.get("core_level")
        or row.get("level")
    )
    level = int_number(direct)
    if level > 0:
        return level
    candidates = nested_level_candidates(row)
    return max(candidates, default=0)


def hexa_skill_level_summary(raw: dict[str, Any]) -> dict[str, Any]:
    rows = []
    rows.extend(pick_list(raw.get("hexamatrix") or {}, "character_hexa_core_equipment"))
    rows.extend(pick_list(raw.get("skill6") or {}, "character_skill"))

    levels_by_name: dict[str, int] = {}
    for index, row in enumerate(rows):
        name = (
            row.get("hexa_core_name")
            or row.get("skill_name")
            or row.get("core_name")
            or f"hexa-{index}"
        )
        level = row_level(row)
        if level <= 0:
            continue
        key = str(name)
        levels_by_name[key] = max(levels_by_name.get(key, 0), level)

    levels = list(levels_by_name.values())
    total_level = sum(levels)
    effect_rate = min(HEXA_SKILL_EFFECT_CAP, total_level * HEXA_SKILL_EFFECT_PER_LEVEL)
    return {
        "count": len(levels),
        "totalLevel": total_level,
        "maxLevel": max(levels, default=0),
        "effectRate": effect_rate,
        "levels": levels_by_name,
    }


def hexa_completion_ratio(total_level: int) -> float:
    if total_level <= 0:
        return 1.0
    completion = min(1.0, total_level / HEXA_COMPLETION_LEVEL_CAP)
    return HEXA_INCOMPLETE_BASE_RATIO + (1 - HEXA_INCOMPLETE_BASE_RATIO) * completion


def hexa_converted_score(
    raw: dict[str, Any],
    stats: dict[str, float],
    item_response: dict[str, Any],
    current: dict[str, Any],
    character_class: str | None = None,
) -> dict[str, Any]:
    stat_effect = hexa_stat_profile(
        raw.get("hexamatrixStat") or {},
        current["mainStat"],
        current["attackType"],
    )
    skill_effect = hexa_skill_level_summary(raw)
    stat_profile = stat_effect.get("profile") or empty_profile()
    stats_without_hexa = remove_hexa_profile(stats, stat_profile) if stat_effect.get("details") else dict(stats)
    without_hexa_stat = converted_score(
        stats_without_hexa,
        item_response,
        character_class=character_class,
        use_combat_model=False,
    )
    stat_gain = max(0.0, float(current["converted"] or 0.0) - float(without_hexa_stat["converted"] or 0.0))
    stat_gain_percent = stat_gain / float(without_hexa_stat["converted"]) * 100 if without_hexa_stat["converted"] else 0.0
    ratio = hexa_completion_ratio(skill_effect["totalLevel"])
    converted = current["converted"] * ratio
    converted = min(current["converted"], converted)
    return {
        "converted": converted,
        "completionRatio": ratio,
        "gap": current["converted"] - converted,
        "withoutHexaStatConverted": without_hexa_stat["converted"],
        "statConvertedGain": stat_gain,
        "statConvertedGainPercent": stat_gain_percent,
        "statEffect": stat_effect,
        "skillEffect": skill_effect,
    }


def summarize_pets(pet_response: dict[str, Any]) -> list[dict[str, Any]]:
    pets = []
    for index in (1, 2, 3):
        name = pet_response.get(f"pet_{index}_name") or pet_response.get(f"pet_{index}_nickname")
        equipment = pet_response.get(f"pet_{index}_equipment") or {}
        if name or equipment:
            pets.append(
                {
                    "name": name or "-",
                    "icon": pet_response.get(f"pet_{index}_icon") or "",
                    "equipment": equipment.get("item_name") if isinstance(equipment, dict) else "",
                }
            )
    return pets


def summarize_named_rows(rows: list[dict[str, Any]], name_keys: tuple[str, ...], icon_keys: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        name = next((row.get(key) for key in name_keys if row.get(key)), "")
        icon = next((row.get(key) for key in icon_keys if row.get(key)), "")
        level = row.get("skill_level") or row.get("v_core_level") or row.get("hexa_core_level")
        if name or icon:
            result.append({"name": name or "-", "icon": icon or "", "level": level})
    return result


def summarize_skills(raw: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for grade in ("5", "6"):
        payload = raw.get(f"skill{grade}") or {}
        for skill in pick_list(payload, "character_skill"):
            rows.append(
                {
                    "grade": grade,
                    "name": skill.get("skill_name") or "-",
                    "icon": skill.get("skill_icon") or "",
                    "level": skill.get("skill_level"),
                }
            )
    return rows


def summarize_other_stats(other_response: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not isinstance(other_response, dict):
        return rows

    for source, value in other_response.items():
        candidates = value if isinstance(value, list) else [value]
        for candidate in candidates:
            if isinstance(candidate, dict):
                name = (
                    candidate.get("stat_name")
                    or candidate.get("name")
                    or candidate.get("type")
                    or candidate.get("option_name")
                    or source
                )
                stat_value = (
                    candidate.get("stat_value")
                    or candidate.get("value")
                    or candidate.get("description")
                    or candidate.get("option_value")
                    or ""
                )
            elif candidate not in (None, "", [], {}):
                name = source
                stat_value = candidate
            else:
                continue

            rows.append({"name": str(name), "value": str(stat_value), "source": str(source)})
            if len(rows) >= 12:
                return rows

    return rows


def summarize_extra(raw: dict[str, Any]) -> dict[str, Any]:
    link_response = raw.get("linkSkill") or {}
    vmatrix_response = raw.get("vmatrix") or {}
    hexamatrix_response = raw.get("hexamatrix") or {}
    hexa_stat_response = raw.get("hexamatrixStat") or {}
    other_response = raw.get("otherStat") or {}
    exchange_ring = raw.get("ringExchangeSkillEquipment") or {}
    reserve_ring = raw.get("ringReserveSkillEquipment") or {}

    link_rows = pick_list(link_response, "character_link_skill", "character_owned_link_skill")
    v_rows = pick_list(vmatrix_response, "character_v_core_equipment")
    hexa_rows = pick_list(hexamatrix_response, "character_hexa_core_equipment")
    hexa_stat_rows = pick_list(
        hexa_stat_response,
        "character_hexa_stat_core",
        "character_hexa_stat_core_2",
        "character_hexa_stat_core_3",
    )

    rings = []
    for label, payload in (("링 익스체인지", exchange_ring), ("예비 특수 반지", reserve_ring)):
        name = (
            payload.get("item_name")
            or payload.get("ring_skill_equipment")
            or payload.get("ring_skill_item_name")
            or payload.get("special_ring_reserve_name")
            or payload.get("special_ring_exchange_name")
        )
        if isinstance(name, dict):
            name = name.get("item_name")
        if name:
            rings.append(
                {
                    "type": label,
                    "name": str(name),
                    "icon": payload.get("item_icon")
                    or payload.get("special_ring_reserve_icon")
                    or payload.get("special_ring_exchange_icon")
                    or "",
                }
            )

    skills = summarize_skills(raw)
    pets = summarize_pets(raw.get("petEquipment") or {})
    other_stats = summarize_other_stats(other_response)
    return {
        "pets": pets,
        "linkSkills": summarize_named_rows(link_rows, ("skill_name", "link_skill_name"), ("skill_icon",)),
        "skills": skills,
        "vCores": summarize_named_rows(v_rows, ("v_core_name",), ("v_core_icon",)),
        "hexaCores": summarize_named_rows(hexa_rows, ("hexa_core_name",), ("hexa_core_icon",)),
        "hexaStatCores": hexa_stat_rows,
        "otherStats": other_stats,
        "rings": rings,
        "counts": {
            "pets": len(pets),
            "linkSkills": len(link_rows),
            "skills": len(skills),
            "vCores": len(v_rows),
            "hexaCores": len(hexa_rows),
            "hexaStatCores": len(hexa_stat_rows),
            "otherStats": len(other_stats),
            "rings": len(rings),
        },
    }


def api_section_fetched(raw: dict[str, Any], key: str) -> bool:
    return key in raw and isinstance(raw.get(key), (dict, list))


def api_payload_count(value: Any) -> int:
    if isinstance(value, list):
        return sum(1 for row in value if row not in (None, "", {}, []))
    if isinstance(value, dict):
        total = 0
        for child in value.values():
            if isinstance(child, (dict, list)):
                total += api_payload_count(child)
            elif child not in (None, ""):
                total += 1
        return total
    return 1 if value not in (None, "") else 0


def api_section_has_payload(raw: dict[str, Any], key: str) -> bool:
    if not api_section_fetched(raw, key):
        return False
    return api_payload_count(raw.get(key)) > 0


def api_section_rows(raw: dict[str, Any], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    rows = []
    for key in keys:
        rows.append(
            {
                "key": key,
                "label": API_SECTION_LABELS.get(key, key),
                "fetched": api_section_fetched(raw, key),
                "hasData": api_section_has_payload(raw, key),
                "payloadCount": api_payload_count(raw.get(key)),
            }
        )
    return rows


def api_data_quality(raw: dict[str, Any]) -> dict[str, Any]:
    warnings = [row for row in raw.get("warnings") or [] if isinstance(row, dict)]
    warning_sections = {str(row.get("section") or "") for row in warnings}
    required_rows = api_section_rows(raw, API_REQUIRED_SECTIONS)
    optional_rows = api_section_rows(raw, API_OPTIONAL_SECTIONS)
    missing_required = [row for row in required_rows if not row["fetched"]]
    missing_optional = [row for row in optional_rows if not row["fetched"]]
    empty_optional = [row for row in optional_rows if row["fetched"] and not row["hasData"]]
    required_fetched = len(required_rows) - len(missing_required)
    optional_fetched = len(optional_rows) - len(missing_optional)
    total_sections = len(required_rows) + len(optional_rows)
    fetched_sections = required_fetched + optional_fetched

    item_response = raw.get("itemEquipment") or {}
    ability_response = raw.get("ability") or {}
    hyper_response = raw.get("hyperStat") or {}
    item_presets = available_item_presets(item_response)
    ability_presets = available_ability_presets(ability_response)
    hyper_presets = available_hyper_presets(hyper_response)
    item_preset_count = len(item_presets) or (1 if pick_list(item_response, "item_equipment") else 0)
    ability_preset_count = len(ability_presets) or (1 if pick_list(ability_response, "ability_info") else 0)

    if missing_required:
        status = "error"
    elif warnings:
        status = "warning"
    elif missing_optional:
        status = "partial"
    else:
        status = "complete"

    return {
        "status": status,
        "qualityPercent": round(fetched_sections / total_sections * 100, 1) if total_sections else 0,
        "requiredPresent": required_fetched,
        "requiredTotal": len(required_rows),
        "optionalPresent": optional_fetched,
        "optionalTotal": len(optional_rows),
        "required": required_rows,
        "optional": optional_rows,
        "presentSections": [row["key"] for row in required_rows + optional_rows if row["fetched"]],
        "missingRequiredSections": [row["key"] for row in missing_required],
        "missingOptionalSections": [row["key"] for row in missing_optional],
        "emptyOptionalSections": [row["key"] for row in empty_optional],
        "warningCount": len(warnings),
        "warningSections": sorted(section for section in warning_sections if section),
        "warnings": warnings[:8],
        "hexaAvailable": api_section_has_payload(raw, "hexamatrix") or api_section_has_payload(raw, "hexamatrixStat"),
        "presetSections": {
            "itemPresetCount": item_preset_count,
            "abilityPresetCount": ability_preset_count,
            "hyperPresetCount": len(hyper_presets),
        },
    }


def radar(stats: dict[str, float], converted: dict[str, Any]) -> dict[str, float]:
    formula = converted["damageFormula"]
    return {
        "stat": min(100, converted["baseStatFactor"] / 5000),
        "attack": min(100, converted["attack"] / 120),
        "damage": min(100, (formula["damage"] + formula["bossDamage"]) / 7),
        "critical": min(100, (formula["criticalDamage"] + 35) / 2),
        "ignore": min(100, formula["ignoredDefence"]),
        "final": min(100, formula["finalDamage"]),
    }


def build_view_model(raw: dict[str, Any]) -> dict[str, Any]:
    stats = stat_map(raw.get("stat") or {})
    item_response = raw.get("itemEquipment") or {}
    basic = raw.get("basic") or {}
    character_class = str(basic.get("character_class") or "")
    converted = converted_score(stats, item_response, character_class=character_class)
    hexa_converted = hexa_converted_score(raw, stats, item_response, converted, character_class=character_class)
    combat_power = exact_combat_power(stats)
    main_stat = converted["mainStat"]
    attack_type = converted["attackType"]
    items = summarize_items(item_response, main_stat, attack_type)
    unified_converted = float(hexa_converted["converted"])
    unified_multiplier = unified_converted / converted["converted"] if converted["converted"] else 1.0
    unified_basis = "\ud5e5\uc0ac\ud658\uc0b0(380)"
    item_upgrade_plan = build_item_upgrade_plan(
        stats,
        item_response,
        converted,
        character_class,
        current_converted_override=unified_converted,
        score_multiplier=unified_multiplier,
        basis=unified_basis,
    )
    preset_optimization = optimize_presets(
        raw,
        stats,
        character_class=character_class,
        score_multiplier=unified_multiplier,
        basis=unified_basis,
    )
    preset_upgrade_plans = build_preset_upgrade_plans(
        raw,
        stats,
        character_class,
        score_multiplier=unified_multiplier,
        basis=unified_basis,
    )
    preset_views = build_preset_views(raw, main_stat, attack_type, preset_optimization)
    boss_basis = round(unified_converted)
    best_preset = preset_optimization.get("best") or {}
    best_converted = best_preset.get("converted", boss_basis)
    boss_board = build_boss_board(boss_basis)
    coverage = calculation_coverage(character_class)
    formula_quality = formula_diagnostics(coverage, converted, character_class)
    calculation_audit = build_calculation_audit(
        converted,
        hexa_converted,
        coverage,
        unified_converted,
        unified_multiplier,
    )

    union = raw.get("union") or {}
    api_quality = api_data_quality(raw)
    confidence = primary_metric_confidence(formula_quality, api_quality, coverage)
    primary_metric = {
        "id": "unifiedConverted380",
        "label": "대표 환산(380)",
        "basis": unified_basis,
        "value": boss_basis,
        "rawValue": round(unified_converted, 2),
        "armor": ARMOR,
        "source": "hexaConverted380",
        "description": "보스 가능 여부, 아이템 개선 순서, 프리셋 비교에 공통으로 쓰는 단일 대표 지표입니다.",
        "status": "ready" if confidence["score"] >= 90 else "diagnostic",
        "confidence": confidence,
        "diagnostics": {
            "formulaStatus": formula_quality["status"],
            "apiStatus": api_quality["status"],
            "apiWarningCount": api_quality["warningCount"],
        },
        "usedBy": {
            "bossBoard": boss_basis,
            "itemUpgradePlan": item_upgrade_plan["currentConverted"],
            "presetOptimization": (preset_optimization.get("current") or {}).get("converted") or boss_basis,
        },
        "comparison": {
            "detailConverted380": round(converted["converted"]),
            "hexaConverted380": round(hexa_converted["converted"]),
            "legacyConverted380": round(converted["legacyConverted"]),
        },
    }
    return {
        "date": raw.get("date"),
        "basic": basic,
        "stats": stats,
        "primaryMetric": primary_metric,
        "summary": {
            "combatPower": combat_power,
            "converted380": round(converted["converted"]),
            "hexaConverted380": round(hexa_converted["converted"]),
            "unifiedConverted380": boss_basis,
            "unifiedBasis": unified_basis,
            "unifiedScoreMultiplier": round(unified_multiplier, 6),
            "hexaGap380": round(hexa_converted["gap"]),
            "hexaSkillTotalLevel": hexa_converted["skillEffect"]["totalLevel"],
            "hexaSkillEffectPercent": round(hexa_converted["skillEffect"]["effectRate"] * 100, 2),
            "hexaCompletionPercent": round(hexa_converted["completionRatio"] * 100, 2),
            "hexaStatCoreCount": hexa_converted["statEffect"]["count"],
            "hexaStatGain380": round(hexa_converted["statConvertedGain"]),
            "hexaStatGainPercent": round(hexa_converted["statConvertedGainPercent"], 2),
            "bossBasisConverted380": boss_basis,
            "bestConverted380": best_converted,
            "armorAdjustedCombatPower": round(combat_power * converted["armorFactor"]),
            "mainStat": main_stat,
            "subStat": converted["subStat"],
            "attackType": attack_type,
            "unionLevel": union.get("union_level"),
            "unionGrade": union.get("union_grade"),
            "equipmentCount": items["count"],
            "starforceTotal": items["starforceTotal"],
            "jobRuleApplied": converted["jobRuleApplied"],
            "jobConvertedMultiplier": converted["jobConvertedMultiplier"],
            "combatPowerJobFactor": converted["combatPowerJobFactor"],
            "convertedModel": converted["convertedModel"],
            "legacyConverted380": round(converted["legacyConverted"]),
            "jobNote": converted["jobNote"],
            "apiQualityPercent": api_quality["qualityPercent"],
            "apiWarningCount": api_quality["warningCount"],
            "formulaStatus": formula_quality["status"],
            "formulaMessage": formula_quality["message"],
        },
        "convertedDetail": converted,
        "hexaConvertedDetail": hexa_converted,
        "presetOptimization": preset_optimization,
        "presetViews": preset_views,
        "presetUpgradePlans": preset_upgrade_plans,
        "apiDataQuality": api_quality,
        "formulaDiagnostics": formula_quality,
        "calculationCoverage": coverage,
        "calculationAudit": calculation_audit,
        "itemUpgradePlan": item_upgrade_plan,
        "bossBoard": boss_board,
        "radar": radar(stats, converted),
        "equipment": items["items"],
        "symbols": summarize_symbols(raw.get("symbol") or {}),
        "ability": summarize_ability(raw.get("ability") or {}),
        "extra": summarize_extra(raw),
        "raw": raw,
    }
