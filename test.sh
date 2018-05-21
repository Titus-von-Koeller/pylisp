while true; do clear && python test-nodes.py "$@"; inotifywait -e create,modify test-nodes.py nodes.py 2>/dev/null; done
