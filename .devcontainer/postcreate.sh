pip3 install --upgrade pip
pip3 install --user -r ./requirements.txt
pip3 install -e .
set -o allexport 
source ./.env
set +o allexport
git config --global user.name = "\"${USERNAME}\""
git config --global user.email = "\"${USEREMAIL}\""