#!/bin/bash
set -euo pipefail

# ============================
# Install Script for ChainKopi
# ============================
# Skrip ini akan menginstall semua dependensi Python yang terdaftar di requirements.txt.

# Fungsi untuk menampilkan pesan info
info() {
  echo -e "[INFO] $1"
}

# Fungsi untuk menampilkan pesan error
error() {
  echo -e "[ERROR] $1" >&2
}

# Pastikan file requirements.txt ada
if [ ! -f "requirements.txt" ]; then
  error "File requirements.txt tidak ditemukan. Pastikan file tersebut ada di direktori ini."
  exit 1
fi

# Cek apakah pip tersedia (gunakan pip3 jika tersedia)
if command -v pip3 &> /dev/null; then
  PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
  PIP_CMD="pip"
else
  error "pip tidak ditemukan. Pastikan Python dan pip telah terinstal."
  exit 1
fi

info "Menginstall dependensi Python menggunakan ${PIP_CMD}..."
${PIP_CMD} install -r requirements.txt

info "Instalasi dependensi selesai."
exit 0
