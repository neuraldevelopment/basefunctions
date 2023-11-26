echo `pwd`
# -------------------------------------------------
pip3 install --upgrade pip
pip3 install --user -r ./requirements.txt
pip3 install -e .
# -------------------------------------------------
set -a
. ./.env
set +a
# -------------------------------------------------
git config --global --add safe.directory .
git config --global user.name "\"${USERNAME}\""
git config --global user.email "\"${USEREMAIL}\""
# -------------------------------------------------
