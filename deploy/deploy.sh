#!/bin/bash
# l3ou9's deploy script (Session 1, "Never type it twice").
set -e   # stop at the first error

echo "Restarting the shop..."
sudo systemctl restart shop
sleep 2
curl -fsS http://127.0.0.1:8000/health
echo
echo "Deploy OK"
