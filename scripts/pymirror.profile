cd /Users/greg
cd git/pymirror
git pull
source ./scripts/rpi/set-venv.sh
./taskmgr.sh ./configs/rpi01/tasks.json &
./run.sh ./configs/rpi01/config.json