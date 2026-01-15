import math
import dpsimpy
import os
import sys
import argparse
from pathlib import Path

def print_help():
    """Mostra l'help dello script"""
    print("\nDPSim RL Switch Simulation")
    print("========================\n")
    print("Utilizzo: python rl_switch_dp.py [--env-file PERCORSO_FILE_VARIABILI]")
    print("\nParametri:")
    print("  --env-file, -e    Percorso al file di variabili da utilizzare (default: ../.env)")
    print("\nVariabili di ambiente necessarie nel file .env:")
    print("  TIME_STOP               Tempo di simulazione")
    print("  TIME_STEP_MILLIS        Passo di simulazione in millisecondi")
    print("  FREQUENZA               Frequenza del sistema in Hz")
    print("  V_REF_VS                Tensione di riferimento")
    print("  BOOTSTRAP_VOLTAGE_REAL  Parte reale della tensione iniziale")
    print("  BOOTSTRAP_VOLTAGE_IMAG  Parte immaginaria della tensione iniziale")
    print("\nVariabili di ambiente opzionali nel file .env:")
    print("  OUTPUT_FILENAME         Nome del file di output (default: simulation_output)")
    print("  OUTPUT_DIR              Directory di output per i file di log (default: ./log)")
    print("\nEsempio:")
    print("  python rl_switch_dp.py --env-file ../config/.env")
    sys.exit(1)

# Parsing degli argomenti da riga di comando
def parse_arguments():
    parser = argparse.ArgumentParser(description='DPSim RL Switch Simulation', add_help=False)
    parser.add_argument('--env-file', '-e', type=str, default='../.env',
                        help='Percorso al file .env da utilizzare')
    parser.add_argument('--help', '-h', action='store_true', help='Mostra questo messaggio di aiuto')
    
    # Cattura l'errore se vengono forniti argomenti non validi
    try:
        args = parser.parse_args()
        if args.help:
            print_help()
        return args
    except Exception:
        print_help()
        sys.exit(1)

# Lista delle variabili di ambiente necessarie per la simulazione
REQUIRED_ENV_VARS = [
    'TIME_STOP',
    'TIME_STEP_MILLIS',
    'FREQUENZA',
    'V_REF_VS',
    'BOOTSTRAP_VOLTAGE_REAL',
    'BOOTSTRAP_VOLTAGE_IMAG'
]

# Lista delle variabili di ambiente opzionali per la simulazione
OPTIONAL_ENV_VARS = [
    'OUTPUT_FILENAME',
    'OUTPUT_DIR'
]

# Verifica se le variabili di ambiente necessarie sono già definite
def check_env_variables():
    missing_vars = [var for var in REQUIRED_ENV_VARS if os.getenv(var) is None]
    return missing_vars

# Carica le variabili di ambiente dal file specificato
def load_env_file(env_file_path):
    env_path = Path(env_file_path)
    if not env_path.exists():
        print(f"\nErrore: Il file '{env_file_path}' non esiste.")
        print_help()
    
    print(f"\nCaricamento variabili di ambiente da: {env_file_path}")
    
    # Legge il file e imposta le variabili di ambiente
    with open(env_file_path, 'r') as file:
        for line in file:
            line = line.strip()
            # Salta le linee vuote e i commenti
            if not line or line.startswith('#'):
                continue
            # Divide la linea in chiave e valore
            if '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

# Mostra i valori delle variabili di ambiente definite
def show_env_variables():
    print("\nValori delle variabili di ambiente per la simulazione:")
    print("-----------------------------------------------------")
    print("Variabili obbligatorie:")
    for var in REQUIRED_ENV_VARS:
        value = os.getenv(var, 'Non definita')
        print(f"  {var}: {value}")
    
    print("\nVariabili opzionali:")
    for var in OPTIONAL_ENV_VARS:
        value = os.getenv(var, 'Non definita')
        print(f"  {var}: {value}")
    print()

# Parsing degli argomenti
args = parse_arguments()

# Verifica se le variabili di ambiente necessarie sono già definite
missing_vars = check_env_variables()

# Se mancano variabili di ambiente, carica il file .env
if missing_vars:
    print(f"\nVariabili di ambiente mancanti: {', '.join(missing_vars)}")
    load_env_file(args.env_file)
    
    # Verifica nuovamente dopo il caricamento del file .env
    missing_vars = check_env_variables()
    if missing_vars:
        print(f"\nErrore: Le seguenti variabili di ambiente sono ancora mancanti: {', '.join(missing_vars)}")
        print("Assicurati che siano definite nel file .env o nell'ambiente.")
        sys.exit(1)

# Mostra i valori delle variabili di ambiente
show_env_variables()


# Leggi le variabili di ambiente
tsim = float(os.getenv('TIME_STOP'))
time_step = float(os.getenv('TIME_STEP_MILLIS')) / 1000  # Converti da millisecondi a secondi
frequenza = float(os.getenv('FREQUENZA'))

# Nodes
gnd = dpsimpy.dp.SimNode.gnd
n1 =  dpsimpy.dp.SimNode('n1')
n2 =  dpsimpy.dp.SimNode('n2')
n3 =  dpsimpy.dp.SimNode('n3')
n4 =  dpsimpy.dp.SimNode('n4')

# initialize node voltages as in simulunk
# Usa i valori BOOTSTRAP_VOLTAGE_REAL e BOOTSTRAP_VOLTAGE_IMAG
bootstrap_voltage_real = float(os.getenv('BOOTSTRAP_VOLTAGE_REAL'))
bootstrap_voltage_imag = float(os.getenv('BOOTSTRAP_VOLTAGE_IMAG'))
n2.set_initial_voltage(complex(bootstrap_voltage_real, bootstrap_voltage_imag))
n3.set_initial_voltage(complex(bootstrap_voltage_real, bootstrap_voltage_imag))

# Components
vs = dpsimpy.dp.ph1.VoltageSource('vs')
# Usa il valore V_REF_VS
v_ref = float(os.getenv('V_REF_VS'))
vs.set_parameters(V_ref=complex(real=v_ref, imag=0) * math.sqrt(2))
r1 = dpsimpy.dp.ph1.Resistor('r1')
r1.set_parameters(R=1)
l1 = dpsimpy.dp.ph1.Inductor('l1')
l1.set_parameters(L=0.02)

rload = dpsimpy.dp.ph1.Resistor('rload')
rload.set_parameters(R=10)
rload2 = dpsimpy.dp.ph1.Resistor('rload2')
rload2.set_parameters(R=10)

sw = dpsimpy.dp.ph1.Switch('StepLoad', dpsimpy.LogLevel.debug)
sw.set_parameters(1e9, 0.01, False)
sw.open()

vs.connect([gnd, n1])
r1.connect([n2, n1])
l1.connect([n3, n2])
rload.connect([gnd, n3])
rload2.connect([n4, n3])
sw.connect([n4, gnd])

# Usa il valore FREQUENZA dal file .env
system = dpsimpy.SystemTopology(frequenza, [gnd, n1, n2, n3, n4], [vs, r1, l1, rload, rload2, sw])

# Leggi le variabili di ambiente opzionali o usa i valori predefiniti
output_filename = os.getenv('OUTPUT_FILENAME', 'simulation_output')
output_dir = os.getenv('OUTPUT_DIR', './log')

# Crea la directory di output se non esiste
os.makedirs(output_dir, exist_ok=True)

# Imposta la directory di log e crea il logger
dpsimpy.Logger.set_log_dir(output_dir)
logger = dpsimpy.Logger(output_filename)

print(f"\nFile di log: {output_dir}/{output_filename}.csv")


for i in range(1, len(system.nodes)):
    logger.log_attribute("n" + str(i) + ".v", "v", system.nodes[i])
    
logger.log_attribute('r1.i_intf', 'i_intf', r1);

sim = dpsimpy.Simulation(output_filename)
sim.set_domain(dpsimpy.Domain.DP)
sim.set_system(system)
sim.set_time_step(time_step)
sim.set_final_time(tsim)

# Events
sw_on = dpsimpy.event.SwitchEvent(0.1, sw, True)
sim.add_event(sw_on)

sw_off = dpsimpy.event.SwitchEvent(0.2, sw, False)
sim.add_event(sw_off)

sim.add_logger(logger)
sim.run()