#/bin/bash

cd client
virtualenv env --distribute
source env/bin/activate
pip install -r dependencies.txt
