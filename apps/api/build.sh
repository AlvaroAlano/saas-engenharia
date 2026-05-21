#!/usr/bin/env bash
# exit on error
set -o errexit

echo "[*] Iniciando Script de Build..."

# Nota: No Render (Ambiente Nativo), o apt-get pode exigir privilégios ou não estar disponível.
# Se o build falhar por falta de permissão, recomendo migrar para Docker ou usar Nixpacks.
# Para bibliotecas como FPDF (atual), estas dependências não são estritamente necessárias, 
# mas são vitais para WeasyPrint/Cairo.

if command -v apt-get >/dev/null; then
  echo "[*] Instalando dependências de sistema para geração de PDF..."
  apt-get update && apt-get install -y \
      libpango-1.0-0 \
      libharfbuzz0b \
      libpangoft2-1.0-0 \
      libpangocairo-1.0-0 \
      libgdk-pixbuf2.0-0 \
      libffi-dev \
      shared-mime-info
else
  echo "[!] apt-get não encontrado. Pulando instalação de pacotes de sistema."
fi

echo "[*] Instalando dependências Python..."
pip install --upgrade pip
pip install -r requirements.txt

echo "[*] Build concluído com sucesso!"
