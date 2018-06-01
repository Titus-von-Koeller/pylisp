while true; do clear && python test-nodes.py "$@"; inotifywait -e create,modify pylisp/*.py *.py 2>/dev/null; done
