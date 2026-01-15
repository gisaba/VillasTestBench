#!/bin/bash

# Script per eseguire l'intera pipeline di simulazione DESF + DPSim

set -e  # Termina lo script se un comando fallisce

# Assicurati che lo script venga eseguito con bash
if [ -z "$BASH_VERSION" ]; then
    echo "Questo script deve essere eseguito con bash, non con sh."
    echo "Esegui: bash $(basename "$0")"
    exit 1
fi

rm lab_a/logs/log_*.log  > /dev/null 2>&1 || true
rm lab_b/logs/log_*.log  > /dev/null 2>&1 || true
rm lab_a/app/logs/dpsim_log_*.log  > /dev/null 2>&1 || true
rm lab_b/app/logs/dpsim_log_*.log  > /dev/null 2>&1 || true

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

echo "===== AVVIO SIMULAZIONE COMPLETA DESF + DPSIM ====="
echo "$(date)"
echo

# 1. Esegui la simulazione DPSim
echo "===== AVVIO SIMULAZIONE DPSIM ====="
cd dpsim_local
# Esegui in background e reindirizza l'output
sh run_simulation.sh > /tmp/dpsim_output.log 2>&1 &
pid=$!
show_spinner $pid "Esecuzione simulazione DPSim in corso..."
echo "Simulazione DPSim completata"
cd ..
echo

# 2. Esegui la simulazione DESF con Docker Compose
echo "===== AVVIO SIMULAZIONE DESF ====="
# Esegui in background e reindirizza l'output
docker compose up --build > /tmp/desf_output.log 2>&1 &
pid=$!
show_spinner $pid "Esecuzione simulazione DESF in corso..."

# Verifica che tutti i container siano terminati
printf "Verifica che tutti i container siano terminati... "
while docker ps --filter "name=2labs_dp" | grep -q "2labs_dp"; do
    printf "."  # Mostra un punto per indicare che stiamo ancora aspettando
    sleep 1
done
printf "\033[32m[OK]\033[0m\n"
echo

# 3. Genera i diagrammi
echo "===== GENERAZIONE DIAGRAMMI ====="
# Esegui in background e reindirizza l'output
python3 plot_result_plotly.py --desf-dir lab_a/logs --dpsim-dir dpsim_local/logs > /tmp/plot_output.log 2>&1 &
python3 plot_result_plotly_RMSE.py --desf-dir lab_a/logs --dpsim-dir dpsim_local/logs > /tmp/plot_output.log 2>&1 &
python3 plot_delta_log_origine.py --desf-dir lab_b/logs --dpsim-dir dpsim_local/logs > /tmp/plot_output.log 2>&1 &
pid=$!
show_spinner $pid "Generazione diagrammi in corso..."

# Mostra i file utilizzati per la generazione dei diagrammi
echo "File utilizzati:"
grep "File " /tmp/plot_output.log

echo
echo "===== SIMULAZIONE COMPLETA TERMINATA ====="
echo "$(date)"
