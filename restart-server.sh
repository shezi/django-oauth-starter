#/bin/bash

cd server/
source env/bin/activate
rm dev.db
python manage.py syncdb --noinput
python manage.py loaddata test_consumer.json
python manage.py runserver
