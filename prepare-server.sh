#/bin/bash

cd server
virtualenv env --distribute
source env/bin/activate
pip install -r dependencies.txt
