#!/usr/bin/env bash
# Starts Diaspora (8501) and Vigil (8502) together. Ctrl+C stops both.
cd "$(dirname "$0")"
[ -d venv ] || { echo "Run 'bash setup.sh' first."; exit 1; }
export PYTHONPATH="$(pwd)/packages"
./venv/bin/streamlit run apps/diaspora-platform/diaspora_dashboards/app.py --server.port 8501 --server.headless true > diaspora.log 2>&1 &
D=$!
./venv/bin/streamlit run apps/vigil-platform/vigil_dashboards/app.py --server.port 8502 --server.headless true > vigil.log 2>&1 &
V=$!
trap 'trap - INT TERM; echo; echo "Stopping..."; kill $D $V 2>/dev/null; wait; exit 0' INT TERM
sleep 4
echo "Diaspora: http://localhost:8501"
echo "Vigil:    http://localhost:8502"
echo "Logs: diaspora.log, vigil.log   |   Press Ctrl+C to stop both."
wait
