#!/usr/bin/env bash
# Render build script — installs deps, collects static, runs migrations
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate --no-input
