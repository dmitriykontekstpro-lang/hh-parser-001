@echo off
ssh root@85.239.34.67 "cd /root/hh-parser-001 && docker compose logs -f --tail=100"
