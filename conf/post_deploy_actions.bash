#!/bin/bash

# abort on any errors
set -e

# check that we are in the expected directory
cd `dirname $0`/..

source .venv/bin/activate

./manage.py migrate

# gather all the static files in one place
./manage.py collectstatic --noinput
