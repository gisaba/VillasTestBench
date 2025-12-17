#!/bin/bash

# Assicurati che lo script venga eseguito con bash
if [ -z "$BASH_VERSION" ]; then
    echo "Questo script deve essere eseguito con bash, non con sh."
    echo "Esegui: bash $(basename "$0")"
    exit 1
fi

echo $1

rm dpsim_local/logs/simulation_output.csv
rm lab_a/logs/log_*.log    
rm lab_b/logs/log_*.log 

sh run_complete_simulation.sh

mkdir -p "./TEST/$1" || exit 1

mv ./dpsim_local/logs/simulation_output.csv "./TEST/$1/simulation_output.csv"

mv ./lab_a/logs/log_*.log "./TEST/$1/"