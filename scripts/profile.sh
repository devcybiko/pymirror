HOST=`hostname`
cd ./git/pymirror
./scripts/purge.sh
git pull
source ./scripts/rpi/set-venv.sh
./taskmgr.sh configs/$HOST/tasks.json &
./run.sh configs/$HOST/config.json
