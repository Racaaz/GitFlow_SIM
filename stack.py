"""
core/stack.py
=============
Implementasi Stack MANUAL menggunakan pointer (bukan list Python bawaan).
Setiap Branch memiliki instance Stack sendiri.
Disertai RollbackStack untuk mekanisme Undo/Redo time-travel.
"""

from __future__ import annotations
from typing import Optional, List
from .commit import CommitNode


# ──────────────────────────────────────────────────────────────────────────────
# COMMIT STACK (utama)
# ──────────────────────────────────────────────────────────────────────────────

class CommitStack:
    """
    Stack berbasis linked-pointer untuk menyimpan riwayat commit satu Branch.

    Tidak menggunakan list Python sebagai penyimpan utama — elemen dihubungkan
    murni lewat `CommitNode.pointer_to_prev` (analog dengan pointer C).

    Attributes
    ----------
    _top    : CommitNode | None  — TOP POINTER, selalu menunjuk elemen teratas
    _size   : int                — Jumlah elemen dalam stack
    name    : str                — Nama branch pemilik stack ini
    """

    def __init__(self, branch_name: str):
        self._top: Optional[CommitNode] = None   # ← TOP POINTER
        self._size: int = 0
        self.name: str = branch_name

    # ── Operasi Utama ──────────────────────────────────────────────────────────

    def push(self, node: CommitNode) -> CommitNode:
        """
        Masukkan CommitNode ke atas stack (O(1)).
        Top pointer diperbarui ke node baru.
        """
        node.pointer_to_prev = self._top   # sambungkan ke elemen sebelumnya
        self._top = node                   # geser TOP ke atas
        self._size += 1
        return node

    def pop(self) -> Optional[CommitNode]:
        """
        Keluarkan elemen paling atas dari stack (O(1)).
        Top pointer digeser ke elemen di bawahnya.
        Kembalikan None jika stack kosong.
        """
        if self.is_empty():
            return None
        popped = self._top
        self._top = self._top.pointer_to_prev   # turunkan TOP POINTER
        if popped:
            popped.pointer_to_prev = None       # putuskan pointer (bersihkan)
        self._size -= 1
        return popped

    def peek(self) -> Optional[CommitNode]:
        """Lihat elemen teratas tanpa mengeluarkannya (O(1))."""
        return self._top

    # ── Utilitas ───────────────────────────────────────────────────────────────

    def is_empty(self) -> bool:
        return self._top is None

    @property
    def size(self) -> int:
        return self._size

    @property
    def top_pointer(self) -> Optional[CommitNode]:
        """Alias eksplisit untuk top pointer — digunakan di visualisasi."""
        return self._top

    def to_list(self) -> List[CommitNode]:
        """
        Konversi stack ke list Python (untuk keperluan visualisasi GUI saja).
        Indeks 0 = paling bawah (tertua), indeks -1 = paling atas (terbaru).
        Operasi ini O(n) dan TIDAK mengubah struktur stack.
        """
        result = []
        current = self._top
        while current is not None:
            result.append(current)
            current = current.pointer_to_prev
        result.reverse()   # balik agar urutan kronologis
        return result

    def clone_from(self, other: 'CommitStack') -> None:
        """
        Salin semua elemen dari stack lain ke stack ini (untuk branching).
        Stack baru berbagi referensi ke CommitNode yang sama (shallow copy).
        """
        # Ambil semua node dari stack sumber
        nodes = other.to_list()
        # Reset stack ini
        self._top = None
        self._size = 0
        # Push ulang dari bawah ke atas
        for node in nodes:
            # Buat wrapper node baru agar pointer tidak saling tumpang-tindih
            cloned = CommitNode(
                message=node.message,
                content=node.content,
                branch_name=self.name,  # ganti nama branch
                parent=None
            )
            cloned.commit_id = node.commit_id   # pertahankan ID asli
            cloned.timestamp = node.timestamp
            cloned.memory_address = node.memory_address
            self.push(cloned)

    def __repr__(self) -> str:
        return f"CommitStack(branch={self.name!r}, size={self._size}, top={self._top})"


# ──────────────────────────────────────────────────────────────────────────────
# ROLLBACK STACK (untuk Undo/Redo time-travel)
# ──────────────────────────────────────────────────────────────────────────────

class RollbackStack:
    """
    Stack sekunder yang menampung commit yang di-pop dari CommitStack utama.
    Memungkinkan operasi Redo (push kembali) tanpa kehilangan data.

    Mekanisme:
      - Rewind/Step Back → pop dari CommitStack → push ke RollbackStack
      - Fast Forward/Step Next → pop dari RollbackStack → push ke CommitStack
    """

    def __init__(self):
        self._top: Optional[CommitNode] = None
        self._size: int = 0

    def push(self, node: CommitNode) -> None:
        """Simpan node yang di-pop dari commit stack utama."""
        node.pointer_to_prev = self._top
        self._top = node
        self._size += 1

    def pop(self) -> Optional[CommitNode]:
        """Ambil kembali node untuk di-redo ke commit stack utama."""
        if self.is_empty():
            return None
        popped = self._top
        self._top = self._top.pointer_to_prev
        if popped:
            popped.pointer_to_prev = None
        self._size -= 1
        return popped

    def peek(self) -> Optional[CommitNode]:
        return self._top

    def is_empty(self) -> bool:
        return self._top is None

    def clear(self) -> None:
        """Hapus semua isi rollback (dipanggil saat commit baru dibuat setelah rewind)."""
        self._top = None
        self._size = 0

    @property
    def size(self) -> int:
        return self._size

    def to_list(self) -> List[CommitNode]:
        """Untuk visualisasi saja."""
        result = []
        current = self._top
        while current:
            result.append(current)
            current = current.pointer_to_prev
        return result   # urutan: top = indeks 0

    def __repr__(self) -> str:
        return f"RollbackStack(size={self._size})"
