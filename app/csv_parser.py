import csv
import io
import re
from typing import List, Dict, Any, Optional

def clean_str(val: Any) -> str:
    if val is None:
        return ""
    return str(val).strip()

def to_int(val: Any, default: int = 0) -> int:
    try:
        if val is None:
            return default
        # Remove commas or spaces if any
        s = str(val).replace(",", "").strip()
        return int(float(s))
    except (ValueError, TypeError):
        return default

def normalize_header(header: str) -> str:
    h = header.lower().strip()
    h = re.sub(r'[^a-z0-9]', '', h)
    return h

def parse_points_table_csv(csv_content: str) -> Dict[str, Any]:
    """
    Parses a Free Fire points table CSV and returns structured data
    with calculated rankings and tournament highlights.
    """
    # Remove BOM if present
    if csv_content.startswith('\ufeff'):
        csv_content = csv_content[1:]

    stream = io.StringIO(csv_content)
    # Sniff dialect or default to excel
    try:
        sample = csv_content[:1024]
        dialect = csv.Sniffer().sniff(sample)
    except Exception:
        dialect = csv.excel

    reader = csv.reader(stream, dialect=dialect)
    rows = [r for r in reader if any(field.strip() for field in r)]

    if not rows:
        raise ValueError("The uploaded CSV file is empty.")

    header_row = rows[0]
    data_rows = rows[1:]

    # Map headers to canonical keys
    col_map = {
        'rank': -1,
        'team': -1,
        'kills': -1,
        'placement': -1,
        'total': -1
    }

    for idx, raw_h in enumerate(header_row):
        norm = normalize_header(raw_h)
        if norm in ['rank', 'pos', 'position', 'no', '#', 'r']:
            col_map['rank'] = idx
        elif any(k in norm for k in ['team', 'player', 'squad', 'name', 'clan']):
            col_map['team'] = idx
        elif any(k in norm for k in ['kill', 'frags', 'eliminat']):
            col_map['kills'] = idx
        elif any(k in norm for k in ['place', 'pospoint', 'rankpoint', 'placementpoints']):
            col_map['placement'] = idx
        elif any(k in norm for k in ['total', 'points', 'pts', 'score', 'overall']):
            col_map['total'] = idx

    # Fallbacks if columns weren't identified
    total_cols = len(header_row)
    if col_map['rank'] == -1 and total_cols >= 1:
        col_map['rank'] = 0
    if col_map['team'] == -1 and total_cols >= 2:
        col_map['team'] = 1
    if col_map['kills'] == -1 and total_cols >= 3:
        col_map['kills'] = 2
    if col_map['placement'] == -1 and total_cols >= 4:
        col_map['placement'] = 3
    if col_map['total'] == -1 and total_cols >= 5:
        col_map['total'] = 4

    standings: List[Dict[str, Any]] = []

    for idx, r in enumerate(data_rows, start=1):
        def get_val(col_idx: int, default: str = "") -> str:
            if 0 <= col_idx < len(r):
                return r[col_idx].strip()
            return default

        raw_rank = get_val(col_map['rank'])
        team_str = get_val(col_map['team'], f"Team {idx}")
        kills = to_int(get_val(col_map['kills']), 0)
        placement = to_int(get_val(col_map['placement']), 0)
        
        # Calculate total points if missing or 0
        raw_total = get_val(col_map['total'])
        total_pts = to_int(raw_total, kills + placement)
        if total_pts == 0 and (kills > 0 or placement > 0):
            total_pts = kills + placement

        rank = to_int(raw_rank, idx)

        # Parse player tags if comma-separated
        players = []
        if ',' in team_str:
            players = [p.strip() for p in team_str.split(',') if p.strip()]
        elif team_str:
            players = [team_str]

        team_display_name = players[0] if len(players) == 1 else f"Team {idx}"
        # If players has multiple names, maybe first name or generic team title
        if len(players) > 1:
            team_display_name = f"Squad #{idx}"

        standings.append({
            "rank": rank,
            "team_raw": team_str,
            "team_name": team_display_name,
            "players": players,
            "kills": kills,
            "placement": placement,
            "total_points": total_pts
        })

    # Ensure rankings are properly sequential if rank wasn't reliable
    # Sort primarily by Total Points desc, then kills desc, placement desc
    standings.sort(key=lambda x: (x['total_points'], x['kills'], x['placement']), reverse=True)
    for i, item in enumerate(standings, start=1):
        item['rank'] = i

    # Calculate highlights
    total_match_kills = sum(s['kills'] for s in standings)
    max_kills_team = max(standings, key=lambda s: s['kills']) if standings else None
    booyah_team = standings[0] if standings else None

    return {
        "success": True,
        "count": len(standings),
        "standings": standings,
        "highlights": {
            "booyah": {
                "team": booyah_team['team_raw'] if booyah_team else "N/A",
                "points": booyah_team['total_points'] if booyah_team else 0,
                "kills": booyah_team['kills'] if booyah_team else 0
            } if booyah_team else None,
            "top_fragger": {
                "team": max_kills_team['team_raw'] if max_kills_team else "N/A",
                "kills": max_kills_team['kills'] if max_kills_team else 0
            } if max_kills_team else None,
            "total_kills": total_match_kills,
            "total_teams": len(standings)
        }
    }
