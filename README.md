# GitFlow Sim 🔀
**Interactive Data Structure & Version Control Simulator**

Proyek tugas akhir / portofolio Struktur Data menggunakan Python + CustomTkinter.

---

## Struktur File
```
gitflow_sim/
├── backend.py      # Struktur data murni (Stack, CommitNode, BranchManager)
├── main.py         # GUI lengkap (Panel Kiri, Tengah, Kanan)
├── requirements.txt
└── README.md
```

## Cara Menjalankan
```bash
pip install customtkinter
python main.py
```

## Fitur Tahap 2 (Implemented)
- ✅ Panel Kiri: Stack visual dengan alamat memori buatan & TOP POINTER
- ✅ Panel Tengah: Editor file, commit, timeline, rewind/forward, slider
- ✅ Panel Kanan: Conflict Arena (placeholder, aktif saat merge conflict)
- ✅ Animasi push/pop (highlight kartu)
- ✅ Multi-branch support
- ✅ Time-travel via slider

## Tahap 3 (berikutnya)
- Animasi pointer bergerak di Panel Kiri
- Conflict Arena visual lebih detail
- Visualisasi tree branch di Panel Kanan
