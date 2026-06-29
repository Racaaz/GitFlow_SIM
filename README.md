# ⬡ GitFlow Sim

**Interactive Data Structure & Version Control Simulator**

GitFlow Sim adalah aplikasi desktop berbasis Python yang memvisualisasikan cara kerja struktur data **Stack (Linked List)** melalui simulasi workflow Git sederhana — commit, time-travel (rewind/forward), branching, hingga deteksi & resolusi konflik merge. Seluruh logika backend dibangun manual tanpa library struktur data eksternal, sehingga proses push/pop, pointer, dan linked list benar-benar terlihat "di balik layar".

---

## ✨ Fitur Utama

| Fitur | Deskripsi |
|---|---|
| 📝 **Commit** | Menyimpan snapshot teks sebagai node baru di atas Stack |
| ◀▶ **Time-Travel (Rewind/Forward)** | Mundur/maju antar commit menggunakan rollback buffer (Stack kedua) |
| ⎇ **Multi-Branch** | Membuat & berpindah branch, masing-masing punya Stack independen |
| ⚠ **Conflict Detection** | Otomatis mendeteksi konflik saat HEAD `main` dan branch lain berbeda sejak fork-point |
| 🧩 **Conflict Arena** | Panel visual untuk membandingkan diff & memilih pemenang konflik |
| 💾 **Auto-Save / Auto-Load** | Seluruh state (Stack, branch, rollback, fork-point) disimpan otomatis ke disk dan dimuat kembali saat aplikasi dibuka ulang |
| 🎨 **Visualisasi Real-time** | Animasi push/pop, pointer TOP, dan linimasa commit di GUI dark-mode neon |

---

## 🗂️ Struktur Proyek

```
gitflow-sim/
├── backend.py             # Logika inti: struktur data & state management
├── main.py                # GUI (customtkinter) & event handler
├── gitflow_session.dat    # (otomatis dibuat) file penyimpanan sesi
└── README.md
```

### Komponen Backend (`backend.py`)

| Kelas | Peran |
|---|---|
| `CommitNode` | Node tunggal dalam linked list (id, message, timestamp, content, pointer `prev`) |
| `Stack` | Stack manual berbasis linked list (push/pop/peek — semua O(1)) |
| `ConflictInfo` | Data class yang menyimpan detail konflik antar branch |
| `BranchManager` | Koordinator multi-branch: commit, rewind/forward, create/switch branch, deteksi konflik, merge, **serta persistence (save/load session)** |

### Komponen Frontend (`main.py`)

Dibangun dengan **CustomTkinter**, terbagi 3 panel:

- **Panel Kiri** — Memory & Stack Monitor (visualisasi linked list + animasi push/pop)
- **Panel Tengah** — Time-Travel Visualizer & editor commit
- **Panel Kanan** — Conflict Arena (aktif otomatis saat merge konflik terdeteksi)

---

## ⚙️ Instalasi

### Prasyarat
- Python **3.10+** (memakai sintaks `X | None`)
- pip

### Langkah Instalasi

```bash
pip install customtkinter
```

Library lain yang digunakan (`tkinter`, `hashlib`, `time`, `random`, `pickle`, `os`) sudah bawaan Python standar — tidak perlu instalasi tambahan.

> **Catatan font:** Aplikasi menggunakan font *JetBrains Mono* jika tersedia di sistem. Jika tidak, tkinter otomatis fallback ke font monospace bawaan sistem — aplikasi tetap berjalan normal.

---

## ▶️ Cara Menjalankan

Pastikan `backend.py` dan `main.py` berada di folder yang sama, lalu jalankan:

```bash
python main.py
```

Aplikasi akan terbuka dengan jendela GUI berukuran `1400x820` (minimal `1200x700`).

---

## 💾 Sistem Penyimpanan Permanen (Persistence)

Sejak versi ini, GitFlow Sim **tidak lagi kehilangan data saat aplikasi ditutup**.

### Cara Kerja

1. **Auto-Load (saat startup)**
   Saat `main.py` dijalankan, aplikasi mengecek apakah file `gitflow_session.dat` ada di folder proyek.
   - Jika **ada** → seluruh state (`BranchManager`, mencakup semua branch, Stack, rollback buffer, fork-point) di-*deserialize* dan GUI langsung menyesuaikan tampilan (panel Stack Monitor, linimasa, dan combobox branch ter-render otomatis).
   - Jika **tidak ada** (kunjungan pertama) → aplikasi berjalan normal dengan commit awal, tanpa error.

2. **Auto-Save (saat ada perubahan data)**
   Sistem menyimpan state secara otomatis ke `gitflow_session.dat` setiap kali:
   - Pengguna menekan **Commit**
   - **Merge** berhasil tanpa konflik
   - Konflik **berhasil diselesaikan** (resolve conflict)
   - Branch baru **dibuat**
   - Aplikasi **ditutup** (sebagai pengaman tambahan lewat `WM_DELETE_WINDOW`)

3. **Format Penyimpanan**
   Menggunakan modul bawaan Python `pickle` untuk serialisasi biner objek `BranchManager` secara utuh — termasuk seluruh pointer linked list antar `CommitNode`.

### API Persistence (`backend.py`)

```python
bm = BranchManager()

# Simpan sesi ke disk
bm.save_session(path="gitflow_session.dat")  # -> True/False

# Muat sesi dari disk (static method)
loaded = BranchManager.load_session(path="gitflow_session.dat")  # -> BranchManager | None
```

> ⚠️ Jika ingin mereset total aplikasi ke kondisi awal, cukup hapus file `gitflow_session.dat` secara manual lalu jalankan ulang `main.py`.

---

## 🧠 Konsep Struktur Data yang Divisualisasikan

| Konsep CS | Implementasi di Aplikasi |
|---|---|
| Singly Linked List | `CommitNode` dengan pointer `prev` |
| Stack (LIFO) | Riwayat commit — push saat commit, pop saat rewind |
| Dua Stack (Undo/Redo) | Time-travel: Stack utama ↔ Stack rollback |
| Pointer/Reference manual | `fake_address` (alamat memori palsu untuk visualisasi) |
| Hashing | `commit_id` dihasilkan dari SHA-1 (message + timestamp + random) |
| Graph percabangan (fork point) | `_fork_points` pada `BranchManager` |
| Serialization | Auto-save/load dengan `pickle` |

---

## 🖱️ Panduan Penggunaan Singkat

1. Tulis konten di editor teks, isi **Commit Message**, lalu klik **Commit**.
2. Gunakan tombol **◀ Rewind** / **▶ Forward** atau slider untuk time-travel antar commit.
3. Klik **New Branch** untuk membuat branch baru dari HEAD aktif.
4. Gunakan ComboBox **Active Branch** di pojok kanan atas untuk berpindah branch.
5. Klik **Merge** untuk menggabungkan branch ke `main`:
   - Jika tidak ada konflik → merge otomatis sukses.
   - Jika ada konflik → **Conflict Arena** (panel kanan) aktif, pilih pemenang: **Keep Main** atau **Keep Branch**.
6. Semua progres tersimpan otomatis — tutup aplikasi kapan saja, data akan kembali saat dibuka ulang.

---

## 🐞 Troubleshooting

| Masalah | Solusi |
|---|---|
| `ModuleNotFoundError: customtkinter` | Jalankan `pip install customtkinter` |
| Data lama tidak muncul saat dibuka ulang | Pastikan `gitflow_session.dat` berada di folder yang sama dengan `main.py` dan tidak terhapus/ter-rename |
| Ingin mulai dari kondisi bersih | Hapus file `gitflow_session.dat`, lalu jalankan ulang `python main.py` |
| Error saat load sesi lama (file korup) | Aplikasi otomatis fallback ke state baru tanpa crash; hapus file `.dat` yang korup jika error berulang |

---

## 📌 Lisensi & Kredit

Proyek edukasi untuk simulasi konsep struktur data (Stack, Linked List) dan version control sederhana. Dibuat dengan Python, CustomTkinter, dan pickle untuk persistence.
