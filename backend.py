"""
GitFlow Sim - Backend: Struktur Data Murni
Berisi: CommitNode, Stack, BranchManager
"""

import hashlib
import time
import random


# ──────────────────────────────────────────────
# 1. COMMIT NODE  (pengganti linked-list node)
# ──────────────────────────────────────────────
class CommitNode:
    """
    Satu simpul commit.  Atribut `prev` adalah POINTER manual
    ke CommitNode sebelumnya (bukan list Python).
    """
    def __init__(self, message: str, content: str, prev=None):
        # Buat hash unik dari pesan + waktu + angka acak
        raw = f"{message}{time.time()}{random.random()}"
        self.commit_id: str = hashlib.sha1(raw.encode()).hexdigest()[:7]
        self.message: str = message
        self.timestamp: str = time.strftime("%H:%M:%S")
        self.content: str = content          # "isi file" yang disimulasikan
        self.prev: "CommitNode | None" = prev   # ← pointer manual

        # Alamat memori buatan (hanya untuk visualisasi)
        base = random.randint(0x7FFE10, 0x7FFEFF)
        self.fake_address: str = f"0x{base:X}"

    def __repr__(self):
        return f"CommitNode({self.commit_id}, '{self.message}')"


# ──────────────────────────────────────────────
# 2. STACK  (implementasi manual tanpa list.append/pop)
# ──────────────────────────────────────────────
class Stack:
    """
    Stack berbasis linked-list manual.
    _top  → CommitNode teratas  (HEAD)
    _size → jumlah elemen
    """
    def __init__(self):
        self._top: CommitNode | None = None
        self._size: int = 0

    # — Operasi Utama —
    def push(self, node: CommitNode) -> None:
        """Tautkan node baru ke atas stack (O(1))."""
        node.prev = self._top          # arahkan pointer node ke top lama
        self._top = node               # top sekarang adalah node baru
        self._size += 1

    def pop(self) -> CommitNode | None:
        """Cabut elemen teratas, kembalikan node-nya (O(1))."""
        if self.is_empty():
            return None
        node = self._top
        self._top = node.prev          # geser top ke bawah
        node.prev = None               # putus pointer (bersihkan referensi)
        self._size -= 1
        return node

    def peek(self) -> CommitNode | None:
        """Lihat elemen teratas tanpa mencabut."""
        return self._top

    def is_empty(self) -> bool:
        return self._top is None

    def size(self) -> int:
        return self._size

    # — Helper: ubah stack jadi list (untuk visualisasi, dari atas ke bawah) —
    def to_list(self) -> list[CommitNode]:
        result = []
        current = self._top
        while current is not None:
            result.append(current)
            current = current.prev
        return result


# ──────────────────────────────────────────────
# 3. BRANCH MANAGER
# ──────────────────────────────────────────────
class BranchManager:
    """
    Mengelola seluruh branch, pointer aktif, dan rollback stack.
    Setiap branch punya Stack commit + Stack rollback tersendiri.
    """
    def __init__(self):
        # Inisiasi branch utama
        self._branches: dict[str, Stack] = {"main": Stack()}
        self._rollbacks: dict[str, Stack] = {"main": Stack()}
        self._active: str = "main"           # ← Active Branch Pointer

    # ── Properties ──────────────────────────
    @property
    def active_branch(self) -> str:
        return self._active

    @property
    def branch_names(self) -> list[str]:
        return list(self._branches.keys())

    def current_stack(self) -> Stack:
        return self._branches[self._active]

    def current_rollback(self) -> Stack:
        return self._rollbacks[self._active]

    # ── Operasi Commit ───────────────────────
    def commit(self, message: str, content: str) -> CommitNode:
        """Push commit baru ke stack branch aktif."""
        node = CommitNode(message, content)
        self.current_stack().push(node)
        # Hapus rollback karena jalur baru dimulai
        self._rollbacks[self._active] = Stack()
        return node

    # ── Time-Travel ──────────────────────────
    def rewind(self) -> CommitNode | None:
        """
        Pop dari commit stack → push ke rollback stack.
        Kembalikan node yang dipop (untuk mengupdate editor).
        """
        stack = self.current_stack()
        rollback = self.current_rollback()
        if stack.size() <= 1:
            # Jaga agar minimal 1 commit tersisa (tidak bisa balik ke kosong)
            return None
        node = stack.pop()
        rollback.push(node)
        return node

    def forward(self) -> CommitNode | None:
        """
        Pop dari rollback stack → push kembali ke commit stack.
        """
        stack = self.current_stack()
        rollback = self.current_rollback()
        if rollback.is_empty():
            return None
        node = rollback.pop()
        stack.push(node)
        return node

    def can_rewind(self) -> bool:
        return self.current_stack().size() > 1

    def can_forward(self) -> bool:
        return not self.current_rollback().is_empty()

    # ── Branch Operations ─────────────────────
    def create_branch(self, name: str) -> bool:
        """
        Buat branch baru dari HEAD branch aktif saat ini.
        Salin node HEAD (bukan stack penuh) sebagai titik awal.
        """
        if name in self._branches:
            return False  # nama sudah ada
        new_stack = Stack()
        new_rollback = Stack()
        # Salin seluruh history dari branch aktif ke branch baru
        nodes = self.current_stack().to_list()
        for node in reversed(nodes):
            clone = CommitNode(node.message, node.content)
            clone.commit_id = node.commit_id   # pertahankan id yang sama
            clone.timestamp = node.timestamp
            clone.fake_address = node.fake_address
            new_stack.push(clone)
        self._branches[name] = new_stack
        self._rollbacks[name] = new_rollback
        return True

    def switch_branch(self, name: str) -> bool:
        if name not in self._branches:
            return False
        self._active = name
        return True

    # ── Merge & Conflict Detection ────────────
    def detect_conflict(self, other_branch: str) -> bool:
        """
        Konflik terjadi jika HEAD kedua branch berbeda commit_id
        tapi keduanya memiliki commit setelah fork-point yang sama.
        """
        if other_branch not in self._branches:
            return False
        main_head = self._branches["main"].peek()
        other_head = self._branches[other_branch].peek()
        if main_head is None or other_head is None:
            return False
        return main_head.commit_id != other_head.commit_id

    def merge(self, source_branch: str, keep_main: bool = True) -> CommitNode | None:
        """
        Lakukan merge: pilih commit HEAD mana yang dipakai.
        Returns: commit node pemenang (sudah di-push ke main).
        """
        if source_branch not in self._branches:
            return None
        if keep_main:
            winner = self._branches["main"].peek()
        else:
            # Ganti HEAD main dengan HEAD source
            loser = self._branches["main"].pop()   # pop HEAD main
            winner = self._branches[source_branch].peek()
            if winner:
                merge_node = CommitNode(
                    f"Merge: {winner.message}",
                    winner.content
                )
                self._branches["main"].push(merge_node)
                winner = merge_node
        # Hapus branch yang di-merge (opsional, bisa dipertahankan)
        # del self._branches[source_branch]
        self._active = "main"
        return winner

    # ── Top Pointer Info ─────────────────────
    def top_pointer(self) -> CommitNode | None:
        """Referensi ke elemen TOP pada stack branch aktif."""
        return self.current_stack().peek()

    def stack_snapshot(self) -> list[CommitNode]:
        """List semua commit dari TOP ke bawah (untuk visualisasi)."""
        return self.current_stack().to_list()

    def rollback_count(self) -> int:
        return self.current_rollback().size()
