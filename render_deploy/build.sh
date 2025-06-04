#!/bin/bash
# Script de build para o Render

# Instalar dependências
pip install -U pip
pip install gunicorn
pip install -r requirements_render.txt

# Instalar Playwright
pip install playwright
playwright install-deps
playwright install chromium
