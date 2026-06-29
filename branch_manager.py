"""
core/branch_manager.py
======================
BranchManager — Mengelola semua Branch, Active Branch Pointer,
operasi merge, dan deteksi konflik.

Konsep pointer yang didemonstrasikan:
  - active_branch_pointer  : menunjuk Branch yang sedang aktif
  - branch_origin_pointer  : menunjuk CommitNode titik percabangan sebuah Branch
  - conflict_pointer_main  : penunjuk commit konflik di Main Branch
  - conflict_pointer_other : penunjuk commit konflik di Branch lain
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Tuple
from .commit import CommitNode
from .stack import CommitStack, RollbackStack


# ──────────────────────────────────────────────────────────────────────────────
# DATA CLASS: Branch
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class Branch:
    """
    Representasi sebuah branch dalam sistem version control.

    Attributes
    ----------
    name            : str          — Nama branch (misal: 'main', 'feature-x')
    commit_stack    : CommitStack  — Stack commit milik branch ini
    rollback_stack  : RollbackStack— Stack undo/redo milik branch ini
    origin_commit   : CommitNode | None — Titik percabangan (branch point)
    color           : str          — Warna hex untuk visualisasi timeline
    """
    name: str
    commit_stack: CommitStack = field(default_factory=lambda: CommitStack(""))
    rollback_stack: RollbackStack = field(default_factory=RollbackStack)
    origin_commit: Optional[CommitNode] = None
    color: str = "#4A9EFF"

    def __post_init__(self):
        self.commit_stack.name = self.name

    @property
    def head(self) -> Optional[CommitNode]:
        """Commit terbaru (HEAD) dari branch ini."""
        return self.commit_stack.peek()

    @property
    def history(self) -> List[CommitNode]:
        """Seluruh riwayat commit dari terlama ke terbaru."""
        return self.commit_stack.to_list()

    def __repr__(self) -> str:
        return f"Branch(name={self.name!r}, commits={self.commit_stack.size})"


# ──────────────────────────────────────────────────────────────────────────────
# DATA CLASS: ConflictState
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ConflictState:
    """
    Menyimpan state saat konflik merge terjadi.

    Dua pointer menunjuk ke commit yang berkonflik dari masing-masing branch.
    """
    is_active: bool = False
    main_branch_name: str = ""
    other_branch_name: str = ""
    conflict_pointer_main: Optional[CommitNode] = None    # ← pointer konflik Main
    conflict_pointer_other: Optional[CommitNode] = None   # ← pointer konflik Other
    conflicting_lines: List[int] = field(default_factory=list)

    def activate(self, main_branch: str, other_branch: str,
                 main_commit: CommitNode, other_commit: CommitNode) -> None:
        self.is_active = True
        self.main_branch_name = main_branch
        self.other_branch_name = other_branch
        self.conflict_pointer_main = main_commit
        self.conflict_pointer_other = other_commit

    def resolve(self) -> None:
        self.is_active = False
        self.conflict_pointer_main = None
        self.conflict_pointer_other = None
        self.conflicting_lines.clear()

    def __repr__(self) -> str:
        return (f"ConflictState(active={self.is_active}, "
                f"main={self.main_branch_name!r}, "
                f"other={self.other_branch_name!r})")


# ──────────────────────────────────────────────────────────────────────────────
# BRANCH MANAGER
# ──────────────────────────────────────────────────────────────────────────────

# Palet warna untuk branch baru (bergilir)
BRANCH_COLORS = [
    "#4A9EFF",   # biru (main)
    "#FF6B9D",   # pink
    "#50FA7B",   # hijau
    "#FFB86C",   # oranye
    "#BD93F9",   # ungu
    "#FF5555",   # merah
    "#8BE9FD",   # cyan
    "#F1FA8C",   # kuning
]


class BranchManager:
    """
    Mengelola keseluruhan sistem branching GitFlow Sim.

    Tanggung Jawab
    --------------
    1. Membuat branch baru (clone dari titik HEAD saat ini)
    2. Memindahkan active_branch_pointer antar branch
    3. Menambahkan commit ke branch aktif
    4. Operasi time-travel (rewind/forward) via rollback stack
    5. Mendeteksi dan menyelesaikan konflik merge
    6. Menyediakan data snapshot untuk GUI
    """

    def __init__(self):
        # ── Daftar semua branch ────────────────────────────────────────────────
        self._branches: Dict[str, Branch] = {}

        # ── ACTIVE BRANCH POINTER ─────────────────────────────────────────────
        self._active_branch_pointer: Optional[Branch] = None

        # ── State konflik ─────────────────────────────────────────────────────
        self.conflict_state: ConflictState = ConflictState()

        # ── Inisialisasi branch 'main' ────────────────────────────────────────
        self._color_index: int = 0
        self._init_main_branch()

    # ── Setup Awal ─────────────────────────────────────────────────────────────

    def _init_main_branch(self) -> None:
        """Buat branch 'main' sebagai branch default."""
        main = Branch(
            name="main",
            color=BRANCH_COLORS[self._color_index % len(BRANCH_COLORS)]
        )
        self._color_index += 1
        self._branches["main"] = main
        self._active_branch_pointer = main   # ← set active pointer ke main

        # Commit awal otomatis
        initial_commit = CommitNode(
            message="Initial commit",
            content="# GitFlow Sim\n\nSelamat datang di repositori simulasi ini.\nMulailah dengan mengetik konten dan membuat commit!",
            branch_name="main"
        )
        main.commit_stack.push(initial_commit)

    # ── Properti Aktif ─────────────────────────────────────────────────────────

    @property
    def active_branch(self) -> Branch:
        """Branch yang sedang aktif (tidak boleh None setelah init)."""
        if self._active_branch_pointer is None:
            raise RuntimeError("active_branch_pointer is NULL — sistem tidak valid.")
        return self._active_branch_pointer

    @property
    def active_branch_name(self) -> str:
        return self.active_branch.name

    @property
    def all_branch_names(self) -> List[str]:
        return list(self._branches.keys())

    @property
    def branch_count(self) -> int:
        return len(self._branches)

    # ── Operasi Branch ─────────────────────────────────────────────────────────

    def create_branch(self, name: str) -> Tuple[bool, str]:
        """
        Buat branch baru dari titik HEAD branch aktif saat ini.

        Returns
        -------
        (True, pesan sukses) atau (False, pesan error)
        """
        name = name.strip()

        if not name:
            return False, "Nama branch tidak boleh kosong."
        if name in self._branches:
            return False, f"Branch '{name}' sudah ada."
        if ' ' in name:
            return False, "Nama branch tidak boleh mengandung spasi."

        # Simpan origin commit (titik percabangan)
        origin = self.active_branch.head

        # Buat branch baru
        new_branch = Branch(
            name=name,
            color=BRANCH_COLORS[self._color_index % len(BRANCH_COLORS)],
            origin_commit=origin
        )
        self._color_index += 1

        # Clone riwayat commit dari branch aktif
        new_branch.commit_stack.clone_from(self.active_branch.commit_stack)

        self._branches[name] = new_branch
        return True, f"Branch '{name}' berhasil dibuat dari '{self.active_branch_name}' @ {origin.short_id if origin else 'kosong'}."

    def switch_branch(self, name: str) -> Tuple[bool, str]:
        """
        Pindahkan active_branch_pointer ke branch yang dituju.

        Catatan: rollback stack branch lama dibersihkan saat berpindah
        untuk menghindari state yang ambigu.
        """
        if name not in self._branches:
            return False, f"Branch '{name}' tidak ditemukan."
        if name == self.active_branch_name:
            return False, f"Sudah berada di branch '{name}'."

        self._active_branch_pointer = self._branches[name]   # ← geser pointer
        return True, f"Berpindah ke branch '{name}'."

    def get_branch(self, name: str) -> Optional[Branch]:
        return self._branches.get(name)

    # ── Operasi Commit ─────────────────────────────────────────────────────────

    def make_commit(self, message: str, content: str) -> Tuple[bool, str, Optional[CommitNode]]:
        """
        Buat commit baru di branch aktif.

        Jika ada rollback stack yang terisi (sedang di tengah time-travel),
        rollback stack akan dibersihkan (sama seperti Git: tidak bisa redo
        setelah commit baru).
        """
        message = message.strip()
        if not message:
            return False, "Pesan commit tidak boleh kosong.", None

        # Bersihkan rollback stack saat commit baru dibuat
        if not self.active_branch.rollback_stack.is_empty():
            self.active_branch.rollback_stack.clear()

        node = CommitNode(
            message=message,
            content=content,
            branch_name=self.active_branch_name,
            parent=self.active_branch.head
        )
        self.active_branch.commit_stack.push(node)
        return True, f"Commit [{node.short_id}] '{message}' berhasil.", node

    # ── Time-Travel (Undo/Redo) ────────────────────────────────────────────────

    def step_back(self) -> Tuple[bool, str, Optional[CommitNode]]:
        """
        Rewind: Pop dari CommitStack → Push ke RollbackStack.
        Kembalikan CommitNode yang kini menjadi HEAD baru.
        """
        branch = self.active_branch

        if branch.commit_stack.size <= 1:
            return False, "Sudah berada di commit paling awal.", None

        # Pop dari commit stack utama
        popped = branch.commit_stack.pop()
        if popped:
            # Push ke rollback stack (untuk redo nanti)
            branch.rollback_stack.push(popped)

        new_head = branch.commit_stack.peek()
        msg = f"Rewind ke [{new_head.short_id}] '{new_head.message}'" if new_head else "Stack kosong."
        return True, msg, new_head

    def step_forward(self) -> Tuple[bool, str, Optional[CommitNode]]:
        """
        Fast Forward: Pop dari RollbackStack → Push kembali ke CommitStack.
        """
        branch = self.active_branch

        if branch.rollback_stack.is_empty():
            return False, "Tidak ada riwayat redo. Anda sudah di titik terbaru.", None

        # Pop dari rollback stack
        node = branch.rollback_stack.pop()
        if node:
            # Push kembali ke commit stack utama
            branch.commit_stack.push(node)

        head = branch.commit_stack.peek()
        msg = f"Forward ke [{head.short_id}] '{head.message}'" if head else "Stack kosong."
        return True, msg, head

    def jump_to_index(self, target_index: int) -> Tuple[bool, str, Optional[CommitNode]]:
        """
        Lompat ke posisi commit tertentu berdasarkan indeks (untuk slider).
        Indeks 0 = commit tertua, indeks n-1 = commit terbaru.
        """
        branch = self.active_branch
        all_commits = branch.commit_stack.to_list()
        rollback_list = branch.rollback_stack.to_list()

        # Total urutan lengkap: commit aktif + rollback (di atas HEAD)
        full_history = all_commits + list(reversed(rollback_list))
        total = len(full_history)

        if not (0 <= target_index < total):
            return False, f"Indeks {target_index} di luar jangkauan (0–{total-1}).", None

        current_index = len(all_commits) - 1   # posisi HEAD sekarang

        if target_index == current_index:
            return False, "Sudah berada di posisi ini.", branch.commit_stack.peek()

        # Lakukan step_back atau step_forward berulang
        while current_index > target_index:
            ok, _, _ = self.step_back()
            if not ok:
                break
            current_index -= 1

        while current_index < target_index:
            ok, _, _ = self.step_forward()
            if not ok:
                break
            current_index += 1

        head = branch.commit_stack.peek()
        return True, f"Melompat ke commit ke-{target_index}.", head

    # ── Merge & Conflict ───────────────────────────────────────────────────────

    def _detect_line_conflict(self, content_a: str, content_b: str) -> List[int]:
        """
        Deteksi konflik baris: kembalikan daftar nomor baris yang berbeda
        antara dua versi konten.
        """
        lines_a = content_a.splitlines()
        lines_b = content_b.splitlines()
        max_len = max(len(lines_a), len(lines_b))
        conflicting = []
        for i in range(max_len):
            line_a = lines_a[i] if i < len(lines_a) else ""
            line_b = lines_b[i] if i < len(lines_b) else ""
            if line_a != line_b:
                conflicting.append(i + 1)   # nomor baris 1-based
        return conflicting

    def merge_branch(self, source_name: str) -> Tuple[bool, str, Optional[ConflictState]]:
        """
        Coba merge branch sumber ke branch aktif (target).

        Alur:
        1. Cari commit leluhur bersama (common ancestor)
        2. Bandingkan HEAD source vs HEAD target
        3. Jika ada baris yang sama diubah keduanya → konflik
        4. Jika tidak ada konflik → fast-forward merge otomatis

        Returns
        -------
        (True, pesan, None)                     — merge berhasil
        (False, pesan, ConflictState aktif)     — ada konflik
        (False, pesan, None)                    — error lain
        """
        if source_name not in self._branches:
            return False, f"Branch '{source_name}' tidak ditemukan.", None
        if source_name == self.active_branch_name:
            return False, "Tidak bisa merge branch dengan dirinya sendiri.", None

        source_branch = self._branches[source_name]
        target_branch = self.active_branch

        source_head = source_branch.head
        target_head = target_branch.head

        if source_head is None:
            return False, f"Branch '{source_name}' tidak memiliki commit.", None

        # Cek apakah source punya perubahan yang berbeda dari target
        if source_head.content == (target_head.content if target_head else ""):
            return False, "Tidak ada perubahan untuk di-merge (konten identik).", None

        # Deteksi konflik baris
        target_content = target_head.content if target_head else ""
        source_content = source_head.content

        conflicting_lines = self._detect_line_conflict(target_content, source_content)

        if conflicting_lines:
            # ADA KONFLIK → aktifkan ConflictState
            self.conflict_state.activate(
                main_branch=target_branch.name,
                other_branch=source_branch.name,
                main_commit=target_head,
                other_commit=source_head
            )
            self.conflict_state.conflicting_lines = conflicting_lines

            return (
                False,
                f"⚠ KONFLIK pada {len(conflicting_lines)} baris! "
                f"Baris: {conflicting_lines[:5]}{'...' if len(conflicting_lines) > 5 else ''}",
                self.conflict_state
            )

        # TIDAK ADA KONFLIK → fast-forward merge
        merge_commit = CommitNode(
            message=f"Merge branch '{source_name}' into '{target_branch.name}'",
            content=source_content,
            branch_name=target_branch.name
        )
        target_branch.commit_stack.push(merge_commit)

        return True, f"Merge berhasil. Commit merge [{merge_commit.short_id}] dibuat.", None

    def resolve_conflict(self, keep_main: bool) -> Tuple[bool, str, Optional[CommitNode]]:
        """
        Selesaikan konflik merge yang aktif.

        Parameters
        ----------
        keep_main : bool
            True  → pertahankan commit dari Main Branch
            False → terima commit dari Branch sumber
        """
        if not self.conflict_state.is_active:
            return False, "Tidak ada konflik aktif.", None

        cs = self.conflict_state
        target_branch = self._branches.get(cs.main_branch_name)
        if target_branch is None:
            return False, f"Branch '{cs.main_branch_name}' tidak ditemukan.", None

        if keep_main:
            # Pertahankan konten main, buat merge commit dengan konten main
            winning_content = cs.conflict_pointer_main.content if cs.conflict_pointer_main else ""
            winner_label = "Main"
        else:
            # Terima konten branch lain
            winning_content = cs.conflict_pointer_other.content if cs.conflict_pointer_other else ""
            winner_label = cs.other_branch_name

        merge_commit = CommitNode(
            message=f"Merge conflict resolved — keeping '{winner_label}'",
            content=winning_content,
            branch_name=target_branch.name
        )
        target_branch.commit_stack.push(merge_commit)

        # Reset conflict state
        cs.resolve()
        self._active_branch_pointer = target_branch

        return True, f"Konflik diselesaikan. Commit [{merge_commit.short_id}] dibuat (menggunakan: {winner_label}).", merge_commit

    # ── Snapshot untuk GUI ─────────────────────────────────────────────────────

    def get_snapshot(self) -> dict:
        """
        Kembalikan ringkasan keseluruhan state untuk GUI refresh.
        Dipanggil setiap kali ada perubahan state.
        """
        active = self.active_branch
        return {
            "active_branch": active.name,
            "active_head": active.head,
            "active_stack": active.commit_stack.to_list(),
            "active_stack_size": active.commit_stack.size,
            "rollback_stack": active.rollback_stack.to_list(),
            "rollback_size": active.rollback_stack.size,
            "top_pointer": active.commit_stack.top_pointer,
            "all_branches": {
                name: {
                    "history": branch.history,
                    "head": branch.head,
                    "color": branch.color,
                    "origin_commit_id": branch.origin_commit.commit_id if branch.origin_commit else None,
                    "size": branch.commit_stack.size,
                }
                for name, branch in self._branches.items()
            },
            "conflict": {
                "is_active": self.conflict_state.is_active,
                "main_branch": self.conflict_state.main_branch_name,
                "other_branch": self.conflict_state.other_branch_name,
                "main_commit": self.conflict_state.conflict_pointer_main,
                "other_commit": self.conflict_state.conflict_pointer_other,
                "conflicting_lines": self.conflict_state.conflicting_lines,
            }
        }
