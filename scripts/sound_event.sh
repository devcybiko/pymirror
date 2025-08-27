filename="$1"
if [[ "$filename" == "" ]]; then
  echo "$0 <filename>"
  exit 1
fi
curl -X POST "http://rpi01.local:8080/event" \
  -H "Content-Type: application/json" \
  -d '{"event":"SoundEvent", "filename": "'$filename'"}'