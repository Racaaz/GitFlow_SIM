"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              GitFlow Sim – GUI v4  (Tahap 4: Polish)                       ║
║                                                                              ║
║  CARA MENJALANKAN:                                                           ║
║    1. Install dependensi (jika belum):                                       ║
║         pip install customtkinter                                            ║
║    2. Pastikan backend_v4.py ada di folder yang sama, lalu:                 ║
║         python main_v4.py                                                   ║
║                                                                              ║
║  LIBRARY YANG DIPERLUKAN:                                                    ║
║    - customtkinter >= 5.2.0   pip install customtkinter                     ║
║    - tkinter                  (bawaan Python – tidak perlu pip)             ║
║    - hashlib, time, random    (bawaan Python – tidak perlu pip)             ║
║                                                                              ║
║  CATATAN FONT:                                                               ║
║    Aplikasi menggunakan font "JetBrains Mono" jika tersedia.               ║
║    Jika tidak, tkinter akan fallback ke font monospace sistem secara        ║
║    otomatis — aplikasi tetap berjalan normal.                               ║
║                                                                              ║
║  PANEL LAYOUT:                                                               ║
║    Kiri   → Memory & Stack Monitor (visualisasi linked list + animasi)     ║
║    Tengah → Time-Travel Visualizer & Editor commit                          ║
║    Kanan  → Conflict Arena (aktif otomatis saat merge conflict)             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import simpledialog
from backend import BranchManager, CommitNode, ConflictInfo

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── Palet Warna Dark Mode (Charcoal + Slate Gray + Neon Electric) ─────────────
C = {
    # Latar belakang bertingkat (charcoal ke slate)
    "bg_dark":   "#0A0E14",          # level terdalam
    "bg_mid":    "#111720",          # panel background
    "bg_card":   "#181F2A",          # kartu / elemen dalam panel
    "border":    "#2A3544",          # border standar

    # Neon elektrik – aksen utama
    "accent":    "#00B4FF",          # biru neon (pointer / info)
    "accent2":   "#00E676",          # hijau neon (commit / sukses)
    "accent3":   "#FF4C4C",          # merah neon (error / conflict)
    "accent4":   "#FFB700",          # amber (rewind / ghost)

    # TOP pointer – ungu neon berpendar
    "top_ptr":       "#BF5FFF",
    "top_ptr_glow":  "#7B2FBE",      # latar kartu TOP
    "top_ptr_badge": "#2A1060",      # badge latar belakang

    # Teks
    "text":      "#D9E4F0",
    "text_dim":  "#5C7087",
    "text_mono": "#6BC5FF",

    # Conflict Arena
    "conf_bg":       "#10050A",
    "conf_border":   "#FF4C4C",
    "conf_main":     "#00B4FF",
    "conf_branch":   "#FF6B6B",
    "conf_fork":     "#FFB700",
    "conf_resolved": "#00E676",

    # Flash animasi push/pop
    "flash_push": "#003322",         # kilatan hijau gelap saat push
    "flash_pop":  "#332200",         # kilatan amber gelap saat pop
}

FM  = ("JetBrains Mono", 11)
FMS = ("JetBrains Mono", 9)
FL  = ("Segoe UI", 11)
FB  = ("Segoe UI", 11, "bold")
FT  = ("Segoe UI", 13, "bold")


# ══════════════════════════════════════════════════════════════════════════════
class GitFlowSimApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("GitFlow Sim  •  Interactive Data Structure & Version Control Simulator")
        self.geometry("1400x820")
        self.minsize(1200, 700)
        self.configure(fg_color=C["bg_dark"])

        self.bm = BranchManager()
        self.bm.commit("Initial commit",
                        "# Selamat datang di GitFlow Sim!\n\nEdit teks di sini lalu klik Commit.")

        self._conflict_branch_name: str | None = None
        self._blink_job     = None
        self._ptr_anim_step = 0
        self._flash_jobs: list = []   # track after-jobs animasi push/pop

        self._build_topbar()
        self._build_layout()
        self._build_left_panel()
        self._build_center_panel()
        self._build_right_panel()

        self._sync_all()
        self.after(120, self._render_timeline)

    # ══════════════════════════════════════════════════════════════════════════
    # TOP BAR
    # ══════════════════════════════════════════════════════════════════════════
    def _build_topbar(self):
        bar = ctk.CTkFrame(self, fg_color=C["bg_mid"], corner_radius=0, height=50)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        # Logo + judul
        ctk.CTkLabel(bar, text="⬡  GitFlow Sim",
                     font=("Segoe UI", 15, "bold"),
                     text_color=C["accent"]).pack(side="left", padx=20)
        ctk.CTkLabel(bar,
                     text="Interactive Data Structure & Version Control Simulator",
                     font=("Segoe UI", 10), text_color=C["text_dim"]).pack(side="left")

        # Branch selector (kanan)
        ctk.CTkLabel(bar, text="Active Branch:", font=FL,
                     text_color=C["text_dim"]).pack(side="right", padx=(0, 6))
        self.var_branch = tk.StringVar(value="main")
        self.cb_branch  = ctk.CTkComboBox(
            bar, variable=self.var_branch, values=["main"], width=160,
            font=FM, command=self._on_switch_branch,
            fg_color=C["bg_card"], border_color=C["accent"],
            button_color=C["accent"], dropdown_fg_color=C["bg_mid"],
            text_color=C["text"]
        )
        self.cb_branch.pack(side="right", padx=10)

    # ══════════════════════════════════════════════════════════════════════════
    # LAYOUT
    # ══════════════════════════════════════════════════════════════════════════
    def _build_layout(self):
        self.mf = ctk.CTkFrame(self, fg_color=C["bg_dark"])
        self.mf.pack(fill="both", expand=True, padx=8, pady=8)
        self.mf.columnconfigure(0, weight=28, minsize=270)
        self.mf.columnconfigure(1, weight=42, minsize=400)
        self.mf.columnconfigure(2, weight=30, minsize=310)
        self.mf.rowconfigure(0, weight=1)

    # ══════════════════════════════════════════════════════════════════════════
    # PANEL KIRI — Memory & Stack Monitor
    # ══════════════════════════════════════════════════════════════════════════
    def _build_left_panel(self):
        outer = ctk.CTkFrame(self.mf, fg_color=C["bg_mid"], corner_radius=12,
                             border_width=1, border_color=C["border"])
        outer.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        # Header
        hdr = ctk.CTkFrame(outer, fg_color="transparent")
        hdr.pack(fill="x", padx=12, pady=(12, 0))
        ctk.CTkLabel(hdr, text="▥  Memory & Stack Monitor",
                     font=FT, text_color=C["accent"]).pack(side="left")

        self.lbl_stack_info = ctk.CTkLabel(outer, text="", font=FMS,
                                           text_color=C["text_dim"])
        self.lbl_stack_info.pack(anchor="w", padx=14, pady=(2, 0))
        ctk.CTkFrame(outer, height=1, fg_color=C["border"]).pack(fill="x", padx=12, pady=6)

        # Scrollable list commit
        self.stack_scroll = ctk.CTkScrollableFrame(
            outer, fg_color="transparent",
            scrollbar_button_color=C["border"],
            scrollbar_button_hover_color=C["accent"])
        self.stack_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        # Legend
        leg = ctk.CTkFrame(outer, fg_color=C["bg_card"], corner_radius=6)
        leg.pack(fill="x", padx=10, pady=(0, 10))
        for col, lbl in [(C["top_ptr"], "TOP PTR"),
                         (C["accent2"], "Commit"),
                         (C["accent4"], "Rolled back")]:
            ctk.CTkLabel(leg, text="●", font=("Segoe UI", 13),
                         text_color=col).pack(side="left", padx=(8, 0), pady=4)
            ctk.CTkLabel(leg, text=f" {lbl}  ", font=("Segoe UI", 9),
                         text_color=C["text_dim"]).pack(side="left")

    def _render_stack_panel(self):
        """Re-render seluruh isi panel kiri."""
        for w in self.stack_scroll.winfo_children():
            w.destroy()
        nodes = self.bm.stack_snapshot()
        self.lbl_stack_info.configure(
            text=f"  Stack size: {len(nodes)}   Rollback buffer: {self.bm.rollback_count()}")
        if not nodes:
            ctk.CTkLabel(self.stack_scroll, text="Stack kosong",
                         text_color=C["text_dim"]).pack(pady=20)
            return
        for idx, node in enumerate(nodes):
            self._make_stack_card(node, idx == 0, idx)
        for node in self.bm.current_rollback().to_list():
            self._make_stack_card(node, False, -1, ghost=True)

    def _make_stack_card(self, node: CommitNode, is_top: bool,
                         idx: int, ghost: bool = False):
        """Buat satu kartu commit di panel kiri."""
        bc = C["top_ptr"] if is_top else (C["accent4"] if ghost else C["border"])
        bg = C["top_ptr_glow"] if is_top else (C["bg_dark"] if ghost else C["bg_card"])
        tc = C["text_dim"] if ghost else C["text"]

        card = ctk.CTkFrame(self.stack_scroll, fg_color=bg, corner_radius=8,
                            border_width=2 if is_top else 1, border_color=bc)
        card.pack(fill="x", pady=3, padx=2)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=7)

        # Baris 1: badge TOP + commit ID + timestamp
        r1 = ctk.CTkFrame(inner, fg_color="transparent")
        r1.pack(fill="x")
        if is_top:
            ctk.CTkLabel(r1, text="◆ TOP PTR", font=("JetBrains Mono", 9, "bold"),
                         text_color=C["top_ptr"], fg_color=C["top_ptr_badge"],
                         corner_radius=4).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(r1, text=f"#{node.commit_id}",
                     font=("JetBrains Mono", 10, "bold"),
                     text_color=C["text_mono"] if not ghost else C["accent4"]
                     ).pack(side="left")
        ctk.CTkLabel(r1, text=node.timestamp, font=FMS,
                     text_color=C["text_dim"]).pack(side="right")

        # Baris 2: pesan commit
        ctk.CTkLabel(inner, text=node.message, font=("Segoe UI", 10),
                     text_color=tc, anchor="w", wraplength=210).pack(fill="x", pady=(2, 0))

        # Baris 3: alamat memori + pointer prev
        r2 = ctk.CTkFrame(inner, fg_color="transparent")
        r2.pack(fill="x", pady=(2, 0))
        ctk.CTkLabel(r2, text=f"addr: {node.fake_address}", font=FMS,
                     text_color=C["accent2"] if not ghost else C["text_dim"]
                     ).pack(side="left")
        if not ghost:
            prev_txt = f"→ prev: {node.prev.fake_address}" if node.prev else "→ prev: NULL"
            ctk.CTkLabel(r2, text=prev_txt, font=FMS,
                         text_color=C["text_dim"] if node.prev else C["accent3"]
                         ).pack(side="left", padx=6)

        # Panah antar node
        nodes = self.bm.stack_snapshot()
        if not ghost and idx < len(nodes) - 1:
            ctk.CTkLabel(self.stack_scroll, text="▼", font=("Segoe UI", 12),
                         text_color=C["border"]).pack()

    # ══════════════════════════════════════════════════════════════════════════
    # PANEL TENGAH — Time-Travel Visualizer & Input
    # ══════════════════════════════════════════════════════════════════════════
    def _build_center_panel(self):
        outer = ctk.CTkFrame(self.mf, fg_color=C["bg_mid"], corner_radius=12,
                             border_width=1, border_color=C["border"])
        outer.grid(row=0, column=1, sticky="nsew", padx=4)

        ctk.CTkLabel(outer, text="⏱  Time-Travel Visualizer",
                     font=FT, text_color=C["accent"]).pack(anchor="w", padx=12, pady=(12, 0))
        ctk.CTkFrame(outer, height=1, fg_color=C["border"]).pack(fill="x", padx=12, pady=6)

        # Editor
        ctk.CTkLabel(outer, text="  📄 Simulasi Isi File", font=FB,
                     text_color=C["text"]).pack(anchor="w", padx=12)
        self.txt_editor = ctk.CTkTextbox(
            outer, height=155, font=FM, fg_color=C["bg_dark"],
            text_color=C["text"], border_color=C["border"], border_width=1)
        self.txt_editor.pack(fill="x", padx=12, pady=(4, 8))

        # ── Commit section ────────────────────────────────────────────────────
        cf = ctk.CTkFrame(outer, fg_color=C["bg_card"], corner_radius=8,
                          border_width=1, border_color=C["border"])
        cf.pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkLabel(cf, text="  ✎  Commit", font=FB,
                     text_color=C["accent2"]).pack(anchor="w", padx=10, pady=(8, 2))
        self.entry_msg = ctk.CTkEntry(
            cf, placeholder_text="Tulis commit message...", font=FM,
            fg_color=C["bg_dark"], border_color=C["border"],
            text_color=C["text"])
        self.entry_msg.pack(fill="x", padx=10, pady=(0, 6))
        # Enter key = commit
        self.entry_msg.bind("<Return>", lambda e: self._on_commit())

        br = ctk.CTkFrame(cf, fg_color="transparent")
        br.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkButton(br, text="⬡  Commit", font=FB, fg_color=C["accent2"],
                      hover_color="#00B84A", text_color="#0A0E14",
                      corner_radius=6, width=105, command=self._on_commit
                      ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(br, text="⎇  New Branch", font=FB, fg_color=C["bg_mid"],
                      hover_color=C["border"], text_color=C["accent"],
                      corner_radius=6, width=130, border_width=1,
                      border_color=C["accent"], command=self._on_new_branch
                      ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(br, text="↩  Merge", font=FB, fg_color=C["bg_mid"],
                      hover_color=C["border"], text_color=C["accent4"],
                      corner_radius=6, width=100, border_width=1,
                      border_color=C["accent4"], command=self._on_merge
                      ).pack(side="left")

        # ── Timeline canvas ───────────────────────────────────────────────────
        ctk.CTkFrame(outer, height=1, fg_color=C["border"]).pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(outer, text="  ◈  Commit Timeline", font=FB,
                     text_color=C["text"]).pack(anchor="w", padx=12)
        self.timeline_canvas = tk.Canvas(outer, height=100, bg=C["bg_dark"],
                                         highlightthickness=0)
        self.timeline_canvas.pack(fill="x", padx=12, pady=(4, 4))

        # ── Time Travel Controls ──────────────────────────────────────────────
        ctk.CTkFrame(outer, height=1, fg_color=C["border"]).pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(outer, text="  ◀▶  Time Travel Controls", font=FB,
                     text_color=C["text"]).pack(anchor="w", padx=12)
        ctrl = ctk.CTkFrame(outer, fg_color="transparent")
        ctrl.pack(fill="x", padx=12, pady=(4, 8))

        self.btn_rewind = ctk.CTkButton(
            ctrl, text="◀  Rewind", font=FB, fg_color=C["accent4"],
            hover_color="#CC8800", text_color="#0A0E14", corner_radius=6,
            width=110, command=self._on_rewind)
        self.btn_rewind.pack(side="left", padx=(0, 8))

        self.btn_forward = ctk.CTkButton(
            ctrl, text="Forward  ▶", font=FB, fg_color=C["accent"],
            hover_color="#0090CC", text_color="#0A0E14", corner_radius=6,
            width=110, command=self._on_forward)
        self.btn_forward.pack(side="left", padx=(0, 12))

        self.slider = ctk.CTkSlider(
            ctrl, from_=0, to=100, command=self._on_slider,
            button_color=C["accent"], progress_color=C["accent4"],
            fg_color=C["border"])
        self.slider.set(100)
        self.slider.pack(side="left", fill="x", expand=True, padx=4)

        # Status bar
        self.lbl_status = ctk.CTkLabel(outer, text="", font=FMS,
                                       text_color=C["text_dim"], anchor="w")
        self.lbl_status.pack(fill="x", padx=14, pady=(0, 8))

    def _render_timeline(self):
        """Gambar timeline commit di canvas tengah."""
        c = self.timeline_canvas
        c.delete("all")
        nodes_asc = list(reversed(self.bm.stack_snapshot()))
        total     = len(nodes_asc)
        if total == 0:
            return
        w    = c.winfo_width() or 420
        h    = 100
        mx   = 44
        step = (w - 2*mx) / max(total - 1, 1)
        cy   = h // 2

        for i, node in enumerate(nodes_asc):
            x      = mx + i * step
            is_head = (i == total - 1)
            # Garis penghubung
            if i > 0:
                c.create_line(mx + (i-1)*step + 14, cy, x - 14, cy,
                              fill=C["accent"] if is_head else C["border"],
                              width=2, dash=(4, 3))
            r    = 15 if is_head else 10
            fill = C["top_ptr"] if is_head else C["accent2"]
            # Glow ring pada HEAD
            if is_head:
                c.create_oval(x-r-4, cy-r-4, x+r+4, cy+r+4,
                              fill="", outline=C["top_ptr_glow"], width=2)
            c.create_oval(x-r, cy-r, x+r, cy+r,
                          fill=fill, outline="#FFFFFF" if is_head else fill, width=2)
            c.create_text(x, cy, text=node.commit_id[:4],
                          fill="#0A0E14", font=("JetBrains Mono", 8, "bold"))
            msg = (node.message[:12] + "…") if len(node.message) > 12 else node.message
            c.create_text(x, cy + r + 14, text=msg,
                          fill=C["text_dim"], font=("Segoe UI", 8))
            if is_head:
                c.create_text(x, cy - r - 12, text="HEAD",
                              fill=C["top_ptr"], font=("JetBrains Mono", 9, "bold"))

        # Ghost (rolled-back) nodes
        for j, node in enumerate(reversed(self.bm.current_rollback().to_list())):
            i2 = total + j
            x  = mx + i2 * step
            if x > w - 10:
                break
            c.create_line(mx + (i2-1)*step + 14, cy, x - 14, cy,
                          fill=C["accent4"], width=1, dash=(2, 4))
            c.create_oval(x-8, cy-8, x+8, cy+8,
                          fill="", outline=C["accent4"], width=1, dash=(2, 2))
            c.create_text(x, cy, text=node.commit_id[:4],
                          fill=C["accent4"], font=("JetBrains Mono", 8))

    # ══════════════════════════════════════════════════════════════════════════
    # PANEL KANAN — Conflict Arena
    # ══════════════════════════════════════════════════════════════════════════
    def _build_right_panel(self):
        self.right_panel = ctk.CTkFrame(
            self.mf, fg_color=C["bg_mid"], corner_radius=12,
            border_width=1, border_color=C["border"])
        self.right_panel.grid(row=0, column=2, sticky="nsew", padx=(4, 0))

        # Header
        hdr = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        hdr.pack(fill="x", padx=12, pady=(12, 0))
        self.lbl_arena_title = ctk.CTkLabel(
            hdr, text="⚔  Conflict Arena",
            font=FT, text_color=C["text_dim"])
        self.lbl_arena_title.pack(side="left")
        self.lbl_arena_badge = ctk.CTkLabel(
            hdr, text="  IDLE  ", font=FMS,
            fg_color=C["bg_card"], text_color=C["text_dim"],
            corner_radius=4)
        self.lbl_arena_badge.pack(side="left", padx=8)

        ctk.CTkFrame(self.right_panel, height=1,
                     fg_color=C["border"]).pack(fill="x", padx=12, pady=6)

        # ── Idle placeholder ──────────────────────────────────────────────────
        self.idle_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.idle_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(self.idle_frame, text="⚠", font=("Segoe UI", 42),
                     text_color=C["border"]).pack(pady=(40, 4))
        ctk.CTkLabel(self.idle_frame,
                     text="Panel ini aktif saat\nada Merge Conflict.",
                     font=("Segoe UI", 11), text_color=C["text_dim"],
                     justify="center").pack()
        ctk.CTkLabel(self.idle_frame,
                     text="\nCara memicu konflik:\n"
                          "1. Commit di main\n"
                          "2. Buat branch baru\n"
                          "3. Ubah teks → commit di branch\n"
                          "4. Switch ke main\n"
                          "5. Ubah teks → commit di main\n"
                          "6. Klik Merge ↩",
                     font=("Segoe UI", 10), text_color=C["text_dim"],
                     justify="left").pack(padx=20, pady=(8, 0))

        # ── Active conflict UI ────────────────────────────────────────────────
        self.conflict_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")

        # Canvas pointer clash
        self.conf_canvas = tk.Canvas(
            self.conflict_frame, height=220, bg=C["conf_bg"],
            highlightthickness=0)
        self.conf_canvas.pack(fill="x", padx=12, pady=(0, 6))

        # Info cards: main vs branch
        cards_row = ctk.CTkFrame(self.conflict_frame, fg_color="transparent")
        cards_row.pack(fill="x", padx=12, pady=(0, 6))
        cards_row.columnconfigure(0, weight=1)
        cards_row.columnconfigure(1, weight=1)
        self.card_main   = self._make_conflict_card(cards_row, 0, "main",   C["conf_main"])
        self.card_branch = self._make_conflict_card(cards_row, 1, "branch", C["conf_branch"])

        # Diff view
        ctk.CTkLabel(self.conflict_frame, text="  ⚡  Perbedaan Konten (HEAD vs HEAD)",
                     font=FB, text_color=C["text_dim"]).pack(anchor="w", padx=12)
        self.txt_diff = ctk.CTkTextbox(
            self.conflict_frame, height=100, font=FMS,
            fg_color=C["bg_dark"], text_color=C["text"],
            border_color=C["conf_border"], border_width=1,
            state="disabled")
        self.txt_diff.pack(fill="x", padx=12, pady=(2, 8))

        # Resolution buttons
        ctk.CTkFrame(self.conflict_frame, height=1,
                     fg_color=C["conf_border"]).pack(fill="x", padx=12, pady=(0, 8))
        ctk.CTkLabel(self.conflict_frame, text="  Pilih Resolusi:",
                     font=FB, text_color=C["text"]).pack(anchor="w", padx=12)
        btn_row = ctk.CTkFrame(self.conflict_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=(4, 12))
        self.btn_keep_main = ctk.CTkButton(
            btn_row, text="✔  Keep Main",
            font=FB, fg_color=C["conf_main"], hover_color="#0080BB",
            text_color="#0A0E14", corner_radius=6,
            command=lambda: self._resolve_conflict(keep_main=True))
        self.btn_keep_main.pack(side="left", expand=True, fill="x", padx=(0, 4))
        self.btn_keep_branch = ctk.CTkButton(
            btn_row, text="✔  Accept Branch",
            font=FB, fg_color=C["conf_branch"], hover_color="#CC3333",
            text_color="#0A0E14", corner_radius=6,
            command=lambda: self._resolve_conflict(keep_main=False))
        self.btn_keep_branch.pack(side="left", expand=True, fill="x", padx=(4, 0))

        # Resolved banner (tersembunyi sampai konflik selesai)
        self.resolved_frame = ctk.CTkFrame(
            self.conflict_frame,
            fg_color="#061A0D", corner_radius=8,
            border_width=1, border_color=C["conf_resolved"])
        self.lbl_resolved = ctk.CTkLabel(
            self.resolved_frame, text="", font=FB,
            text_color=C["conf_resolved"], justify="center")
        self.lbl_resolved.pack(padx=12, pady=10)

    def _make_conflict_card(self, parent, col, label, color):
        """Buat kartu info branch di Conflict Arena."""
        f = ctk.CTkFrame(parent, fg_color=C["bg_card"], corner_radius=8,
                         border_width=1, border_color=color)
        f.grid(row=0, column=col, sticky="ew",
               padx=(0, 4) if col == 0 else (4, 0), pady=2)
        ctk.CTkLabel(f, text=label.upper(), font=("JetBrains Mono", 9, "bold"),
                     text_color=color).pack(anchor="w", padx=8, pady=(6, 0))
        id_lbl  = ctk.CTkLabel(f, text="—", font=FMS, text_color=C["text_mono"])
        id_lbl.pack(anchor="w", padx=8)
        msg_lbl = ctk.CTkLabel(f, text="—", font=("Segoe UI", 9),
                               text_color=C["text_dim"], wraplength=130)
        msg_lbl.pack(anchor="w", padx=8, pady=(0, 6))
        return {"frame": f, "id": id_lbl, "msg": msg_lbl, "color": color}

    # ── Conflict Arena canvas drawing ─────────────────────────────────────────
    def _draw_conflict_canvas(self, info: ConflictInfo):
        """
        Visualisasi dua pointer bertabrakan memperebutkan fork-point.
        Animasi jitter memberikan kesan 'perebutan' secara visual.
        """
        c  = self.conf_canvas
        c.delete("all")
        W  = c.winfo_width() or 310
        H  = 220
        cx = W // 2
        cy = H // 2

        # Subtle grid background
        for x in range(0, W, 24):
            c.create_line(x, 0, x, H, fill="#1A0808", width=1)
        for y in range(0, H, 24):
            c.create_line(0, y, W, y, fill="#1A0808", width=1)

        # Fork-point box (tengah)
        bw, bh = 110, 52
        c.create_rectangle(cx-bw//2-2, cy-bh//2-2, cx+bw//2+2, cy+bh//2+2,
                           fill="#2D1800", outline=C["conf_fork"], width=2)
        c.create_text(cx, cy - 10, text="FORK POINT",
                      fill=C["conf_fork"], font=("JetBrains Mono", 8, "bold"))
        c.create_text(cx, cy + 8, text=f"id: {info.fork_id or '—'}",
                      fill=C["text_dim"], font=("JetBrains Mono", 8))

        # HEAD main (kiri) – jitter kiri-kanan
        jitter = self._ptr_anim_step % 2
        lx = 28 + jitter
        c.create_rectangle(lx, cy-22, lx+90, cy+22,
                           fill="#071830", outline=C["conf_main"], width=2)
        c.create_text(lx+45, cy-8, text="main HEAD",
                      fill=C["conf_main"], font=("JetBrains Mono", 8, "bold"))
        c.create_text(lx+45, cy+7, text=f"#{info.head_a.commit_id}",
                      fill=C["text_mono"], font=("JetBrains Mono", 8))
        c.create_line(lx+90, cy, cx-bw//2, cy,
                      fill=C["conf_main"], width=3,
                      arrow=tk.LAST, arrowshape=(10, 12, 4))
        c.create_text(lx+45, cy+30, text=info.head_a.fake_address,
                      fill=C["text_dim"], font=("JetBrains Mono", 7))

        # HEAD branch (kanan) – jitter berlawanan
        rx = W - 28 - 90 - jitter
        c.create_rectangle(rx, cy-22, rx+90, cy+22,
                           fill="#2D0707", outline=C["conf_branch"], width=2)
        c.create_text(rx+45, cy-8, text=f"{info.branch_b} HEAD",
                      fill=C["conf_branch"], font=("JetBrains Mono", 8, "bold"))
        c.create_text(rx+45, cy+7, text=f"#{info.head_b.commit_id}",
                      fill=C["text_mono"], font=("JetBrains Mono", 8))
        c.create_line(rx, cy, cx+bw//2, cy,
                      fill=C["conf_branch"], width=3,
                      arrow=tk.LAST, arrowshape=(10, 12, 4))
        c.create_text(rx+45, cy+30, text=info.head_b.fake_address,
                      fill=C["text_dim"], font=("JetBrains Mono", 7))

        # Berkedip bergantian merah/amber
        bolt_color = C["accent3"] if self._ptr_anim_step % 2 == 0 else C["conf_fork"]
        c.create_text(cx, cy - bh//2 - 22, text="⚡ CONFLICT ⚡",
                      fill=bolt_color, font=("Segoe UI", 10, "bold"))

        c.create_text(cx, H - 14,
                      text="Dua pointer memperebutkan slot memori yang sama",
                      fill=C["text_dim"], font=("Segoe UI", 8))

    def _start_conflict_anim(self):
        def _tick():
            if self._conflict_branch_name is None:
                return
            info = self.bm.last_conflict
            if info:
                self._ptr_anim_step += 1
                self._draw_conflict_canvas(info)
            self._blink_job = self.after(500, _tick)
        _tick()

    def _stop_conflict_anim(self):
        if self._blink_job:
            self.after_cancel(self._blink_job)
            self._blink_job = None

    # ── Activate / Deactivate ─────────────────────────────────────────────────
    def _activate_conflict_panel(self, branch_name: str, info: ConflictInfo):
        self._conflict_branch_name = branch_name
        self._stop_conflict_anim()

        self.idle_frame.pack_forget()
        self.resolved_frame.pack_forget()
        self.conflict_frame.pack(fill="both", expand=True)

        self.right_panel.configure(fg_color=C["conf_bg"],
                                   border_color=C["conf_border"])
        self.lbl_arena_title.configure(text_color=C["accent3"])
        self.lbl_arena_badge.configure(text=" ⚠ CONFLICT ", fg_color=C["accent3"],
                                       text_color="#0A0E14")

        self.card_main["id"].configure(text=f"#{info.head_a.commit_id}")
        self.card_main["msg"].configure(text=info.head_a.message)
        self.card_branch["id"].configure(text=f"#{info.head_b.commit_id}")
        self.card_branch["msg"].configure(text=info.head_b.message)
        for w in self.card_branch["frame"].winfo_children():
            if isinstance(w, ctk.CTkLabel) and w.cget("text") in ("BRANCH", branch_name.upper()):
                w.configure(text=branch_name.upper())
                break

        self._update_diff(info)
        self.after(80, lambda: self._draw_conflict_canvas(info))
        self._start_conflict_anim()
        self._flash_status("⚠  Konflik terdeteksi! Pilih resolusi di Panel Kanan.",
                           color=C["accent3"])

    def _deactivate_conflict_panel(self, winner_label: str):
        self._stop_conflict_anim()
        self._conflict_branch_name = None

        self.conflict_frame.pack_forget()
        self.right_panel.configure(fg_color=C["bg_mid"], border_color=C["border"])
        self.lbl_arena_title.configure(text_color=C["text_dim"])
        self.lbl_arena_badge.configure(text="  RESOLVED  ",
                                       fg_color=C["conf_resolved"],
                                       text_color="#0A0E14")

        self.lbl_resolved.configure(
            text=f"✔  Konflik diselesaikan\nPemenang: {winner_label}")
        self.resolved_frame.pack(padx=12, pady=8)
        self.idle_frame.pack(fill="both", expand=True)
        self.after(3000, lambda: self.resolved_frame.pack_forget())

    def _update_diff(self, info: ConflictInfo):
        """Tampilkan diff sederhana (baris berbeda) di txt_diff."""
        lines_a = info.head_a.content.splitlines()
        lines_b = info.head_b.content.splitlines()
        diff_lines = []
        max_l = max(len(lines_a), len(lines_b))
        for i in range(max_l):
            a = lines_a[i] if i < len(lines_a) else ""
            b = lines_b[i] if i < len(lines_b) else ""
            if a != b:
                diff_lines.append(f"L{i+1}  main:   {a}")
                diff_lines.append(f"L{i+1}  branch: {b}")
        text = "\n".join(diff_lines) if diff_lines else "(Perbedaan tidak terdeteksi pada baris)"
        self.txt_diff.configure(state="normal")
        self.txt_diff.delete("1.0", "end")
        self.txt_diff.insert("1.0", text)
        self.txt_diff.configure(state="disabled")

    # ══════════════════════════════════════════════════════════════════════════
    # EVENT HANDLERS
    # ══════════════════════════════════════════════════════════════════════════
    def _on_commit(self):
        """Handler tombol Commit. Validasi pesan & konten sebelum commit."""
        message = self.entry_msg.get().strip()
        content = self.txt_editor.get("1.0", "end-1c")

        # Validasi: pesan kosong
        if not message:
            self._flash_status("⚠  Tulis commit message terlebih dahulu!", color=C["accent3"])
            self.entry_msg.focus()
            # Beri efek border merah pada entry
            self.entry_msg.configure(border_color=C["accent3"])
            self.after(1500, lambda: self.entry_msg.configure(border_color=C["border"]))
            return

        # Validasi: konten editor kosong
        if not content.strip():
            self._flash_status("⚠  Editor kosong! Tulis sesuatu sebelum commit.", color=C["accent3"])
            self.txt_editor.focus()
            return

        node = self.bm.commit(message, content)
        self.entry_msg.delete(0, "end")
        self._flash_status(f"✔  Commit [{node.commit_id}] — '{message}'",
                           color=C["accent2"])
        self._sync_all(animate_push=True)

    def _on_rewind(self):
        """Handler tombol Rewind. Safe – tidak crash saat stack minimal."""
        # Guard: sudah di commit paling awal
        if not self.bm.can_rewind():
            self._flash_status("⚠  Sudah di commit paling awal – tidak bisa rewind lagi.",
                               color=C["accent3"])
            # Getar tombol rewind sebagai feedback visual
            self._shake_button(self.btn_rewind)
            return

        self.bm.rewind()
        head = self.bm.top_pointer()
        if head:
            self._set_editor(head.content)
            self._flash_status(f"◀  Rewind → [{head.commit_id}] — '{head.message}'",
                               color=C["accent4"])
        self._sync_all(animate_pop=True)

    def _on_forward(self):
        """Handler tombol Forward."""
        if not self.bm.can_forward():
            self._flash_status("⚠  Tidak ada commit untuk di-forward.", color=C["accent3"])
            self._shake_button(self.btn_forward)
            return
        node = self.bm.forward()
        if node:
            self._set_editor(node.content)
            self._flash_status(f"▶  Forward → [{node.commit_id}] — '{node.message}'",
                               color=C["accent"])
        self._sync_all()

    def _on_slider(self, val):
        """Handler slider time-travel."""
        stack_size = self.bm.current_stack().size()
        rb_size    = self.bm.current_rollback().size()
        total      = stack_size + rb_size
        if total <= 1:
            return
        target  = int(float(val))
        current = stack_size
        if target < current:
            for _ in range(current - target):
                if not self.bm.can_rewind():
                    break
                self.bm.rewind()
        elif target > current:
            for _ in range(target - current):
                if not self.bm.can_forward():
                    break
                self.bm.forward()
        head = self.bm.top_pointer()
        if head:
            self._set_editor(head.content)
            self._flash_status(f"◈  Time travel → [{head.commit_id}]", color=C["accent"])
        self._sync_all()

    def _on_new_branch(self):
        """Handler tombol New Branch."""
        name = simpledialog.askstring("New Branch", "Nama branch baru:", parent=self)
        if not name:
            return
        name = name.strip().replace(" ", "-").lower()
        if not name:
            self._flash_status("⚠  Nama branch tidak valid.", color=C["accent3"])
            return
        if self.bm.create_branch(name):
            self.bm.switch_branch(name)
            self._update_branch_selector()
            self._flash_status(f"⎇  Branch [{name}] dibuat & aktif.", color=C["accent"])
            self._sync_all()
        else:
            self._flash_status(f"⚠  Branch '{name}' sudah ada.", color=C["accent3"])

    def _on_switch_branch(self, name: str):
        """Handler ComboBox ganti branch."""
        if self.bm.switch_branch(name):
            head = self.bm.top_pointer()
            if head:
                self._set_editor(head.content)
            self._flash_status(f"⎇  Pindah ke branch [{name}]", color=C["accent"])
            self._sync_all()

    def _on_merge(self):
        """Handler tombol Merge."""
        branches = [b for b in self.bm.branch_names if b != "main"]
        if not branches:
            self._flash_status("⚠  Tidak ada branch lain untuk di-merge.",
                               color=C["accent3"])
            return
        if len(branches) == 1:
            src = branches[0]
        else:
            src = simpledialog.askstring(
                "Merge Branch",
                f"Branch yang di-merge ke main:\n{', '.join(branches)}",
                parent=self)
        if not src or src not in self.bm.branch_names:
            return

        info = self.bm.detect_conflict(src)
        if info:
            self._activate_conflict_panel(src, info)
        else:
            self.bm.switch_branch("main")
            self.bm.merge(src, keep_main=True)
            self._update_branch_selector()
            self._flash_status(f"↩  Merge [{src}] → main sukses (no conflict).",
                               color=C["accent2"])
            self._sync_all()

    def _resolve_conflict(self, keep_main: bool):
        """Selesaikan konflik dengan memilih versi main atau branch."""
        src = self._conflict_branch_name
        if not src:
            return
        self.bm.switch_branch("main")
        winner_node = self.bm.merge(src, keep_main=keep_main)
        self._update_branch_selector()
        if winner_node:
            self._set_editor(winner_node.content)
        label = "main" if keep_main else src
        self._deactivate_conflict_panel(winner_label=label)
        self._flash_status(f"✔  Konflik selesai — pemenang: [{label}]",
                           color=C["conf_resolved"])
        self._sync_all()

    # ══════════════════════════════════════════════════════════════════════════
    # ANIMASI VISUAL
    # ══════════════════════════════════════════════════════════════════════════
    def _flash_top_card(self, color: str, restore_color: str):
        """
        Efek kilat (flash) pada kartu TOP saat push atau pop.
        Warna berubah seketika lalu kembali ke warna asli setelah 350ms.
        """
        cards = self.stack_scroll.winfo_children()
        if not cards:
            return
        try:
            top_card = cards[0]
            top_card.configure(fg_color=color)
            job = self.after(350, lambda: self._safe_restore_card(top_card, restore_color))
            self._flash_jobs.append(job)
        except Exception:
            pass

    def _safe_restore_card(self, card, color: str):
        """Kembalikan warna kartu dengan aman (guard jika widget sudah destroyed)."""
        try:
            card.configure(fg_color=color)
        except Exception:
            pass

    def _shake_button(self, btn):
        """
        Efek 'goyang' pada tombol sebagai feedback error visual.
        Tombol bergerak kecil kiri-kanan 3x.
        """
        original_x = btn.winfo_x()
        offsets = [4, -4, 3, -3, 2, -2, 0]
        def _step(i=0):
            if i >= len(offsets):
                return
            try:
                btn.place_configure(x=original_x + offsets[i])
            except Exception:
                pass
            self.after(40, lambda: _step(i + 1))
        # Shake hanya bekerja jika tombol di-place; jika pack, skip (graceful)
        try:
            btn.place_configure(x=original_x)
            _step()
        except Exception:
            pass

    def _flash_status_blink(self, msg: str, color: str, times: int = 3):
        """
        Teks status berkedip (blink) untuk pesan error/warning penting.
        """
        def _blink(n):
            if n <= 0:
                self.lbl_status.configure(text=f"  {msg}", text_color=color)
                return
            vis = n % 2 == 0
            self.lbl_status.configure(
                text=f"  {msg}" if vis else "",
                text_color=color)
            self.after(200, lambda: _blink(n - 1))
        _blink(times * 2)

    # ══════════════════════════════════════════════════════════════════════════
    # SYNC & HELPERS
    # ══════════════════════════════════════════════════════════════════════════
    def _sync_all(self, animate_push=False, animate_pop=False):
        """Sinkronisasi semua widget dengan state backend."""
        self._render_stack_panel()
        self._render_timeline()
        self._update_slider()
        self._update_buttons()
        if animate_push:
            # Kilatan hijau neon saat PUSH
            self.after(60, lambda: self._flash_top_card(C["accent2"], C["top_ptr_glow"]))
            self.after(420, lambda: self._flash_top_card("#003322", C["top_ptr_glow"]))
        if animate_pop:
            # Kilatan amber saat POP
            self.after(60, lambda: self._flash_top_card(C["accent4"], C["top_ptr_glow"]))
            self.after(420, lambda: self._flash_top_card("#332200", C["top_ptr_glow"]))

    def _update_buttons(self):
        """Enable/disable tombol rewind dan forward sesuai state."""
        self.btn_rewind.configure(
            state="normal" if self.bm.can_rewind()  else "disabled")
        self.btn_forward.configure(
            state="normal" if self.bm.can_forward() else "disabled")

    def _update_slider(self):
        """Sinkronisasi posisi slider time-travel."""
        ss = self.bm.current_stack().size()
        rb = self.bm.current_rollback().size()
        total = ss + rb
        if total > 1:
            self.slider.configure(from_=1, to=float(total))
            self.slider.set(float(ss))
        else:
            self.slider.configure(from_=0, to=100)
            self.slider.set(100)

    def _update_branch_selector(self):
        """Perbarui ComboBox branch dengan daftar branch terkini."""
        self.cb_branch.configure(values=self.bm.branch_names)
        self.var_branch.set(self.bm.active_branch)

    def _set_editor(self, content: str):
        """Set konten editor teks."""
        self.txt_editor.delete("1.0", "end")
        self.txt_editor.insert("1.0", content)

    def _flash_status(self, msg: str, color: str = None):
        """Tampilkan pesan di status bar."""
        self.lbl_status.configure(text=f"  {msg}",
                                  text_color=color or C["text_dim"])


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = GitFlowSimApp()
    app.after(120, app._render_timeline)
    app.mainloop()
