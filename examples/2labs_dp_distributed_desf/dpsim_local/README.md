# DESF DPSim Local Simulation

Questa directory contiene script per eseguire simulazioni locali utilizzando DPSim all'interno del framework DESF (Distributed Electric Simulation Framework).

## rl_switch_dp.py

`rl_switch_dp.py` è uno script che esegue una simulazione DP (Dynamic Phasor) di un circuito RL con uno switch. Lo script è configurabile tramite variabili di ambiente.

### Funzionalità

- Simulazione di un circuito RL con uno switch controllato
- Configurazione tramite variabili di ambiente
- Generazione di file di log con i risultati della simulazione
- Supporto per l'esecuzione in container Docker

### Utilizzo

```bash
python rl_switch_dp.py [--env-file PERCORSO_FILE_VARIABILI]
```

### Parametri

- `--env-file`, `-e`: Percorso al file di variabili da utilizzare (default: ../.env)

### Variabili di ambiente

#### Obbligatorie:
- `TIME_STOP`: Tempo di simulazione
- `TIME_STEP_MILLIS`: Passo di simulazione in millisecondi
- `FREQUENZA`: Frequenza del sistema in Hz
- `V_REF_VS`: Tensione di riferimento
- `BOOTSTRAP_VOLTAGE_REAL`: Parte reale della tensione iniziale
- `BOOTSTRAP_VOLTAGE_IMAG`: Parte immaginaria della tensione iniziale

#### Opzionali:
- `OUTPUT_FILENAME`: Nome del file di output (default: simulation_output)
- `OUTPUT_DIR`: Directory di output per i file di log (default: ./log)

### Esecuzione con Docker

Lo script viene eseguito in un container Docker utilizzando l'immagine `antoniopicone/dpsim-arm64-dev:1.0.3`:

```bash
./run_simulation.sh
```

### Struttura del circuito simulato

Il circuito simulato è composto da:
- Una sorgente di tensione (vs)
- Un resistore (r1)
- Un induttore (l1)
- Un carico resistivo (rload)
- Un carico resistivo commutabile tramite switch (rload2)
- Uno switch che si attiva a 0.1s e si disattiva a 0.2s

### Output

I risultati della simulazione vengono salvati nella directory specificata dalla variabile `OUTPUT_DIR` con il nome specificato da `OUTPUT_FILENAME`. I file di output contengono le tensioni ai nodi e le correnti nei componenti durante la simulazione.
