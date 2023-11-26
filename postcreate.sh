echo `pwd`
# -------------------------------------------------
set -a
. ./.env
set +a
# -------------------------------------------------
git config --global user.name = "\"${USERNAME}\""
git config --global user.email = "\"${USEREMAIL}\""
# -------------------------------------------------
pip3 install --upgrade pip
pip3 install --user -r ./requirements.txt
pip3 install -e .
# -------------------------------------------------
