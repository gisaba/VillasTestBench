#!/bin/bash

# Script per eseguire l'intera pipeline di simulazione

set -e  # Termina lo script se un comando fallisce

# Assicurati che lo script venga eseguito con bash
if [ -z "$BASH_VERSION" ]; then
    echo "Questo script deve essere eseguito con bash, non con sh."
    echo "Esegui: bash $(basename "$0")"
    exit 1
fi

rm lab_a/logs/log_*.csv  > /dev/null 2>&1 || true
rm lab_a/logs/log_*.tsv  > /dev/null 2>&1 || true
rm lab_b/logs/log_*.log  > /dev/null 2>&1 || true
rm lab_b/logs/log_*.tsv  > /dev/null 2>&1 || true

# Funzione per mostrare un indicatore di progresso
show_spinner() {
  local pid=$1
  local message=$2
  local delay=0.1
  local spinstr='|/-\'
  local temp
  printf "%s " "$message"
  while ps -p $pid > /dev/null; do
    temp=${spinstr#?}
    printf " [%c]  " "$spinstr"
    spinstr=$temp${spinstr%"$temp"}
    sleep $delay
    printf "\b\b\b\b\b\b"
  done
  printf "    \b\b\b\b"
  printf "\033[32m[Completato]\033[0m\n"
}

echo "===== AVVIO SIMULAZIONE COMPLETA DESF ====="
echo "$(date)"
echo

# 2. Esegui la simulazione con Docker Compose
echo "===== AVVIO SIMULAZIONE ====="
# Esegui in background e reindirizza l'output
docker compose --profile villas up --build > /tmp/simulation_output.log 2>&1 &
pid=$!
show_spinner $pid "Esecuzione simulazione in corso CTRL+C per terminare..."

# Verifica che tutti i container siano terminati
printf "Verifica che tutti i container siano terminati... "
while docker ps --filter "name=2nodes" | grep -q "2nodes"; do
    printf "."  # Mostra un punto per indicare che stiamo ancora aspettando
    sleep 1
done
printf "\033[32m[OK]\033[0m\n"
echo

echo
echo "===== SIMULAZIONE COMPLETA TERMINATA ====="
echo "$(date)"
