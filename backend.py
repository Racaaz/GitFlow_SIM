"""
GitFlow Sim – Backend v2
Struktur data murni: CommitNode, Stack, BranchManager
Baru: fork-point tracking, conflict detail, merge reconciliation
"""

import hashlib, time, random


# ─────────────────────────────────────────────────────────────────────────────
# 1. COMMIT NODE
# ─────────────────────────────────────────────────────────────────────────────
class CommitNode:
    """
    Satu simpul commit.  `prev` adalah POINTER manual ke node sebelumnya.
    """
    def __init__(self, message: str, content: str, prev=None):
        raw = f"{message}{time.time()}{random.random()}"
        self.commit_id:    str  = hashlib.sha1(raw.encode()).hexdigest()[:7]
        self.message:      str  = message
        self.timestamp:    str  = time.strftime("%H:%M:%S")
        self.content:      str  = content
        self.prev: "CommitNode | None" = prev
        base = random.randint(0x7FFE10, 0x7FFEFF)
        self.fake_address: str  = f"0x{base:X}"

    def __repr__(self):
        return f"CommitNode({self.commit_id}, '{self.message}')"


# ─────────────────────────────────────────────────────────────────────────────
# 2. STACK  (linked-list manual)
# ─────────────────────────────────────────────────────────────────────────────
class Stack:
    def __init__(self):
        self._top:  CommitNode | None = None
        self._size: int = 0

    def push(self, node: CommitNode) -> None:
        node.prev  = self._top
        self._top  = node
        self._size += 1

    def pop(self) -> CommitNode | None:
        if self.is_empty():
            return None
        node       = self._top
        self._top  = node.prev
        node.prev  = None
        self._size -= 1
        return node

    def peek(self) -> CommitNode | None:
        return self._top

    def is_empty(self) -> bool:
        return self._top is None

    def size(self) -> int:
        return self._size

    def to_list(self) -> list[CommitNode]:
        """Kembalikan list dari TOP → BOTTOM."""
        result, cur = [], self._top
        while cur:
            result.append(cur)
            cur = cur.prev
        return result


# ─────────────────────────────────────────────────────────────────────────────
# 3. CONFLICT INFO  (data class sederhana)
# ─────────────────────────────────────────────────────────────────────────────
class ConflictInfo:
    """Menyimpan detail konflik yang terdeteksi."""
    def __init__(self, branch_a: str, branch_b: str,
                 head_a: CommitNode, head_b: CommitNode,
                 fork_id: str | None):
        self.branch_a   = branch_a     # biasanya "main"
        self.branch_b   = branch_b
        self.head_a     = head_a       # HEAD main saat konflik
        self.head_b     = head_b       # HEAD branch B
        self.fork_id    = fork_id      # commit_id titik percabangan
        self.resolved   = False
        self.winner     = None         # "main" | "branch"


# ─────────────────────────────────────────────────────────────────────────────
# 4. BRANCH MANAGER
# ─────────────────────────────────────────────────────────────────────────────
class BranchManager:
    def __init__(self):
        self._branches:  dict[str, Stack] = {"main": Stack()}
        self._rollbacks: dict[str, Stack] = {"main": Stack()}
        # fork_points[branch_name] = commit_id tempat branch itu dibuat
        self._fork_points: dict[str, str | None] = {"main": None}
        self._active: str = "main"
        self.last_conflict: ConflictInfo | None = None

    # ── Properti ─────────────────────────────────────────────────────────────
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

    # ── Commit ────────────────────────────────────────────────────────────────
    def commit(self, message: str, content: str) -> CommitNode:
        node = CommitNode(message, content)
        self.current_stack().push(node)
        self._rollbacks[self._active] = Stack()   # buang rollback buffer
        return node

    # ── Time-Travel ──────────────────────────────────────────────────────────
    def rewind(self) -> CommitNode | None:
        stack, rollback = self.current_stack(), self.current_rollback()
        if stack.size() <= 1:
            return None
        node = stack.pop()
        rollback.push(node)
        return node

    def forward(self) -> CommitNode | None:
        stack, rollback = self.current_stack(), self.current_rollback()
        if rollback.is_empty():
            return None
        node = rollback.pop()
        stack.push(node)
        return node

    def can_rewind(self)  -> bool: return self.current_stack().size() > 1
    def can_forward(self) -> bool: return not self.current_rollback().is_empty()

    # ── Branch ───────────────────────────────────────────────────────────────
    def create_branch(self, name: str) -> bool:
        if name in self._branches:
            return False
        new_stack = Stack()
        # Salin seluruh history dari branch aktif
        for node in reversed(self.current_stack().to_list()):
            clone = CommitNode(node.message, node.content)
            clone.commit_id   = node.commit_id
            clone.timestamp   = node.timestamp
            clone.fake_address = node.fake_address
            new_stack.push(clone)
        self._branches[name]    = new_stack
        self._rollbacks[name]   = Stack()
        # Simpan fork-point = HEAD saat branch dibuat
        head = self.current_stack().peek()
        self._fork_points[name] = head.commit_id if head else None
        return True

    def switch_branch(self, name: str) -> bool:
        if name not in self._branches:
            return False
        self._active = name
        return True

    # ── Conflict Detection ────────────────────────────────────────────────────
    def detect_conflict(self, other_branch: str) -> ConflictInfo | None:
        """
        Konflik = kedua branch punya commit BARU setelah fork-point yang sama,
        DAN konten HEAD-nya berbeda.
        Kembalikan ConflictInfo jika ada konflik, None jika tidak.
        """
        if other_branch not in self._branches:
            return None
        main_head  = self._branches["main"].peek()
        other_head = self._branches[other_branch].peek()
        if not main_head or not other_head:
            return None

        fork_id = self._fork_points.get(other_branch)

        # Cek apakah main punya commit baru setelah fork
        main_ids  = [n.commit_id for n in self._branches["main"].to_list()]
        other_ids = [n.commit_id for n in self._branches[other_branch].to_list()]

        main_new_after_fork  = fork_id not in main_ids or main_ids[0] != fork_id
        other_new_after_fork = other_ids[0] != fork_id

        # Konflik hanya jika KEDUANYA berubah setelah fork & konten HEAD berbeda
        if main_new_after_fork and other_new_after_fork and \
                main_head.content != other_head.content:
            info = ConflictInfo("main", other_branch,
                                main_head, other_head, fork_id)
            self.last_conflict = info
            return info

        return None   # tidak ada konflik

    # ── Merge & Rekonsiliasi ──────────────────────────────────────────────────
    def merge(self, source_branch: str, keep_main: bool = True) -> CommitNode | None:
        """
        Rekonsiliasi stack:
        - keep_main=True  → buang HEAD source, pertahankan HEAD main
        - keep_main=False → ganti HEAD main dengan HEAD source (buat merge-commit)
        Kembalikan CommitNode pemenang.
        """
        if source_branch not in self._branches:
            return None

        self._active = "main"

        if keep_main:
            winner = self._branches["main"].peek()
        else:
            # Pop HEAD main (kalah) → push merge-commit baru
            loser = self._branches["main"].pop()
            src_head = self._branches[source_branch].peek()
            if src_head:
                merge_node = CommitNode(
                    f"Merge '{source_branch}': {src_head.message}",
                    src_head.content
                )
                self._branches["main"].push(merge_node)
                winner = merge_node
            else:
                winner = loser

        # Tandai konflik selesai
        if self.last_conflict and self.last_conflict.branch_b == source_branch:
            self.last_conflict.resolved = True
            self.last_conflict.winner   = "main" if keep_main else "branch"

        return winner

    # ── Helpers ──────────────────────────────────────────────────────────────
    def top_pointer(self) -> CommitNode | None:
        return self.current_stack().peek()

    def stack_snapshot(self) -> list[CommitNode]:
        return self.current_stack().to_list()

    def rollback_count(self) -> int:
        return self.current_rollback().size()

    def get_branch_head(self, name: str) -> CommitNode | None:
        return self._branches[name].peek() if name in self._branches else None

    def get_fork_point(self, branch: str) -> str | None:
        return self._fork_points.get(branch)
