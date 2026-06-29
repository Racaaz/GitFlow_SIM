"""
GitFlow Sim – GUI v3  (Tahap 3: Conflict Arena)
Panel Kiri   : Memory & Stack Monitor
Panel Tengah : Time-Travel Visualizer & Input
Panel Kanan  : Conflict Arena (aktif saat ada merge conflict)
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import simpledialog
from backend import BranchManager, CommitNode, ConflictInfo

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── Palet warna ───────────────────────────────────────────────────────────────
C = {
    "bg_dark":   "#0D1117",
    "bg_mid":    "#161B22",
    "bg_card":   "#1C2128",
    "border":    "#30363D",
    "accent":    "#58A6FF",
    "accent2":   "#3FB950",
    "accent3":   "#F85149",
    "accent4":   "#D29922",
    "top_ptr":   "#BC8CFF",
    "text":      "#E6EDF3",
    "text_dim":  "#8B949E",
    "text_mono": "#79C0FF",
    # Conflict Arena colours
    "conf_bg":       "#1A0505",
    "conf_border":   "#F85149",
    "conf_main":     "#58A6FF",
    "conf_branch":   "#FF7B72",
    "conf_fork":     "#D29922",
    "conf_resolved": "#3FB950",
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
        self.geometry("1380x800")
        self.minsize(1200, 700)
        self.configure(fg_color=C["bg_dark"])

        self.bm = BranchManager()
        self.bm.commit("Initial commit",
                        "# Selamat datang di GitFlow Sim!\n\nEdit teks di sini lalu klik Commit.")

        self._conflict_branch_name: str | None = None
        self._blink_job = None
        self._ptr_anim_step = 0

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
        bar = ctk.CTkFrame(self, fg_color=C["bg_mid"], corner_radius=0, height=48)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        ctk.CTkLabel(bar, text="⬡  GitFlow Sim",
                     font=("Segoe UI", 15, "bold"),
                     text_color=C["accent"]).pack(side="left", padx=20)
        ctk.CTkLabel(bar,
                     text="Interactive Data Structure & Version Control Simulator",
                     font=("Segoe UI", 10), text_color=C["text_dim"]).pack(side="left")

        ctk.CTkLabel(bar, text="Branch:", font=FL,
                     text_color=C["text_dim"]).pack(side="right", padx=(0, 6))
        self.var_branch = tk.StringVar(value="main")
        self.cb_branch  = ctk.CTkComboBox(
            bar, variable=self.var_branch, values=["main"], width=150,
            font=FM, command=self._on_switch_branch,
            fg_color=C["bg_card"], border_color=C["border"],
            button_color=C["accent"], dropdown_fg_color=C["bg_mid"]
        )
        self.cb_branch.pack(side="right", padx=6)
        ctk.CTkLabel(bar, text="Active:", font=FL,
                     text_color=C["text_dim"]).pack(side="right")

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
        outer = ctk.CTkFrame(self.mf, fg_color=C["bg_mid"], corner_radius=10,
                             border_width=1, border_color=C["border"])
        outer.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        hdr = ctk.CTkFrame(outer, fg_color="transparent")
        hdr.pack(fill="x", padx=12, pady=(12, 0))
        ctk.CTkLabel(hdr, text="▥  Memory & Stack Monitor",
                     font=FT, text_color=C["accent"]).pack(side="left")

        self.lbl_stack_info = ctk.CTkLabel(outer, text="", font=FMS,
                                           text_color=C["text_dim"])
        self.lbl_stack_info.pack(anchor="w", padx=14)
        ctk.CTkFrame(outer, height=1, fg_color=C["border"]).pack(fill="x", padx=12, pady=6)

        self.stack_scroll = ctk.CTkScrollableFrame(
            outer, fg_color="transparent",
            scrollbar_button_color=C["border"])
        self.stack_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        leg = ctk.CTkFrame(outer, fg_color="transparent")
        leg.pack(fill="x", padx=12, pady=(0, 10))
        for col, lbl in [(C["top_ptr"], "TOP PTR"), (C["accent2"], "Commit"),
                         (C["accent4"], "Rolled back")]:
            ctk.CTkLabel(leg, text="●", font=("Segoe UI", 14),
                         text_color=col).pack(side="left")
            ctk.CTkLabel(leg, text=f" {lbl}  ", font=("Segoe UI", 9),
                         text_color=C["text_dim"]).pack(side="left")

    def _render_stack_panel(self):
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
        bc = C["top_ptr"] if is_top else (C["accent4"] if ghost else C["border"])
        bg = "#1A1060" if is_top else (C["bg_dark"] if ghost else C["bg_card"])
        tc = C["text_dim"] if ghost else C["text"]

        card = ctk.CTkFrame(self.stack_scroll, fg_color=bg, corner_radius=6,
                            border_width=2 if is_top else 1, border_color=bc)
        card.pack(fill="x", pady=3, padx=2)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=6)

        r1 = ctk.CTkFrame(inner, fg_color="transparent")
        r1.pack(fill="x")
        if is_top:
            ctk.CTkLabel(r1, text="[ TOP PTR ]", font=("JetBrains Mono", 9, "bold"),
                         text_color=C["top_ptr"], fg_color="#2A1A6A",
                         corner_radius=4).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(r1, text=f"#{node.commit_id}",
                     font=("JetBrains Mono", 10, "bold"),
                     text_color=C["text_mono"] if not ghost else C["accent4"]
                     ).pack(side="left")
        ctk.CTkLabel(r1, text=node.timestamp, font=FMS,
                     text_color=C["text_dim"]).pack(side="right")

        ctk.CTkLabel(inner, text=node.message, font=("Segoe UI", 10),
                     text_color=tc, anchor="w", wraplength=210).pack(fill="x", pady=(2, 0))

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

        nodes = self.bm.stack_snapshot()
        if not ghost and idx < len(nodes) - 1:
            ctk.CTkLabel(self.stack_scroll, text="▼", font=("Segoe UI", 12),
                         text_color=C["border"]).pack()

    # ══════════════════════════════════════════════════════════════════════════
    # PANEL TENGAH — Time-Travel Visualizer & Input
    # ══════════════════════════════════════════════════════════════════════════
    def _build_center_panel(self):
        outer = ctk.CTkFrame(self.mf, fg_color=C["bg_mid"], corner_radius=10,
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

        # Commit section
        cf = ctk.CTkFrame(outer, fg_color=C["bg_card"], corner_radius=8,
                          border_width=1, border_color=C["border"])
        cf.pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkLabel(cf, text="  ✎  Commit", font=FB,
                     text_color=C["accent2"]).pack(anchor="w", padx=10, pady=(8, 2))
        self.entry_msg = ctk.CTkEntry(
            cf, placeholder_text="Tulis commit message...", font=FM,
            fg_color=C["bg_dark"], border_color=C["border"], text_color=C["text"])
        self.entry_msg.pack(fill="x", padx=10, pady=(0, 6))

        br = ctk.CTkFrame(cf, fg_color="transparent")
        br.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkButton(br, text="⬡  Commit", font=FB, fg_color=C["accent2"],
                      hover_color="#2EA043", text_color="#0D1117",
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

        # Timeline canvas
        ctk.CTkFrame(outer, height=1, fg_color=C["border"]).pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(outer, text="  ◈  Commit Timeline", font=FB,
                     text_color=C["text"]).pack(anchor="w", padx=12)
        self.timeline_canvas = tk.Canvas(outer, height=95, bg=C["bg_dark"],
                                         highlightthickness=0)
        self.timeline_canvas.pack(fill="x", padx=12, pady=(4, 4))

        # Controls
        ctk.CTkFrame(outer, height=1, fg_color=C["border"]).pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(outer, text="  ◀▶  Time Travel Controls", font=FB,
                     text_color=C["text"]).pack(anchor="w", padx=12)
        ctrl = ctk.CTkFrame(outer, fg_color="transparent")
        ctrl.pack(fill="x", padx=12, pady=(4, 8))

        self.btn_rewind = ctk.CTkButton(
            ctrl, text="◀  Rewind", font=FB, fg_color=C["accent4"],
            hover_color="#B07900", text_color="#0D1117", corner_radius=6,
            width=110, command=self._on_rewind)
        self.btn_rewind.pack(side="left", padx=(0, 8))

        self.btn_forward = ctk.CTkButton(
            ctrl, text="Forward  ▶", font=FB, fg_color=C["accent"],
            hover_color="#1A7FD4", text_color="#0D1117", corner_radius=6,
            width=110, command=self._on_forward)
        self.btn_forward.pack(side="left", padx=(0, 12))

        self.slider = ctk.CTkSlider(
            ctrl, from_=0, to=100, command=self._on_slider,
            button_color=C["accent"], progress_color=C["accent4"],
            fg_color=C["border"])
        self.slider.set(100)
        self.slider.pack(side="left", fill="x", expand=True, padx=4)

        self.lbl_status = ctk.CTkLabel(outer, text="", font=FMS,
                                       text_color=C["text_dim"], anchor="w")
        self.lbl_status.pack(fill="x", padx=14, pady=(0, 8))

    def _render_timeline(self):
        c = self.timeline_canvas
        c.delete("all")
        nodes_asc = list(reversed(self.bm.stack_snapshot()))
        total     = len(nodes_asc)
        if total == 0:
            return
        w  = c.winfo_width() or 420
        h  = 95
        mx = 44
        step = (w - 2*mx) / max(total - 1, 1)
        cy = h // 2

        for i, node in enumerate(nodes_asc):
            x = mx + i * step
            is_head = (i == total - 1)
            if i > 0:
                c.create_line(mx + (i-1)*step + 14, cy, x - 14, cy,
                              fill=C["border"], width=2, dash=(4, 3))
            r    = 14 if is_head else 10
            fill = C["top_ptr"] if is_head else C["accent2"]
            c.create_oval(x-r, cy-r, x+r, cy+r,
                          fill=fill, outline="#FFF" if is_head else fill, width=2)
            c.create_text(x, cy, text=node.commit_id[:4],
                          fill="#0D1117", font=("JetBrains Mono", 8, "bold"))
            msg = (node.message[:12] + "…") if len(node.message) > 12 else node.message
            c.create_text(x, cy + r + 14, text=msg,
                          fill=C["text_dim"], font=("Segoe UI", 8))
            if is_head:
                c.create_text(x, cy - r - 10, text="HEAD",
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
            self.mf, fg_color=C["bg_mid"], corner_radius=10,
            border_width=1, border_color=C["border"])
        self.right_panel.grid(row=0, column=2, sticky="nsew", padx=(4, 0))

        # ── Header ────────────────────────────────────────────────────────────
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

        # ── Idle state (placeholder) ──────────────────────────────────────────
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
        # (dikemas saat konflik aktif via _activate_conflict_panel)

        # Canvas untuk visualisasi dua pointer bertabrakan
        self.conf_canvas = tk.Canvas(
            self.conflict_frame, height=220, bg=C["conf_bg"],
            highlightthickness=0)
        self.conf_canvas.pack(fill="x", padx=12, pady=(0, 6))

        # Info cards
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
            font=FB, fg_color=C["conf_main"], hover_color="#1A5FAD",
            text_color="#0D1117", corner_radius=6,
            command=lambda: self._resolve_conflict(keep_main=True))
        self.btn_keep_main.pack(side="left", expand=True, fill="x", padx=(0, 4))

        self.btn_keep_branch = ctk.CTkButton(
            btn_row, text="✔  Accept Branch",
            font=FB, fg_color=C["conf_branch"], hover_color="#C0392B",
            text_color="#0D1117", corner_radius=6,
            command=lambda: self._resolve_conflict(keep_main=False))
        self.btn_keep_branch.pack(side="left", expand=True, fill="x", padx=(4, 0))

        # Resolved banner (hidden until resolved)
        self.resolved_frame = ctk.CTkFrame(
            self.conflict_frame,
            fg_color="#0D2B1A", corner_radius=8,
            border_width=1, border_color=C["conf_resolved"])
        self.lbl_resolved = ctk.CTkLabel(
            self.resolved_frame, text="", font=FB,
            text_color=C["conf_resolved"], justify="center")
        self.lbl_resolved.pack(padx=12, pady=10)

    def _make_conflict_card(self, parent, col, label, color):
        """Kartu info branch saat konflik."""
        f = ctk.CTkFrame(parent, fg_color=C["bg_card"], corner_radius=8,
                         border_width=1, border_color=color)
        f.grid(row=0, column=col, sticky="ew", padx=(0 if col else 0, 4 if col == 0 else 0),
               pady=2)
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
        Visualisasi: dua panah (pointer) dari kiri (main) dan kanan (branch)
        sama-sama menunjuk ke kotak memori tengah (fork-point address).
        Animasi jitter memberi kesan "perebutan".
        """
        c  = self.conf_canvas
        c.delete("all")
        W  = c.winfo_width()  or 310
        H  = 220
        cx = W // 2
        cy = H // 2

        # Background grid (subtle)
        for x in range(0, W, 24):
            c.create_line(x, 0, x, H, fill="#1F0808", width=1)
        for y in range(0, H, 24):
            c.create_line(0, y, W, y, fill="#1F0808", width=1)

        # ── Fork-point box (tengah) ──────────────────────────────────────────
        bw, bh = 110, 52
        c.create_rectangle(cx-bw//2-2, cy-bh//2-2, cx+bw//2+2, cy+bh//2+2,
                           fill="#3D1A00", outline=C["conf_fork"], width=2)
        c.create_text(cx, cy - 10, text="FORK POINT",
                      fill=C["conf_fork"], font=("JetBrains Mono", 8, "bold"))
        fork_addr = info.head_a.fake_address if info.fork_id is None else \
                    (info.fork_id[:7])
        c.create_text(cx, cy + 8, text=f"id: {info.fork_id or '—'}",
                      fill=C["text_dim"], font=("JetBrains Mono", 8))

        # ── HEAD main (kiri) ─────────────────────────────────────────────────
        jitter = self._ptr_anim_step % 2   # 0 atau 1 → getaran kecil
        lx = 28 + jitter
        c.create_rectangle(lx, cy-22, lx+90, cy+22,
                           fill="#0A1F3D", outline=C["conf_main"], width=2)
        c.create_text(lx+45, cy-8,  text="main HEAD",
                      fill=C["conf_main"], font=("JetBrains Mono", 8, "bold"))
        c.create_text(lx+45, cy+7,  text=f"#{info.head_a.commit_id}",
                      fill=C["text_mono"], font=("JetBrains Mono", 8))
        # Panah main → fork
        c.create_line(lx+90, cy, cx-bw//2, cy,
                      fill=C["conf_main"], width=3,
                      arrow=tk.LAST, arrowshape=(10, 12, 4))
        c.create_text(lx+45, cy+30, text=info.head_a.fake_address,
                      fill=C["text_dim"], font=("JetBrains Mono", 7))

        # ── HEAD branch (kanan) ──────────────────────────────────────────────
        rx = W - 28 - 90 - jitter
        c.create_rectangle(rx, cy-22, rx+90, cy+22,
                           fill="#3D0A0A", outline=C["conf_branch"], width=2)
        c.create_text(rx+45, cy-8,  text=f"{info.branch_b} HEAD",
                      fill=C["conf_branch"], font=("JetBrains Mono", 8, "bold"))
        c.create_text(rx+45, cy+7,  text=f"#{info.head_b.commit_id}",
                      fill=C["text_mono"], font=("JetBrains Mono", 8))
        # Panah branch → fork
        c.create_line(rx, cy, cx+bw//2, cy,
                      fill=C["conf_branch"], width=3,
                      arrow=tk.LAST, arrowshape=(10, 12, 4))
        c.create_text(rx+45, cy+30, text=info.head_b.fake_address,
                      fill=C["text_dim"], font=("JetBrains Mono", 7))

        # ── Clash lightning bolt (tengah atas) ───────────────────────────────
        bolt_color = C["accent3"] if self._ptr_anim_step % 2 == 0 else C["accent4"]
        c.create_text(cx, cy - bh//2 - 20, text="⚡ CONFLICT ⚡",
                      fill=bolt_color, font=("Segoe UI", 10, "bold"))

        # ── Keterangan bawah ─────────────────────────────────────────────────
        c.create_text(cx, H - 14,
                      text="Dua pointer memperebutkan slot memori yang sama",
                      fill=C["text_dim"], font=("Segoe UI", 8))

    def _start_conflict_anim(self):
        """Loop animasi jitter untuk canvas konflik."""
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

        # Swap frames
        self.idle_frame.pack_forget()
        self.resolved_frame.pack_forget()
        self.conflict_frame.pack(fill="both", expand=True)

        # Header
        self.right_panel.configure(fg_color=C["conf_bg"],
                                   border_color=C["conf_border"])
        self.lbl_arena_title.configure(text_color=C["accent3"])
        self.lbl_arena_badge.configure(text=" ⚠ CONFLICT ", fg_color=C["accent3"],
                                       text_color="#0D1117")

        # Update info cards
        self.card_main["id"].configure(text=f"#{info.head_a.commit_id}")
        self.card_main["msg"].configure(text=info.head_a.message)
        self.card_branch["id"].configure(text=f"#{info.head_b.commit_id}")
        self.card_branch["msg"].configure(text=info.head_b.message)
        # Rename branch card label
        for w in self.card_branch["frame"].winfo_children():
            if isinstance(w, ctk.CTkLabel) and w.cget("text") in ("BRANCH", branch_name.upper()):
                w.configure(text=branch_name.upper())
                break

        # Diff view
        self._update_diff(info)

        # Draw canvas
        self.after(80, lambda: self._draw_conflict_canvas(info))
        self._start_conflict_anim()

        self._flash_status("⚠  Konflik terdeteksi! Pilih resolusi di Panel Kanan.",
                           color=C["accent3"])

    def _deactivate_conflict_panel(self, winner_label: str):
        self._stop_conflict_anim()
        self._conflict_branch_name = None

        # Kembali ke tampilan idle
        self.conflict_frame.pack_forget()
        self.right_panel.configure(fg_color=C["bg_mid"],
                                   border_color=C["border"])
        self.lbl_arena_title.configure(text_color=C["text_dim"])
        self.lbl_arena_badge.configure(text="  RESOLVED  ",
                                       fg_color=C["conf_resolved"],
                                       text_color="#0D1117")

        # Tampilkan resolved banner sebentar
        self.lbl_resolved.configure(
            text=f"✔  Konflik diselesaikan\nPemenang: {winner_label}")
        self.resolved_frame.pack(padx=12, pady=8)
        self.idle_frame.pack(fill="both", expand=True)
        # Hilangkan banner setelah 3 detik
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
        content = self.txt_editor.get("1.0", "end-1c")
        message = self.entry_msg.get().strip()
        if not message:
            self._flash_status("⚠  Tulis commit message!", color=C["accent3"])
            self.entry_msg.focus()
            return
        if not content.strip():
            self._flash_status("⚠  Editor kosong!", color=C["accent3"])
            return
        node = self.bm.commit(message, content)
        self.entry_msg.delete(0, "end")
        self._flash_status(f"✔  Commit [{node.commit_id}] — '{message}'",
                           color=C["accent2"])
        self._sync_all(animate_push=True)

    def _on_rewind(self):
        if not self.bm.can_rewind():
            self._flash_status("⚠  Sudah di commit paling awal.", color=C["accent3"])
            return
        self.bm.rewind()
        head = self.bm.top_pointer()
        if head:
            self._set_editor(head.content)
            self._flash_status(f"◀  Rewind → [{head.commit_id}]", color=C["accent4"])
        self._sync_all(animate_pop=True)

    def _on_forward(self):
        if not self.bm.can_forward():
            self._flash_status("⚠  Tidak ada commit untuk di-forward.", color=C["accent3"])
            return
        node = self.bm.forward()
        if node:
            self._set_editor(node.content)
            self._flash_status(f"▶  Forward → [{node.commit_id}]", color=C["accent"])
        self._sync_all()

    def _on_slider(self, val):
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
        name = simpledialog.askstring("New Branch", "Nama branch baru:", parent=self)
        if not name:
            return
        name = name.strip().replace(" ", "-").lower()
        if self.bm.create_branch(name):
            self.bm.switch_branch(name)
            self._update_branch_selector()
            self._flash_status(f"⎇  Branch [{name}] dibuat & aktif.", color=C["accent"])
            self._sync_all()
        else:
            self._flash_status(f"⚠  Branch '{name}' sudah ada.", color=C["accent3"])

    def _on_switch_branch(self, name: str):
        if self.bm.switch_branch(name):
            head = self.bm.top_pointer()
            if head:
                self._set_editor(head.content)
            self._flash_status(f"⎇  Pindah ke [{name}]", color=C["accent"])
            self._sync_all()

    def _on_merge(self):
        branches = [b for b in self.bm.branch_names if b != "main"]
        if not branches:
            self._flash_status("⚠  Tidak ada branch lain untuk di-merge.",
                               color=C["accent3"])
            return
        src = branches[0] if len(branches) == 1 else simpledialog.askstring(
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
    # SYNC & HELPERS
    # ══════════════════════════════════════════════════════════════════════════
    def _sync_all(self, animate_push=False, animate_pop=False):
        self._render_stack_panel()
        self._render_timeline()
        self._update_slider()
        self._update_buttons()
        if animate_push:
            self.after(50, self._flash_top_card, C["accent2"])
        if animate_pop:
            self.after(50, self._flash_top_card, C["accent4"])

    def _update_buttons(self):
        self.btn_rewind.configure(
            state="normal" if self.bm.can_rewind()  else "disabled")
        self.btn_forward.configure(
            state="normal" if self.bm.can_forward() else "disabled")

    def _update_slider(self):
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
        self.cb_branch.configure(values=self.bm.branch_names)
        self.var_branch.set(self.bm.active_branch)

    def _set_editor(self, content: str):
        self.txt_editor.delete("1.0", "end")
        self.txt_editor.insert("1.0", content)

    def _flash_top_card(self, color: str):
        cards = self.stack_scroll.winfo_children()
        if cards:
            try:
                cards[0].configure(fg_color=color)
                self.after(350, lambda: cards[0].configure(fg_color="#1A1060"))
            except Exception:
                pass

    def _flash_status(self, msg: str, color: str = None):
        self.lbl_status.configure(text=f"  {msg}",
                                  text_color=color or C["text_dim"])


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = GitFlowSimApp()
    app.after(120, app._render_timeline)
    app.mainloop()
