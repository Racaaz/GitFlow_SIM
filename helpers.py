"""
utils/helpers.py
================
Fungsi pembantu yang dipakai oleh GUI dan core.
"""

import time
from typing import Tuple


# ── Warna animasi ──────────────────────────────────────────────────────────────

ANIM_COLORS = {
    "push_flash":    "#50FA7B",   # hijau — saat push commit baru
    "pop_flash":     "#FF5555",   # merah — saat pop/rewind
    "top_highlight": "#FFB86C",   # oranye — highlight TOP POINTER
    "conflict":      "#FF2222",   # merah terang — konflik aktif
    "resolved":      "#50FA7B",   # hijau — konflik selesai
    "idle":          "#282A36",   # abu gelap — state normal (tema Dracula)
    "branch_active": "#BD93F9",   # ungu — branch yang sedang aktif
}

# ── Tema Warna Aplikasi (Dracula-inspired, dark mode) ─────────────────────────

THEME = {
    # Background
    "bg_main":      "#1E1F29",
    "bg_panel":     "#282A36",
    "bg_card":      "#313442",
    "bg_input":     "#21222C",

    # Text
    "text_primary":    "#F8F8F2",
    "text_secondary":  "#6272A4",
    "text_accent":     "#8BE9FD",

    # Aksen
    "accent_blue":   "#4A9EFF",
    "accent_purple": "#BD93F9",
    "accent_green":  "#50FA7B",
    "accent_orange": "#FFB86C",
    "accent_red":    "#FF5555",
    "accent_pink":   "#FF6B9D",
    "accent_cyan":   "#8BE9FD",
    "accent_yellow": "#F1FA8C",

    # Border
    "border":        "#44475A",
    "border_active": "#6272A4",
}


def lerp_color(c1: str, c2: str, t: float) -> str:
    """
    Interpolasi linear antara dua warna hex.
    t=0.0 → c1, t=1.0 → c2
    Digunakan untuk animasi fade transisi.
    """
    def hex_to_rgb(h: str) -> Tuple[int, int, int]:
        h = h.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))  # type: ignore

    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)

    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)

    return f"#{r:02X}{g:02X}{b:02X}"


def format_content_diff(content_main: str, content_other: str) -> Tuple[list, list, list]:
    """
    Bandingkan dua string konten baris per baris.

    Returns
    -------
    (same_lines, main_only_lines, other_only_lines)
    Masing-masing berisi tuple (nomor_baris, teks_baris).
    """
    lines_main = content_main.splitlines()
    lines_other = content_other.splitlines()
    max_len = max(len(lines_main), len(lines_other), 1)

    same, main_only, other_only = [], [], []

    for i in range(max_len):
        lm = lines_main[i] if i < len(lines_main) else ""
        lo = lines_other[i] if i < len(lines_other) else ""

        if lm == lo:
            same.append((i + 1, lm))
        else:
            if lm:
                main_only.append((i + 1, lm))
            if lo:
                other_only.append((i + 1, lo))

    return same, main_only, other_only


def clamp(value: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, value))
