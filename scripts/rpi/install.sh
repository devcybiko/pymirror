rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
python3 -m venv .venv --system-site-packages
pip install -r ./scripts/rpi/requirements.txt
sudo xargs -a ./scripts/rpi/packages.txt apt-get install -y

