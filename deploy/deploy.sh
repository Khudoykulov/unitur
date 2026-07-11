#!/bin/bash
# =============================================================================
# Unitur – Deploy / update script
# Run as the 'unitur' user (or root with sudo -u unitur)
# Usage: bash deploy/deploy.sh
# =============================================================================
set -e

APP_DIR="/var/www/unitur"
VENV="$APP_DIR/.venv"
PYTHON="$VENV/bin/python"
PIP="$VENV/bin/pip"
MANAGE="$PYTHON $APP_DIR/manage.py"

echo ""
echo "=============================="
echo " Unitur – Deploying..."
echo "=============================="

cd $APP_DIR

# --- Pull latest code ---
echo "[1/8] Pulling latest code..."
git pull origin main

# --- Create/update virtual environment ---
echo "[2/8] Updating virtual environment..."
if [ ! -d "$VENV" ]; then
    python3.13 -m venv $VENV
fi
$PIP install --upgrade pip
$PIP install -r requirements.txt

# --- Collect static files (static/css/tailwind.css is a committed, pre-built
#     file — no Node/npm build step needed) ---
echo "[3/7] Collecting static files..."
DJANGO_SETTINGS_MODULE=config.settings $MANAGE collectstatic --noinput

# --- Run database migrations ---
echo "[4/7] Running migrations..."
DJANGO_SETTINGS_MODULE=config.settings $MANAGE migrate --noinput

# --- Compile translation files ---
echo "[5/7] Compiling translations..."
DJANGO_SETTINGS_MODULE=config.settings $MANAGE compilemessages 2>/dev/null || \
    $PYTHON generate_translations.py

# --- Clear cache ---
echo "[6/7] Clearing Redis cache..."
DJANGO_SETTINGS_MODULE=config.settings $MANAGE shell -c \
    "from django.core.cache import cache; cache.clear(); print('Cache cleared.')" 2>/dev/null || true

# --- Restart services ---
echo "[7/7] Restarting services..."
sudo systemctl restart unitur-gunicorn
sudo systemctl restart unitur-celery
sudo systemctl restart unitur-celery-beat

echo ""
echo "=============================="
echo " Deploy complete! ✓"
echo "=============================="
echo "Gunicorn : $(sudo systemctl is-active unitur-gunicorn)"
echo "Celery   : $(sudo systemctl is-active unitur-celery)"
echo "Beat     : $(sudo systemctl is-active unitur-celery-beat)"
