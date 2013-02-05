#! /bin/sh

# 1) Run translate1.sh
# 2) Edit the .po files, translating strings
# 3) Run translate2.sh to compile the translations
# 4) Test

echo
# python2.7 ./setup.py extract_messages
pybabel extract -k tr --omit-header --sort-by-file -F bag/locale/main_mapping.conf -o bag/locale/bag.pot bag
echo
./setup.py update_catalog
