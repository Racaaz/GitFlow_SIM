"""
core/commit.py
==============
Definisi CommitNode — unit terkecil dalam sistem GitFlow Sim.
Setiap node menyimpan data commit dan pointer manual ke node sebelumnya,
persis seperti Linked List node pada struktur data klasik.
"""

import time
import random
import string


def generate_commit_id(length: int = 7) -> str:
    """Menghasilkan hash commit palsu ala Git (7 karakter hex)."""
    return ''.join(random.choices('0123456789abcdef', k=length))


def generate_memory_address() -> str:
    """Menghasilkan alamat memori buatan untuk visualisasi (format hex)."""
    base = random.randint(0x7FFE00, 0x7FFFFF)
    return f"0x{base:06X}"


class CommitNode:
    """
    Representasi satu unit commit dalam Stack.

    Attributes
    ----------
    commit_id       : str   — Hash unik 7 karakter (misal: 'a3f9c12')
    message         : str   — Pesan commit dari pengguna
    timestamp       : float — Unix timestamp saat commit dibuat
    content         : str   — Isi/konten file yang disimpan saat commit ini
    memory_address  : str   — Alamat memori buatan untuk visualisasi
    branch_name     : str   — Nama branch tempat commit ini dibuat
    pointer_to_prev : CommitNode | None — Pointer manual ke commit sebelumnya
    """

    def __init__(self, message: str, content: str, branch_name: str,
                 parent: 'CommitNode | None' = None):
        self.commit_id: str = generate_commit_id()
        self.message: str = message
        self.timestamp: float = time.time()
        self.content: str = content
        self.memory_address: str = generate_memory_address()
        self.branch_name: str = branch_name
        self.pointer_to_prev: 'CommitNode | None' = parent   # ← pointer manual

    @property
    def short_id(self) -> str:
        """Tampilkan 7 karakter pertama commit ID (konvensi Git)."""
        return self.commit_id[:7]

    @property
    def formatted_time(self) -> str:
        """Kembalikan timestamp dalam format HH:MM:SS."""
        return time.strftime('%H:%M:%S', time.localtime(self.timestamp))

    @property
    def formatted_datetime(self) -> str:
        """Kembalikan timestamp dalam format lengkap."""
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.timestamp))

    def __repr__(self) -> str:
        return (f"CommitNode(id={self.short_id!r}, "
                f"msg={self.message!r}, "
                f"branch={self.branch_name!r}, "
                f"addr={self.memory_address})")
