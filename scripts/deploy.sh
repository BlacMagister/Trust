#!/bin/bash
# Build image Docker
docker build -t chainkopi .

# Jalankan container Docker
docker run -d -p 5000:5000 -p 5001:5001 -p 5002:5002 chainkopi
