#!/bin/bash
set -exo pipefail;
python manage.py makemigrations --merge --no-input;
python manage.py migrate;

