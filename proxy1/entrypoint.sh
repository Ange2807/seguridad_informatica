#!/bin/sh
set -e

CERT_DIR=/etc/nginx/certs
CERT_FILE="$CERT_DIR/cert.pem"
KEY_FILE="$CERT_DIR/key.pem"

mkdir -p "$CERT_DIR"

if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
  openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
    -keyout "$KEY_FILE" -out "$CERT_FILE" \
    -subj "/C=SV/O=Empresa/CN=plataforma.empresa.local"
fi

exec nginx -g "daemon off;"
