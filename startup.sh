#!/usr/bin/env bash
python -c 'from app import init_db; init_db()'
gunicorn app:app
