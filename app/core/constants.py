"""
Constants for validation rules in Phase 3B tag expansion.

Contains validation matrices for category-dependent tags and team size rules.
"""

# Team size rules: (min, max) per category
# max=None means unlimited
TEAM_SIZE_RULES: dict[str, tuple[int, int | None]] = {
    "3s": (3, 5),
    "5s": (5, 8),
    "10s": (10, 15),
    "12s": (12, 20),
    "16s": (16, 21),
    "21s": (21, 30),
    "30s": (30, 50),
    "mass": (5, None),
}

# Weapon values (only valid for category="duel")
VALID_WEAPONS: list[str] = [
    "Longsword",
    "Polearm",
    "Sword & Shield",
    "Sword & Buckler",
    "Other",
]

# League values per category
VALID_LEAGUES: dict[str, list[str]] = {
    "duel": ["BI", "IMCF", "ACL", "ACW", "ACS", "HMB"],
    "profight": ["AMMA", "PWR", "BI", "IMCF", "ACL", "ACW", "ACS", "HMB", "Golden Ring"],
    "3s": ["IMCF", "ACS", "ACL", "ACW"],
    "5s": ["HMB", "IMCF", "ACL", "ACS", "BI", "ACW"],
    "10s": ["IMCF", "ACS", "ACL", "ACW"],
    "12s": ["BI", "HMB"],
    "16s": ["IMCF", "ACS", "ACL", "ACW"],
    "21s": ["HMB"],
    "30s": ["BI"],
    "mass": ["IMCF", "HMB", "BI"],
}

# Ruleset values per category
VALID_RULESETS: dict[str, list[str]] = {
    "duel": ["AMMA", "Outrance", "Championship Fights", "Knight Fight", "Other"],
    "profight": ["AMMA", "Outrance", "Championship Fights", "Knight Fight", "Other"],
    "3s": ["IMCF", "Other"],
    "5s": ["HMBIA", "BI", "IMCF", "Other"],
    "10s": ["IMCF", "Other"],
    "12s": ["BI", "Other"],
    "16s": ["IMCF", "Other"],
    "21s": ["HMBIA", "Other"],
    "30s": ["BI", "Other"],
    "mass": ["BI", "HMB", "IMCF", "Other"],
}
