#!/bin/bash
set -euo pipefail

# ============================
# Setup Environment for ChainKopi
# ============================
# Skrip ini membuat folder untuk data blockchain dan
# menghasilkan file konfigurasi .env jika belum ada.

# Fungsi untuk menampilkan pesan info
info() {
  echo -e "[INFO] $1"
}

# Fungsi untuk menampilkan pesan error
error() {
  echo -e "[ERROR] $1" >&2
}

# 1. Membuat folder data jika belum ada
DATA_DIR="data"
if [ ! -d "$DATA_DIR" ]; then
  info "Membuat folder data: $DATA_DIR"
  mkdir -p "$DATA_DIR"
else
  info "Folder data sudah ada: $DATA_DIR"
fi

# 2. Membuat file .env dengan konfigurasi default jika belum ada
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
  info "Membuat file konfigurasi default: $ENV_FILE"
  cat <<EOF > "$ENV_FILE"
# Konfigurasi default untuk ChainKopi
NODE_ADDRESS=http://localhost:5000
PORT=5000
LOG_LEVEL=INFO
EOF
  info ".env file berhasil dibuat."
else
  info "File .env sudah ada. Melewati pembuatan file konfigurasi."
fi

info "Setup selesai. Anda dapat memulai aplikasi ChainKopi."

exit 0
