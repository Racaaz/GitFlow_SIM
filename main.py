"""
GitFlow Sim - TAHAP 2: GUI Utama
Panel Kiri  : Memory & Stack Monitor
Panel Tengah: Time-Travel Visualizer & Input
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, simpledialog
from backend import BranchManager, CommitNode

# ── Tema Global ────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Palet Warna (terminal/dev aesthetic)
C = {
    "bg_dark":    "#0D1117",
    "bg_mid":     "#161B22",
    "bg_card":    "#1C2128",
    "border":     "#30363D",
    "accent":     "#58A6FF",       # biru GitHub
    "accent2":    "#3FB950",       # hijau commit
    "accent3":    "#F85149",       # merah konflik
    "accent4":    "#D29922",       # kuning rollback
    "top_ptr":    "#BC8CFF",       # ungu untuk TOP POINTER
    "text":       "#E6EDF3",
    "text_dim":   "#8B949E",
    "text_mono":  "#79C0FF",
}

FONT_MONO  = ("JetBrains Mono", 11)
FONT_MONO_SM = ("JetBrains Mono", 9)
FONT_LABEL = ("Segoe UI", 11)
FONT_BOLD  = ("Segoe UI", 11, "bold")
FONT_TITLE = ("Segoe UI", 13, "bold")


# ══════════════════════════════════════════════════════════════════════════════
# CLASS UTAMA GUI
# ══════════════════════════════════════════════════════════════════════════════
class GitFlowSimApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("GitFlow Sim  •  Interactive Data Structure Simulator")
        self.geometry("1280x760")
        self.minsize(1100, 680)
        self.configure(fg_color=C["bg_dark"])

        # — Backend —
        self.bm = BranchManager()
        # Buat 1 commit awal agar stack tidak kosong
        self.bm.commit("Initial commit", "# Selamat datang di GitFlow Sim!\n\nMulai edit dan commit file Anda di sini.")

        # — State —
        self._anim_after_id = None      # untuk animasi (after ID)
        self._highlighted_card = None   # card yang sedang di-highlight

        # — Build UI —
        self._build_topbar()
        self._build_main_layout()
        self._build_left_panel()
        self._build_center_panel()
        self._build_right_placeholder()

        # — Sinkronisasi awal —
        self._sync_all()

    # ══════════════════════════════════════════════════════════════════════
    # TOP BAR
    # ══════════════════════════════════════════════════════════════════════
    def _build_topbar(self):
        bar = ctk.CTkFrame(self, fg_color=C["bg_mid"], corner_radius=0, height=48)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        # Logo / judul
        ctk.CTkLabel(
            bar, text="⬡  GitFlow Sim",
            font=("Segoe UI", 15, "bold"), text_color=C["accent"]
        ).pack(side="left", padx=20, pady=10)

        ctk.CTkLabel(
            bar, text="Interactive Data Structure & Version Control Simulator",
            font=("Segoe UI", 10), text_color=C["text_dim"]
        ).pack(side="left", padx=4)

        # Branch selector (kanan)
        ctk.CTkLabel(bar, text="Branch:", font=FONT_LABEL,
                     text_color=C["text_dim"]).pack(side="right", padx=(0,6))
        self.var_branch = tk.StringVar(value="main")
        self.cb_branch = ctk.CTkComboBox(
            bar, variable=self.var_branch, values=["main"],
            width=140, font=FONT_MONO,
            command=self._on_switch_branch,
            fg_color=C["bg_card"], border_color=C["border"],
            button_color=C["accent"], dropdown_fg_color=C["bg_mid"]
        )
        self.cb_branch.pack(side="right", padx=6)
        ctk.CTkLabel(bar, text="Active:", font=FONT_LABEL,
                     text_color=C["text_dim"]).pack(side="right")

    # ══════════════════════════════════════════════════════════════════════
    # LAYOUT UTAMA (3 kolom)
    # ══════════════════════════════════════════════════════════════════════
    def _build_main_layout(self):
        self.main_frame = ctk.CTkFrame(self, fg_color=C["bg_dark"])
        self.main_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.main_frame.columnconfigure(0, weight=3, minsize=280)   # kiri
        self.main_frame.columnconfigure(1, weight=5, minsize=420)   # tengah
        self.main_frame.columnconfigure(2, weight=4, minsize=300)   # kanan
        self.main_frame.rowconfigure(0, weight=1)

    # ══════════════════════════════════════════════════════════════════════
    # PANEL KIRI  — Memory & Stack Monitor
    # ══════════════════════════════════════════════════════════════════════
    def _build_left_panel(self):
        outer = ctk.CTkFrame(self.main_frame, fg_color=C["bg_mid"],
                             corner_radius=10, border_width=1, border_color=C["border"])
        outer.grid(row=0, column=0, sticky="nsew", padx=(0,4), pady=0)

        # Header
        hdr = ctk.CTkFrame(outer, fg_color="transparent")
        hdr.pack(fill="x", padx=12, pady=(12,0))
        ctk.CTkLabel(hdr, text="▥  Memory & Stack Monitor",
                     font=FONT_TITLE, text_color=C["accent"]).pack(side="left")

        # Label info
        self.lbl_stack_info = ctk.CTkLabel(
            outer, text="", font=FONT_MONO_SM, text_color=C["text_dim"]
        )
        self.lbl_stack_info.pack(anchor="w", padx=14)

        # Divider
        ctk.CTkFrame(outer, height=1, fg_color=C["border"]).pack(fill="x", padx=12, pady=6)

        # Scrollable area untuk kartu stack
        self.stack_scroll = ctk.CTkScrollableFrame(
            outer, fg_color="transparent", scrollbar_button_color=C["border"]
        )
        self.stack_scroll.pack(fill="both", expand=True, padx=10, pady=(0,10))

        # Legend bawah
        leg = ctk.CTkFrame(outer, fg_color="transparent")
        leg.pack(fill="x", padx=12, pady=(0,10))
        for color, label in [(C["top_ptr"], "TOP PTR"), (C["accent2"], "Commit"),
                             (C["accent4"], "Rolled back")]:
            dot = ctk.CTkLabel(leg, text="●", font=("Segoe UI", 14), text_color=color)
            dot.pack(side="left")
            ctk.CTkLabel(leg, text=f" {label}  ", font=("Segoe UI", 9),
                         text_color=C["text_dim"]).pack(side="left")

    def _render_stack_panel(self):
        """Hapus dan render ulang seluruh stack cards."""
        for w in self.stack_scroll.winfo_children():
            w.destroy()

        nodes = self.bm.stack_snapshot()          # [TOP, ..., BOTTOM]
        rollback_count = self.bm.rollback_count()

        # Info header
        self.lbl_stack_info.configure(
            text=f"  Stack size: {len(nodes)}   Rollback buffer: {rollback_count}"
        )

        if not nodes:
            ctk.CTkLabel(self.stack_scroll, text="Stack kosong",
                         text_color=C["text_dim"]).pack(pady=20)
            return

        for idx, node in enumerate(nodes):
            is_top = (idx == 0)
            self._make_stack_card(node, is_top, idx)

        # Rollback "ghost" cards
        rb_nodes = self.bm.current_rollback().to_list()
        if rb_nodes:
            ctk.CTkLabel(self.stack_scroll, text="── Rollback Buffer ──",
                         font=FONT_MONO_SM, text_color=C["accent4"]).pack(pady=(8,2))
            for node in rb_nodes:
                self._make_stack_card(node, False, -1, ghost=True)

    def _make_stack_card(self, node: CommitNode, is_top: bool,
                         idx: int, ghost: bool = False):
        """Buat satu kartu commit di stack panel."""
        border_color = C["top_ptr"] if is_top else (C["accent4"] if ghost else C["border"])
        bg_color     = "#1A1060" if is_top else (C["bg_dark"] if ghost else C["bg_card"])
        alpha_text   = C["text_dim"] if ghost else C["text"]

        card = ctk.CTkFrame(
            self.stack_scroll,
            fg_color=bg_color,
            corner_radius=6,
            border_width=2 if is_top else 1,
            border_color=border_color
        )
        card.pack(fill="x", pady=3, padx=2)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=6)

        # Baris 1: TOP POINTER badge + commit id
        row1 = ctk.CTkFrame(inner, fg_color="transparent")
        row1.pack(fill="x")

        if is_top:
            ctk.CTkLabel(row1, text="[ TOP PTR ]",
                         font=("JetBrains Mono", 9, "bold"),
                         text_color=C["top_ptr"],
                         fg_color="#2A1A6A", corner_radius=4
                         ).pack(side="left", padx=(0,6))

        ctk.CTkLabel(
            row1, text=f"#{node.commit_id}",
            font=("JetBrains Mono", 10, "bold"),
            text_color=C["text_mono"] if not ghost else C["accent4"]
        ).pack(side="left")

        ctk.CTkLabel(
            row1, text=node.timestamp,
            font=FONT_MONO_SM, text_color=C["text_dim"]
        ).pack(side="right")

        # Baris 2: pesan commit
        ctk.CTkLabel(
            inner, text=node.message,
            font=("Segoe UI", 10), text_color=alpha_text,
            anchor="w", wraplength=210
        ).pack(fill="x", pady=(2,0))

        # Baris 3: alamat memori
        addr_row = ctk.CTkFrame(inner, fg_color="transparent")
        addr_row.pack(fill="x", pady=(2,0))
        ctk.CTkLabel(
            addr_row, text=f"addr: {node.fake_address}",
            font=FONT_MONO_SM, text_color="#3FB950" if not ghost else C["text_dim"]
        ).pack(side="left")

        # Pointer arrow ke bawah
        if not ghost:
            next_node = node.prev
            if next_node:
                ctk.CTkLabel(
                    addr_row,
                    text=f"→ prev: {next_node.fake_address}",
                    font=FONT_MONO_SM, text_color=C["text_dim"]
                ).pack(side="left", padx=6)
            else:
                ctk.CTkLabel(
                    addr_row, text="→ prev: NULL",
                    font=FONT_MONO_SM, text_color=C["accent3"]
                ).pack(side="left", padx=6)

        # Arrow connector (bukan untuk card terakhir)
        nodes = self.bm.stack_snapshot()
        if not ghost and idx < len(nodes) - 1:
            ctk.CTkLabel(
                self.stack_scroll, text="▼",
                font=("Segoe UI", 12), text_color=C["border"]
            ).pack()

    # ══════════════════════════════════════════════════════════════════════
    # PANEL TENGAH  — Time-Travel Visualizer & Input
    # ══════════════════════════════════════════════════════════════════════
    def _build_center_panel(self):
        outer = ctk.CTkFrame(self.main_frame, fg_color=C["bg_mid"],
                             corner_radius=10, border_width=1, border_color=C["border"])
        outer.grid(row=0, column=1, sticky="nsew", padx=4, pady=0)

        # ── Header ──────────────────────────────
        hdr = ctk.CTkFrame(outer, fg_color="transparent")
        hdr.pack(fill="x", padx=12, pady=(12, 0))
        ctk.CTkLabel(hdr, text="⏱  Time-Travel Visualizer",
                     font=FONT_TITLE, text_color=C["accent"]).pack(side="left")

        ctk.CTkFrame(outer, height=1, fg_color=C["border"]).pack(fill="x", padx=12, pady=6)

        # ── Editor simulasi file ─────────────────
        ctk.CTkLabel(outer, text="  📄 Simulasi Isi File",
                     font=FONT_BOLD, text_color=C["text"]).pack(anchor="w", padx=12)

        self.txt_editor = ctk.CTkTextbox(
            outer, height=160, font=FONT_MONO,
            fg_color=C["bg_dark"], text_color=C["text"],
            border_color=C["border"], border_width=1,
            wrap="word"
        )
        self.txt_editor.pack(fill="x", padx=12, pady=(4, 8))

        # ── Commit Section ───────────────────────
        commit_frame = ctk.CTkFrame(outer, fg_color=C["bg_card"],
                                    corner_radius=8, border_width=1,
                                    border_color=C["border"])
        commit_frame.pack(fill="x", padx=12, pady=(0,10))

        ctk.CTkLabel(commit_frame, text="  ✎  Commit",
                     font=FONT_BOLD, text_color=C["accent2"]).pack(anchor="w", padx=10, pady=(8,2))

        self.entry_msg = ctk.CTkEntry(
            commit_frame,
            placeholder_text="Tulis commit message...",
            font=FONT_MONO,
            fg_color=C["bg_dark"], border_color=C["border"],
            text_color=C["text"]
        )
        self.entry_msg.pack(fill="x", padx=10, pady=(0,6))

        btn_row = ctk.CTkFrame(commit_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=(0,8))

        self.btn_commit = ctk.CTkButton(
            btn_row, text="⬡  Commit",
            font=FONT_BOLD, fg_color=C["accent2"], hover_color="#2EA043",
            text_color="#0D1117", corner_radius=6, width=110,
            command=self._on_commit
        )
        self.btn_commit.pack(side="left", padx=(0,6))

        self.btn_new_branch = ctk.CTkButton(
            btn_row, text="⎇  New Branch",
            font=FONT_BOLD, fg_color=C["bg_mid"], hover_color=C["border"],
            text_color=C["accent"], corner_radius=6, width=130,
            border_width=1, border_color=C["accent"],
            command=self._on_new_branch
        )
        self.btn_new_branch.pack(side="left", padx=(0,6))

        self.btn_merge = ctk.CTkButton(
            btn_row, text="↩  Merge",
            font=FONT_BOLD, fg_color=C["bg_mid"], hover_color=C["border"],
            text_color=C["accent4"], corner_radius=6, width=100,
            border_width=1, border_color=C["accent4"],
            command=self._on_merge
        )
        self.btn_merge.pack(side="left")

        # ── Timeline ─────────────────────────────
        ctk.CTkFrame(outer, height=1, fg_color=C["border"]).pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(outer, text="  ◈  Commit Timeline",
                     font=FONT_BOLD, text_color=C["text"]).pack(anchor="w", padx=12)

        self.timeline_canvas = tk.Canvas(
            outer, height=90, bg=C["bg_dark"],
            highlightthickness=0, bd=0
        )
        self.timeline_canvas.pack(fill="x", padx=12, pady=(4,4))

        # ── Time-Travel Controls ──────────────────
        ctk.CTkFrame(outer, height=1, fg_color=C["border"]).pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(outer, text="  ◀▶  Time Travel Controls",
                     font=FONT_BOLD, text_color=C["text"]).pack(anchor="w", padx=12)

        ctrl = ctk.CTkFrame(outer, fg_color="transparent")
        ctrl.pack(fill="x", padx=12, pady=(4,8))

        self.btn_rewind = ctk.CTkButton(
            ctrl, text="◀  Rewind",
            font=FONT_BOLD, fg_color=C["accent4"], hover_color="#B07900",
            text_color="#0D1117", corner_radius=6, width=110,
            command=self._on_rewind
        )
        self.btn_rewind.pack(side="left", padx=(0,8))

        self.btn_forward = ctk.CTkButton(
            ctrl, text="Forward  ▶",
            font=FONT_BOLD, fg_color=C["accent"], hover_color="#1A7FD4",
            text_color="#0D1117", corner_radius=6, width=110,
            command=self._on_forward
        )
        self.btn_forward.pack(side="left", padx=(0,12))

        # Slider — JANGAN set variable saat init dengan from_==to (ZeroDivisionError)
        # Gunakan range dummy (0–100) dulu, update lewat _update_slider()
        self.var_slider = tk.DoubleVar(value=100.0)
        self.slider = ctk.CTkSlider(
            ctrl,
            from_=0, to=100,          # range valid agar tidak ZeroDivisionError
            command=self._on_slider,
            button_color=C["accent"],
            progress_color=C["accent4"],
            fg_color=C["border"],
        )
        self.slider.set(100)
        self.slider.pack(side="left", fill="x", expand=True, padx=4)

        # Status bar
        self.lbl_status = ctk.CTkLabel(
            outer, text="",
            font=FONT_MONO_SM, text_color=C["text_dim"],
            anchor="w"
        )
        self.lbl_status.pack(fill="x", padx=14, pady=(0,8))

    def _render_timeline(self):
        """Gambar ulang garis waktu commit di canvas."""
        c = self.timeline_canvas
        c.delete("all")

        nodes = self.bm.stack_snapshot()
        nodes_ordered = list(reversed(nodes))   # urutan waktu (lama → baru)
        total = len(nodes_ordered)
        if total == 0:
            return

        w = c.winfo_width() or 400
        h = 90
        margin_x = 40
        step = (w - 2*margin_x) / max(total - 1, 1)
        cy = h // 2

        for i, node in enumerate(nodes_ordered):
            x = margin_x + i * step
            is_head = (i == total - 1)    # HEAD = kanan paling ujung

            # Garis penghubung ke node sebelumnya
            if i > 0:
                prev_x = margin_x + (i-1) * step
                c.create_line(prev_x+14, cy, x-14, cy,
                              fill=C["border"], width=2, dash=(4,3))

            # Lingkaran node
            r = 14 if is_head else 10
            fill = C["top_ptr"] if is_head else C["accent2"]
            c.create_oval(x-r, cy-r, x+r, cy+r,
                          fill=fill, outline="#FFFFFF" if is_head else fill, width=2)

            # Commit ID
            c.create_text(x, cy,
                          text=node.commit_id[:4],
                          fill="#0D1117" if is_head else C["bg_dark"],
                          font=("JetBrains Mono", 8, "bold"))

            # Label bawah (pesan, dipotong)
            msg = node.message[:12] + "…" if len(node.message) > 12 else node.message
            c.create_text(x, cy+r+14,
                          text=msg,
                          fill=C["text_dim"],
                          font=("Segoe UI", 8))

            # HEAD badge
            if is_head:
                c.create_text(x, cy-r-10,
                              text="HEAD", fill=C["top_ptr"],
                              font=("JetBrains Mono", 9, "bold"))

        # Tambahkan ghost (rolled-back) node dengan warna redup
        rb_nodes = list(reversed(self.bm.current_rollback().to_list()))
        for j, node in enumerate(rb_nodes):
            i2 = total + j
            x = margin_x + i2 * step
            if x > w - 10:
                break
            c.create_line(margin_x + (i2-1)*step + 14, cy, x-14, cy,
                          fill=C["accent4"], width=1, dash=(2,4))
            c.create_oval(x-8, cy-8, x+8, cy+8,
                          fill="", outline=C["accent4"], width=1, dash=(2,2))
            c.create_text(x, cy, text=node.commit_id[:4],
                          fill=C["accent4"], font=("JetBrains Mono", 8))

    # ══════════════════════════════════════════════════════════════════════
    # PANEL KANAN — placeholder (Conflict Arena, TAHAP 3)
    # ══════════════════════════════════════════════════════════════════════
    def _build_right_placeholder(self):
        self.right_panel = ctk.CTkFrame(
            self.main_frame, fg_color=C["bg_mid"],
            corner_radius=10, border_width=1, border_color=C["border"]
        )
        self.right_panel.grid(row=0, column=2, sticky="nsew", padx=(4,0), pady=0)

        inner = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(inner, text="⚠", font=("Segoe UI", 40),
                     text_color=C["border"]).pack()
        ctk.CTkLabel(inner, text="Conflict Arena",
                     font=("Segoe UI", 15, "bold"), text_color=C["text_dim"]).pack()
        ctk.CTkLabel(inner, text="Merge two branches dengan\nkonflik untuk mengaktifkan panel ini.",
                     font=("Segoe UI", 10), text_color=C["border"],
                     justify="center").pack(pady=6)

        self.lbl_conflict_status = ctk.CTkLabel(
            inner, text="Status: Tidak ada konflik",
            font=FONT_MONO_SM, text_color=C["text_dim"]
        )
        self.lbl_conflict_status.pack()

        # Conflict resolve buttons (awalnya disable)
        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(pady=8)

        self.btn_keep_main = ctk.CTkButton(
            btn_row, text="Keep Main",
            font=FONT_BOLD, fg_color=C["accent"], width=120,
            state="disabled", command=lambda: self._resolve_conflict(keep_main=True)
        )
        self.btn_keep_main.pack(side="left", padx=4)

        self.btn_keep_branch = ctk.CTkButton(
            btn_row, text="Accept Branch",
            font=FONT_BOLD, fg_color=C["accent3"], width=120,
            state="disabled", command=lambda: self._resolve_conflict(keep_main=False)
        )
        self.btn_keep_branch.pack(side="left", padx=4)

        self._conflict_branch_name = None   # branch yang sedang dalam konflik

    # ══════════════════════════════════════════════════════════════════════
    # EVENT HANDLERS
    # ══════════════════════════════════════════════════════════════════════
    def _on_commit(self):
        content = self.txt_editor.get("1.0", "end-1c")
        message = self.entry_msg.get().strip()

        if not message:
            self._flash_status("⚠  Tulis commit message terlebih dahulu!", color=C["accent3"])
            self.entry_msg.focus()
            return
        if not content.strip():
            self._flash_status("⚠  Isi editor tidak boleh kosong!", color=C["accent3"])
            return

        node = self.bm.commit(message, content)
        self.entry_msg.delete(0, "end")
        self._flash_status(f"✔  Commit [{node.commit_id}] berhasil — '{message}'",
                           color=C["accent2"])
        self._sync_all(animate_push=True)

    def _on_rewind(self):
        if not self.bm.can_rewind():
            self._flash_status("⚠  Tidak bisa rewind lebih jauh (minimal 1 commit).",
                               color=C["accent3"])
            return
        node = self.bm.rewind()
        if node:
            # Tampilkan konten commit sebelumnya (HEAD baru setelah pop)
            head = self.bm.top_pointer()
            if head:
                self._set_editor(head.content)
            self._flash_status(f"◀  Rewind — kembali ke [{head.commit_id if head else '?'}]",
                               color=C["accent4"])
        self._sync_all(animate_pop=True)

    def _on_forward(self):
        if not self.bm.can_forward():
            self._flash_status("⚠  Tidak ada commit untuk di-forward.", color=C["accent3"])
            return
        node = self.bm.forward()
        if node:
            self._set_editor(node.content)
            self._flash_status(f"▶  Forward — kembali ke [{node.commit_id}]",
                               color=C["accent"])
        self._sync_all()

    def _on_slider(self, val):
        """Slider menggerakkan time travel secara absolut."""
        stack_size = self.bm.current_stack().size()
        rb_size = self.bm.current_rollback().size()
        total = stack_size + rb_size
        if total <= 1:
            return

        target_pos = int(float(val))           # posisi yang diinginkan (1 = paling lama)
        current_pos = stack_size               # posisi HEAD saat ini

        if target_pos < current_pos:
            # Perlu rewind
            steps = current_pos - target_pos
            for _ in range(steps):
                if not self.bm.can_rewind():
                    break
                self.bm.rewind()
        elif target_pos > current_pos:
            # Perlu forward
            steps = target_pos - current_pos
            for _ in range(steps):
                if not self.bm.can_forward():
                    break
                self.bm.forward()

        head = self.bm.top_pointer()
        if head:
            self._set_editor(head.content)
            self._flash_status(f"◈  Time travel → commit [{head.commit_id}]",
                               color=C["accent"])
        self._sync_all()

    def _on_new_branch(self):
        name = simpledialog.askstring(
            "New Branch", "Nama branch baru:",
            parent=self
        )
        if not name:
            return
        name = name.strip().replace(" ", "-").lower()
        if not name:
            return
        ok = self.bm.create_branch(name)
        if ok:
            self.bm.switch_branch(name)
            self._update_branch_selector()
            self._flash_status(f"⎇  Branch [{name}] dibuat & aktif.", color=C["accent"])
            self._sync_all()
        else:
            self._flash_status(f"⚠  Branch '{name}' sudah ada.", color=C["accent3"])

    def _on_switch_branch(self, name: str):
        ok = self.bm.switch_branch(name)
        if ok:
            head = self.bm.top_pointer()
            if head:
                self._set_editor(head.content)
            self._flash_status(f"⎇  Pindah ke branch [{name}]", color=C["accent"])
            self._sync_all()

    def _on_merge(self):
        branches = [b for b in self.bm.branch_names if b != "main"]
        if not branches:
            self._flash_status("⚠  Tidak ada branch lain untuk di-merge.", color=C["accent3"])
            return

        # Pilih branch source (jika lebih dari 1, tanya user)
        if len(branches) == 1:
            src = branches[0]
        else:
            src = simpledialog.askstring(
                "Merge Branch",
                f"Nama branch yang ingin di-merge ke main:\n{', '.join(branches)}",
                parent=self
            )
            if not src or src not in branches:
                return

        has_conflict = self.bm.detect_conflict(src)
        if has_conflict:
            self._activate_conflict_panel(src)
        else:
            # Merge otomatis tanpa konflik
            self.bm.switch_branch("main")
            result = self.bm.merge(src, keep_main=True)
            self._update_branch_selector()
            self._flash_status(f"↩  Merge [{src}] → main selesai (no conflict).",
                               color=C["accent2"])
            self._sync_all()

    def _activate_conflict_panel(self, branch_name: str):
        """Aktifkan Conflict Arena dengan visual peringatan."""
        self._conflict_branch_name = branch_name
        self.right_panel.configure(border_color=C["accent3"])
        self.lbl_conflict_status.configure(
            text=f"⚠  KONFLIK: main vs {branch_name}",
            text_color=C["accent3"]
        )
        self.btn_keep_main.configure(state="normal")
        self.btn_keep_branch.configure(state="normal")
        self._flash_status(f"⚠  Konflik terdeteksi! Pilih resolusi di Panel Kanan.",
                           color=C["accent3"])
        # Kedip merah
        self._blink_conflict(3)

    def _blink_conflict(self, times: int):
        if times <= 0:
            return
        current = self.right_panel.cget("fg_color")
        next_color = "#2A0A0A" if current == C["bg_mid"] else C["bg_mid"]
        self.right_panel.configure(fg_color=next_color)
        self.after(400, lambda: self._blink_conflict(times - 1))

    def _resolve_conflict(self, keep_main: bool):
        src = self._conflict_branch_name
        if not src:
            return
        self.bm.switch_branch("main")
        self.bm.merge(src, keep_main=keep_main)
        self._update_branch_selector()
        self.right_panel.configure(fg_color=C["bg_mid"], border_color=C["border"])
        self.lbl_conflict_status.configure(
            text="Status: Konflik selesai ✔", text_color=C["accent2"]
        )
        self.btn_keep_main.configure(state="disabled")
        self.btn_keep_branch.configure(state="disabled")
        self._conflict_branch_name = None
        head = self.bm.top_pointer()
        if head:
            self._set_editor(head.content)
        self._flash_status("✔  Konflik berhasil diselesaikan.", color=C["accent2"])
        self._sync_all()

    # ══════════════════════════════════════════════════════════════════════
    # SINKRONISASI & ANIMASI
    # ══════════════════════════════════════════════════════════════════════
    def _sync_all(self, animate_push=False, animate_pop=False):
        """Update seluruh UI sesuai state backend."""
        self._render_stack_panel()
        self._render_timeline()
        self._update_slider()
        self._update_buttons()

        if animate_push:
            self.after(50, self._flash_top_card, C["accent2"])
        if animate_pop:
            self.after(50, self._flash_top_card, C["accent4"])

    def _update_buttons(self):
        self.btn_rewind.configure(state="normal" if self.bm.can_rewind() else "disabled")
        self.btn_forward.configure(state="normal" if self.bm.can_forward() else "disabled")

    def _update_slider(self):
        stack_size = self.bm.current_stack().size()
        rb_size = self.bm.current_rollback().size()
        total = stack_size + rb_size
        if total > 1:
            # Pastikan from_ < to agar tidak ZeroDivisionError di CTkSlider
            self.slider.configure(from_=1, to=float(total))
            self.slider.set(float(stack_size))
        else:
            # Saat hanya 1 commit: gunakan range 0–100 dummy, posisikan di ujung
            self.slider.configure(from_=0, to=100)
            self.slider.set(100)

    def _update_branch_selector(self):
        names = self.bm.branch_names
        self.cb_branch.configure(values=names)
        self.var_branch.set(self.bm.active_branch)

    def _set_editor(self, content: str):
        self.txt_editor.delete("1.0", "end")
        self.txt_editor.insert("1.0", content)

    def _flash_top_card(self, color: str):
        """Highlight singkat kartu TOP di stack panel (animasi push/pop)."""
        cards = self.stack_scroll.winfo_children()
        if cards:
            card = cards[0]
            try:
                card.configure(fg_color=color)
                self.after(350, lambda: card.configure(fg_color="#1A1060"))
            except Exception:
                pass

    def _flash_status(self, msg: str, color: str = None):
        self.lbl_status.configure(
            text=f"  {msg}",
            text_color=color or C["text_dim"]
        )


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = GitFlowSimApp()
    # Render timeline setelah window siap (agar ukuran canvas diketahui)
    app.after(100, app._render_timeline)
    app.mainloop()