#!/bin/bash
set -euo pipefail

# ============================
# Deploy Script for ChainKopi
# ============================

# Fungsi untuk menampilkan pesan info
info() {
  echo -e "[INFO] $1"
}

# Fungsi untuk menampilkan pesan error
error() {
  echo -e "[ERROR] $1" >&2
}

# Cek apakah Docker terinstal
if ! command -v docker &> /dev/null; then
  error "Docker tidak terinstal. Silakan install Docker terlebih dahulu."
  exit 1
fi

# Variabel konfigurasi
IMAGE_NAME="chainkopi"
CONTAINER_NAME="chainkopi_container"
# Mapping port: host:container
PORT_MAPPING="-p 5000:5000 -p 5001:5001 -p 5002:5002"

# Build Docker image
info "Membangun Docker image dengan nama '${IMAGE_NAME}'..."
docker build -t "${IMAGE_NAME}" .

# Cek apakah container dengan nama yang sama sudah ada, lalu hapus jika ada
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}\$"; then
  info "Container '${CONTAINER_NAME}' sudah ada. Menghentikan dan menghapus container tersebut..."
  docker rm -f "${CONTAINER_NAME}"
fi

# Jalankan container Docker
info "Menjalankan container Docker '${CONTAINER_NAME}'..."
docker run -d --name "${CONTAINER_NAME}" ${PORT_MAPPING} "${IMAGE_NAME}"

info "Deployment selesai dengan sukses."
