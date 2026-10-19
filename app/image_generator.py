import os
import io
import re
from typing import List, Dict, Any
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(BASE_DIR, "static", "fonts")
IMG_DIR = os.path.join(BASE_DIR, "static", "images")

def get_font(name: str, size: int):
    path = os.path.join(FONT_DIR, name)
    if os.path.exists(path):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", size)
    except Exception:
        return ImageFont.load_default()

def sanitize_for_font(text: str) -> str:
    """Replaces complex unicode gaming symbols that standard TTF fonts can't render."""
    if not text:
        return ""
    # Map common gaming symbols
    replacements = {
        '⚡': '⚡', '♨': '*', '▲': '^', '▼': 'v', '♠': '*', '♣': '*', '♥': '*', '♦': '*',
        '×': 'x', '⁶⁹': '69', '⊙': 'o', '☘': '*', '★': '*', '☆': '*', '√': 'v',
        'ᴿᴰ': 'RD ', 'ᵀᴷ': 'TK ', '⚛': '*', 'ⓥ': '(V)', '•': '-'
    }
    cleaned = text
    for k, v in replacements.items():
        cleaned = cleaned.replace(k, v)
    
    # Filter out characters that might render as missing glyph boxes
    # Keep standard ascii + extended latin
    result = []
    for char in cleaned:
        if ord(char) < 256:
            result.append(char)
        else:
            result.append(" ")
    return re.sub(r'\s+', ' ', "".join(result)).strip()

THEME_CONFIGS = {
    "inferno": {
        "primary": (255, 106, 0),       # Neon Orange
        "secondary": (255, 183, 3),     # Fire Gold
        "accent": (255, 42, 0),         # Red Orange
        "highlight": (255, 235, 130),   # Bright Gold
        "card_bg": (12, 15, 22, 245),
        "row_odd": (18, 22, 32, 240),
        "row_even": (14, 17, 26, 240),
        "rank1_glow": (255, 183, 3, 90),
        "rank1_border": (255, 195, 0),
        "header_bg": (32, 20, 14, 250),
    },
    "chrono": {
        "primary": (0, 242, 254),       # Cyan
        "secondary": (157, 0, 255),     # Purple
        "accent": (0, 119, 254),
        "highlight": (180, 245, 255),
        "card_bg": (10, 14, 24, 245),
        "row_odd": (16, 24, 38, 240),
        "row_even": (12, 18, 30, 240),
        "rank1_glow": (0, 242, 254, 90),
        "rank1_border": (0, 242, 254),
        "header_bg": (14, 22, 38, 250),
    },
    "crimson": {
        "primary": (255, 0, 85),        # Crimson
        "secondary": (255, 85, 0),      # Lava
        "accent": (179, 0, 59),
        "highlight": (255, 190, 200),
        "card_bg": (16, 11, 15, 245),
        "row_odd": (28, 16, 22, 240),
        "row_even": (20, 12, 16, 240),
        "rank1_glow": (255, 0, 85, 90),
        "rank1_border": (255, 0, 85),
        "header_bg": (36, 14, 20, 250),
    },
    "gold": {
        "primary": (255, 215, 0),       # Pure Gold
        "secondary": (255, 153, 0),     # Amber
        "accent": (212, 175, 55),
        "highlight": (255, 250, 210),
        "card_bg": (16, 14, 10, 245),
        "row_odd": (26, 23, 16, 240),
        "row_even": (18, 16, 11, 240),
        "rank1_glow": (255, 215, 0, 95),
        "rank1_border": (255, 215, 0),
        "header_bg": (34, 28, 14, 250),
    }
}

def generate_points_table_image(
    standings: List[Dict[str, Any]],
    tournament_title: str = "FREE FIRE BATTLEGROUNDS CHAMPIONSHIP",
    match_info: str = "GRAND FINALS • MATCH 01 • BERMUDA",
    theme_name: str = "inferno",
    width: int = 1920,
    height: int = 1080
) -> io.BytesIO:
    theme = THEME_CONFIGS.get(theme_name.lower(), THEME_CONFIGS["inferno"])

    # Base background
    bg_path = os.path.join(IMG_DIR, "freefire_esports_bg.jpg")
    if os.path.exists(bg_path):
        try:
            base_img = Image.open(bg_path).convert("RGBA")
            base_img = base_img.resize((width, height), Image.Resampling.LANCZOS)
        except Exception:
            base_img = Image.new("RGBA", (width, height), (7, 9, 14, 255))
    else:
        base_img = Image.new("RGBA", (width, height), (7, 9, 14, 255))

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    
    # Dark vignette overlay
    ov_draw.rectangle([0, 0, width, height], fill=(6, 8, 12, 140))

    # Fonts
    f_title = get_font("Teko-Bold.ttf", 66)
    f_subtitle = get_font("Rajdhani-Bold.ttf", 25)
    f_header = get_font("Rajdhani-Bold.ttf", 22)
    f_row_team = get_font("Rajdhani-Bold.ttf", 24)
    f_row_players = get_font("Rajdhani-SemiBold.ttf", 17)
    f_row_num = get_font("Teko-Bold.ttf", 36)
    f_badge = get_font("Teko-Bold.ttf", 28)
    f_watermark = get_font("Rajdhani-Bold.ttf", 16)

    # 1. Header Section
    header_y = 35
    ov_draw.rectangle([0, 0, width, 6], fill=theme["primary"])
    ov_draw.rectangle([width // 2 - 280, 6, width // 2 + 280, 10], fill=theme["secondary"])

    # V-Badge Esports
    vbadge_w, vbadge_h = 170, 36
    vbadge_x = (width - vbadge_w) // 2
    ov_draw.polygon([
        (vbadge_x, header_y),
        (vbadge_x + vbadge_w, header_y),
        (vbadge_x + vbadge_w - 12, header_y + vbadge_h),
        (vbadge_x + 12, header_y + vbadge_h)
    ], fill=(*theme["primary"], 240), outline=theme["secondary"], width=2)
    
    ov_draw.text((width // 2, header_y + vbadge_h // 2 - 2), "★ V-BADGE CERTIFIED ★",
                 font=get_font("Rajdhani-Bold.ttf", 17), fill=(255, 255, 255), anchor="mm")

    # Tournament Title
    title_y = header_y + 44
    ov_draw.text((width // 2 + 2, title_y + 2), tournament_title.upper(),
                 font=f_title, fill=(0, 0, 0, 200), anchor="mt")
    ov_draw.text((width // 2, title_y), tournament_title.upper(),
                 font=f_title, fill=theme["highlight"], anchor="mt")

    # Subtitle Match Info
    clean_sub = match_info.replace("⚡", "•").replace("♨", "*")
    sub_y = title_y + 68
    ov_draw.text((width // 2, sub_y), f"★  {clean_sub.upper()}  ★",
                 font=f_subtitle, fill=(210, 225, 245), anchor="mt")

    # 2. Main Leaderboard Card Box
    card_x1 = 70
    card_x2 = width - 70
    card_y1 = sub_y + 46
    card_y2 = height - 50

    # Draw solid high-contrast dark carbon backing
    ov_draw.rectangle([card_x1, card_y1, card_x2, card_y2], fill=theme["card_bg"], outline=(55, 68, 90, 230), width=2)
    
    # Glowing decorative corners
    corner_size = 22
    ov_draw.polygon([(card_x1, card_y1), (card_x1 + corner_size, card_y1), (card_x1, card_y1 + corner_size)], fill=(*theme["primary"], 255))
    ov_draw.polygon([(card_x2, card_y1), (card_x2 - corner_size, card_y1), (card_x2, card_y1 + corner_size)], fill=(*theme["primary"], 255))
    ov_draw.polygon([(card_x1, card_y2), (card_x1 + corner_size, card_y2), (card_x1, card_y2 - corner_size)], fill=(*theme["primary"], 255))
    ov_draw.polygon([(card_x2, card_y2), (card_x2 - corner_size, card_y2), (card_x2, card_y2 - corner_size)], fill=(*theme["primary"], 255))

    # 3. Table Column Positions
    col_rank_x = card_x1 + 65
    col_team_x = card_x1 + 160
    col_kills_x = card_x2 - 400
    col_place_x = card_x2 - 250
    col_total_x = card_x2 - 95

    # Table Header Row
    th_y1 = card_y1 + 4
    th_h = 52
    th_y2 = th_y1 + th_h
    ov_draw.rectangle([card_x1 + 2, th_y1, card_x2 - 2, th_y2], fill=theme["header_bg"])
    ov_draw.line([(card_x1, th_y2), (card_x2, th_y2)], fill=theme["primary"], width=2)

    ov_draw.text((col_rank_x, th_y1 + th_h // 2), "#", font=f_header, fill=(185, 200, 220), anchor="mm")
    ov_draw.text((col_team_x, th_y1 + th_h // 2), "TEAM & SQUAD ROSTER", font=f_header, fill=(185, 200, 220), anchor="lm")
    ov_draw.text((col_kills_x, th_y1 + th_h // 2), "KILL PTS", font=f_header, fill=(185, 200, 220), anchor="mm")
    ov_draw.text((col_place_x, th_y1 + th_h // 2), "PLACE PTS", font=f_header, fill=(185, 200, 220), anchor="mm")
    ov_draw.text((col_total_x, th_y1 + th_h // 2), "TOTAL PTS", font=f_header, fill=theme["primary"], anchor="mm")

    # Rows rendering
    rows_data = standings[:12]
    available_h = card_y2 - th_y2 - 25
    row_h = min(66, max(46, available_h // max(1, len(rows_data))))

    curr_y = th_y2 + 8
    for i, s in enumerate(rows_data):
        rank = s.get("rank", i + 1)
        row_bg = theme["row_odd"] if i % 2 == 0 else theme["row_even"]
        border_col = None

        if rank == 1:
            row_bg = (48, 34, 12, 255)
            border_col = theme["rank1_border"]
        elif rank == 2:
            row_bg = (28, 36, 50, 255)
            border_col = (190, 215, 240)
        elif rank == 3:
            row_bg = (38, 26, 20, 255)
            border_col = (215, 135, 60)

        # Draw row rectangle
        rx1, rx2 = card_x1 + 8, card_x2 - 8
        ry1, ry2 = curr_y, curr_y + row_h - 4
        ov_draw.rectangle([rx1, ry1, rx2, ry2], fill=row_bg, outline=(40, 50, 70, 180), width=1)

        if border_col:
            ov_draw.rectangle([rx1, ry1, rx2, ry2], outline=border_col, width=2)
            ov_draw.rectangle([rx1, ry1, rx1 + 7, ry2], fill=border_col)

        row_center_y = ry1 + (row_h - 4) // 2

        # Rank Badge
        if rank == 1:
            ov_draw.polygon([
                (col_rank_x - 22, row_center_y - 18),
                (col_rank_x + 22, row_center_y - 18),
                (col_rank_x + 16, row_center_y + 18),
                (col_rank_x - 16, row_center_y + 18)
            ], fill=(255, 185, 0), outline=(255, 240, 150))
            ov_draw.text((col_rank_x, row_center_y - 1), "1", font=f_badge, fill=(20, 15, 0), anchor="mm")
        elif rank == 2:
            ov_draw.polygon([
                (col_rank_x - 20, row_center_y - 16),
                (col_rank_x + 20, row_center_y - 16),
                (col_rank_x + 15, row_center_y + 16),
                (col_rank_x - 15, row_center_y + 16)
            ], fill=(200, 215, 235))
            ov_draw.text((col_rank_x, row_center_y - 1), "2", font=f_badge, fill=(15, 22, 34), anchor="mm")
        elif rank == 3:
            ov_draw.polygon([
                (col_rank_x - 20, row_center_y - 16),
                (col_rank_x + 20, row_center_y - 16),
                (col_rank_x + 15, row_center_y + 16),
                (col_rank_x - 15, row_center_y + 16)
            ], fill=(215, 135, 60))
            ov_draw.text((col_rank_x, row_center_y - 1), "3", font=f_badge, fill=(25, 15, 10), anchor="mm")
        else:
            # Ranks 4+ clean hexagon badge
            ov_draw.polygon([
                (col_rank_x - 18, row_center_y - 15),
                (col_rank_x + 18, row_center_y - 15),
                (col_rank_x + 14, row_center_y + 15),
                (col_rank_x - 14, row_center_y + 15)
            ], fill=(28, 36, 52, 230), outline=(60, 75, 105))
            ov_draw.text((col_rank_x, row_center_y - 1), str(rank), font=f_badge, fill=(200, 215, 235), anchor="mm")

        # Team & Player text
        team_raw = sanitize_for_font(s.get("team_raw", s.get("team_name", "")))
        players = [sanitize_for_font(p) for p in s.get("players", [])]
        
        if len(players) > 1:
            main_name = f"SQUAD #{rank}"
            if rank == 1:
                main_name += "  [ BOOYAH! ]"
            player_str = ", ".join(players)
            if len(player_str) > 70:
                player_str = player_str[:67] + "..."
            ov_draw.text((col_team_x, row_center_y - 11), main_name, font=f_row_team,
                         fill=(255, 220, 110) if rank == 1 else (255, 255, 255), anchor="lm")
            ov_draw.text((col_team_x, row_center_y + 12), player_str, font=f_row_players,
                         fill=(190, 205, 225), anchor="lm")
        else:
            ov_draw.text((col_team_x, row_center_y), team_raw[:60], font=f_row_team,
                         fill=(255, 220, 110) if rank == 1 else (255, 255, 255), anchor="lm")

        # Kills
        kills = s.get("kills", 0)
        ov_draw.text((col_kills_x, row_center_y), str(kills), font=f_row_num, fill=(255, 82, 82), anchor="mm")

        # Placement Points
        placement = s.get("placement", 0)
        ov_draw.text((col_place_x, row_center_y), str(placement), font=f_row_num, fill=(100, 181, 246), anchor="mm")

        # Total Points Pill
        tot_pts = s.get("total_points", 0)
        pill_w, pill_h = 80, 38
        pill_color = (*theme["primary"], 240) if rank <= 3 else (38, 48, 68, 240)
        ov_draw.polygon([
            (col_total_x - pill_w // 2, row_center_y - pill_h // 2),
            (col_total_x + pill_w // 2, row_center_y - pill_h // 2),
            (col_total_x + pill_w // 2 - 8, row_center_y + pill_h // 2),
            (col_total_x - pill_w // 2 + 8, row_center_y + pill_h // 2)
        ], fill=pill_color, outline=theme["primary"] if rank <= 3 else (70, 90, 125))
        
        ov_draw.text((col_total_x, row_center_y), str(tot_pts), font=f_row_num,
                     fill=(255, 255, 255) if rank <= 3 else theme["highlight"], anchor="mm")

        curr_y += row_h

    # Watermark Footer
    bot_y = height - 26
    ov_draw.text((card_x1 + 10, bot_y), "FREE FIRE BATTLEX ESPORTS • OFFICIAL POINTS TABLE",
                 font=f_watermark, fill=(140, 155, 180), anchor="lm")
    ov_draw.text((card_x2 - 10, bot_y), "VERIFIED BY BATTLEX TOURNAMENT SYSTEM",
                 font=f_watermark, fill=theme["primary"], anchor="rm")

    final_img = Image.alpha_composite(base_img, overlay)
    
    buf = io.BytesIO()
    final_img.convert("RGB").save(buf, format="PNG", quality=95)
    buf.seek(0)
    return buf
