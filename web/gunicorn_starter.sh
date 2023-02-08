#!/bin/sh
# Start server on 2 threads
gunicorn run:app -w 2 --threads 2 -b 0.0.0.0:5000 --max-requests 10000 --timeout 5 --keep-alive 5 --log-level info
