"""
Map raw CSV positions to the CD app 5-position schema.

The engine internally uses G/F/C for profile lookups (via normalize_position).
The CD app schema (players_schema.json) requires PG/SG/SF/PF/C.
"""

CD_POSITIONS = {"PG", "SG", "SF", "PF", "C"}

RAW_TO_CD = {
    "G":   "PG",
    "F":   "SF",
    "C":   "C",
    "G-F": "SG",
    "F-G": "SG",
    "F-C": "PF",
    "C-F": "PF",
}


def map_position_to_cd(raw_position: str) -> str:
    """
    Map a raw CSV position to the CD 5-position enum.

    Args:
        raw_position: Position from CSV data (G, F, C, G-F, etc.)

    Returns:
        CD position string (PG, SG, SF, PF, or C)
    """
    cd_pos = RAW_TO_CD.get(raw_position)
    if cd_pos is None:
        raise ValueError(
            f"Unknown position '{raw_position}'. "
            f"Expected one of: {sorted(RAW_TO_CD.keys())}"
        )
    return cd_pos
