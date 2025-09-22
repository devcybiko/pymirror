HOST=`hostname`
cd ./git/pymirror
source ./scripts/rpi/set-venv.sh
./taskmgr.sh configs/$HOST/tasks.json &
./run.sh configs/$HOST/config.json