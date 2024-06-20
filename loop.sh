#!/bin/bash

deactivate
. .venv/bin/activate

if [[ $1 ]] && [ $1 == 'dev' ]; then
envPath=.dev.env
else
envPath=.env
fi
source $envPath && export $(cut -d= -f1 $envPath)

while true; do
python sql.py --prod >> sql.log 2>&1
sleep 60
done