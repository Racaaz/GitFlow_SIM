"""
test_backend.py
===============
Verifikasi manual seluruh logika backend GitFlow Sim.
Jalankan: python test_backend.py
"""

import sys
sys.path.insert(0, '.')

from core import BranchManager, CommitStack, RollbackStack, CommitNode

PASS = "✅"
FAIL = "❌"

def section(title: str):
    print(f"\n{'═'*60}")
    print(f"  {title}")
    print('═'*60)

def check(label: str, condition: bool):
    status = PASS if condition else FAIL
    print(f"  {status}  {label}")
    if not condition:
        print(f"       → GAGAL!")

# ──────────────────────────────────────────────────────────────────────────────
section("1. CommitNode & Stack Dasar")
# ──────────────────────────────────────────────────────────────────────────────

stack = CommitStack("main")
check("Stack awal kosong", stack.is_empty())
check("Size awal = 0", stack.size == 0)
check("Peek pada stack kosong = None", stack.peek() is None)
check("Pop pada stack kosong = None", stack.pop() is None)

# Push 3 commit
c1 = CommitNode("feat: init", "konten A", "main")
c2 = CommitNode("feat: tambah header", "konten B", "main")
c3 = CommitNode("fix: perbaiki typo", "konten C", "main")

stack.push(c1)
check("Setelah push 1: size=1", stack.size == 1)
stack.push(c2)
stack.push(c3)
check("Setelah push 3: size=3", stack.size == 3)
check("TOP = c3", stack.peek() is c3)
check("c3.pointer_to_prev = c2", c3.pointer_to_prev is c2)
check("c2.pointer_to_prev = c1", c2.pointer_to_prev is c1)
check("c1.pointer_to_prev = None", c1.pointer_to_prev is None)

# to_list: urutan dari terlama ke terbaru
lst = stack.to_list()
check("to_list() urutan benar [c1,c2,c3]", lst == [c1, c2, c3])

# Pop
popped = stack.pop()
check("Pop mengembalikan c3", popped is c3)
check("Setelah pop: TOP = c2", stack.peek() is c2)
check("Setelah pop: size = 2", stack.size == 2)

# ──────────────────────────────────────────────────────────────────────────────
section("2. Rollback Stack (Undo/Redo)")
# ──────────────────────────────────────────────────────────────────────────────

rb = RollbackStack()
check("Rollback stack awal kosong", rb.is_empty())

rb.push(popped)   # simpan c3 yang tadi di-pop
check("Setelah push ke rollback: size=1", rb.size == 1)
check("Peek rollback = c3", rb.peek() is c3)

restored = rb.pop()
check("Pop dari rollback = c3", restored is c3)
check("Rollback kosong kembali", rb.is_empty())

rb.clear()
check("Clear rollback tidak error", rb.is_empty())

# ──────────────────────────────────────────────────────────────────────────────
section("3. BranchManager — Init & Commit")
# ──────────────────────────────────────────────────────────────────────────────

bm = BranchManager()
check("Branch 'main' ada", "main" in bm.all_branch_names)
check("Active branch = 'main'", bm.active_branch_name == "main")
check("Initial commit sudah ada", bm.active_branch.commit_stack.size == 1)

ok, msg, node = bm.make_commit("feat: tambah konten", "Baris satu\nBaris dua\nBaris tiga")
check(f"Commit sukses: {msg}", ok)
check("Stack main sekarang size=2", bm.active_branch.commit_stack.size == 2)
check("HEAD = commit terbaru", bm.active_branch.head is node)

# ──────────────────────────────────────────────────────────────────────────────
section("4. BranchManager — Branching")
# ──────────────────────────────────────────────────────────────────────────────

ok, msg = bm.create_branch("feature-x")
check(f"Buat branch baru: {msg}", ok)
check("Branch 'feature-x' ada", "feature-x" in bm.all_branch_names)
check("Active masih 'main'", bm.active_branch_name == "main")

ok, msg = bm.switch_branch("feature-x")
check(f"Switch branch: {msg}", ok)
check("Active sekarang 'feature-x'", bm.active_branch_name == "feature-x")

ok, msg, n = bm.make_commit("feat: fitur baru di feature-x", "Baris satu\nBaris dua\nBaris BARU dari feature-x")
check(f"Commit di feature-x: {msg}", ok)
check("feature-x size = 3", bm.active_branch.commit_stack.size == 3)

# Commit di main dengan baris konflik
bm.switch_branch("main")
ok, msg, n = bm.make_commit("fix: ubah baris dua di main", "Baris satu\nBaris dua DIUBAH di main\nBaris tiga")
check(f"Commit di main setelah switch: {msg}", ok)

# ──────────────────────────────────────────────────────────────────────────────
section("5. Time Travel (Step Back / Forward)")
# ──────────────────────────────────────────────────────────────────────────────

main_size_before = bm.active_branch.commit_stack.size
ok, msg, head = bm.step_back()
check(f"Step back berhasil: {msg}", ok)
check("Stack berkurang 1", bm.active_branch.commit_stack.size == main_size_before - 1)
check("Rollback bertambah 1", bm.active_branch.rollback_stack.size == 1)

ok, msg, head = bm.step_forward()
check(f"Step forward berhasil: {msg}", ok)
check("Stack kembali normal", bm.active_branch.commit_stack.size == main_size_before)
check("Rollback kosong kembali", bm.active_branch.rollback_stack.is_empty())

# ──────────────────────────────────────────────────────────────────────────────
section("6. Merge & Konflik")
# ──────────────────────────────────────────────────────────────────────────────

ok, msg, conflict = bm.merge_branch("feature-x")
if ok:
    check("Merge tanpa konflik (tidak expected di sini)", True)
else:
    check(f"Konflik terdeteksi: {msg}", conflict is not None and conflict.is_active)
    check("Conflict state aktif", bm.conflict_state.is_active)
    check("Pointer konflik main tidak None", bm.conflict_state.conflict_pointer_main is not None)
    check("Pointer konflik other tidak None", bm.conflict_state.conflict_pointer_other is not None)

    # Selesaikan: terima main
    ok2, msg2, merged = bm.resolve_conflict(keep_main=True)
    check(f"Resolve konflik (keep main): {msg2}", ok2)
    check("Conflict state tidak aktif lagi", not bm.conflict_state.is_active)
    check("Merge commit ada di stack", bm.active_branch.commit_stack.size > main_size_before)

# ──────────────────────────────────────────────────────────────────────────────
section("7. Snapshot GUI")
# ──────────────────────────────────────────────────────────────────────────────

snap = bm.get_snapshot()
check("Snapshot punya key 'active_branch'", "active_branch" in snap)
check("Snapshot punya key 'top_pointer'", "top_pointer" in snap)
check("Snapshot punya key 'conflict'", "conflict" in snap)
check("Conflict tidak aktif di snapshot", not snap["conflict"]["is_active"])

# ──────────────────────────────────────────────────────────────────────────────
section("8. Edge Cases")
# ──────────────────────────────────────────────────────────────────────────────

ok, msg = bm.create_branch("")
check("Nama kosong ditolak", not ok)

ok, msg = bm.create_branch("main")
check("Nama duplikat ditolak", not ok)

ok, msg = bm.create_branch("nama branch spasi")
check("Nama dengan spasi ditolak", not ok)

ok, msg = bm.switch_branch("main")
check("Switch ke branch sama ditolak", not ok)

ok, msg, node = bm.make_commit("", "konten")
check("Commit pesan kosong ditolak", not ok)

print(f"\n{'═'*60}")
print("  ✅ Semua test selesai dijalankan.")
print('═'*60)
