#!/bin/sh
docker run --env-file ../.env  -v ./:/app -t antoniopicone/dpsim-arm64-dev:1.0.3 python3 /app/rl_switch_dp.py

# docker run --env-file ../.env  -v ./:/app -t antoniopicone/dpsim-arm64-dev:1.0.3 python3 /app/rl_switch_emt.py
