import socket
import json
import math
import os
import time as time_module
import dpsimpy
import sys
import logging
from io import StringIO
from datetime import datetime, timezone
import time

# Configurazione logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
LOG_FORMAT = os.getenv('LOG_FORMAT', '%(asctime)s - %(levelname)s - %(message)s')
LOG_DATE_FORMAT = os.getenv('LOG_DATE_FORMAT', '%Y-%m-%d %H:%M:%S.%f')
LOG_TO_FILE = os.getenv('LOG_TO_FILE', 'false').lower() == 'true'
LOG_FILENAME = os.getenv('LOG_FILENAME', 'dpsim_log')
OUTPUT_DIR = os.getenv('OUTPUT_DIR', '/app/logs')

# Configurazione del logger
logger = logging.getLogger('dpsim_lab_b')
numeric_level = getattr(logging, LOG_LEVEL, logging.INFO)
logger.setLevel(numeric_level)

# Configurazione formatter
formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)

# Configurazione handlers
handlers = []

# Sempre aggiungere lo StreamHandler per l'output su console
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
handlers.append(stream_handler)

# Se richiesto, aggiungere anche il FileHandler per l'output su file
if LOG_TO_FILE:
    try:
        # Assicurarsi che la directory di output esista
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Creare un nome file con timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filepath = os.path.join(OUTPUT_DIR, f"{LOG_FILENAME}_lab_b_{timestamp}.log")
        
        file_handler = logging.FileHandler(log_filepath)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
        logger.info(f"Logging to file: {log_filepath}")
    except Exception as e:
        print(f"Error setting up file logging: {str(e)}")

# Aggiungere tutti gli handlers al logger
for handler in handlers:
    logger.addHandler(handler)

# Disabilita completamente il logging se richiesto
if os.getenv('DISABLE_LOGGING', 'false').lower() == 'true':
    logger.disabled = True

# Configurazione
HOST_DEST = os.getenv('HOST_DEST', 'villas_lab_b')
HOST_SOURCE = os.getenv('HOST_SOURCE', '0.0.0.0')
PORT_DEST = int(os.getenv('PORT_DEST', '12002'))
PORT_SOURCE = int(os.getenv('PORT_SOURCE', '12003'))
TIME_STEP_MILLIS = float(os.getenv('TIME_STEP_MILLIS', '1'))
TAU_MILLIS = float(os.getenv('TAU_MILLIS', '1'))
FREQUENZA = float(os.getenv('FREQUENZA', '50'))
TIME_STOP = float(os.getenv('TIME_STOP', '1'))
ITERATIONS = int(float(os.getenv('TIME_STOP', '1'))*1000/(TIME_STEP_MILLIS))

# Tensione di bootstrap
BOOTSTRAP_VOLTAGE_REAL = float(os.getenv('BOOTSTRAP_VOLTAGE_REAL', '0.0'))
BOOTSTRAP_VOLTAGE_IMAG = float(os.getenv('BOOTSTRAP_VOLTAGE_IMAG', '0.0'))

def send_bootstrap_voltage(sequence):
    payload = [{
        "sequence": sequence,
        "data": [{
            "real": BOOTSTRAP_VOLTAGE_REAL,
            "imag": BOOTSTRAP_VOLTAGE_IMAG
        }]
    }]
    
    sock_tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_tx.sendto(json.dumps(payload).encode(), (HOST_DEST, PORT_DEST))
    logger.debug(f"Sent bootstrap voltage to {HOST_DEST}: {payload}")

def start_simulation():
    
    name = 'VILLAS_test'
    
    inizio = time_module.perf_counter()

    # Nodes
    gnd = dpsimpy.dp.SimNode.gnd
    n1 = dpsimpy.dp.SimNode('n1')
    n2 = dpsimpy.dp.SimNode('n2')
    
    # Components
    cs = dpsimpy.dp.ph1.CurrentSource('cs')
    cs.set_parameters(I_ref=complex(0,0))
    
    r1 = dpsimpy.dp.ph1.Resistor('r1')
    r1.set_parameters(R=10)

    r2 = dpsimpy.dp.ph1.Resistor('r2')
    r2.set_parameters(R=10)
    
    # Add switch
    #sw = dpsimpy.dp.ph3.SeriesSwitch('StepLoad', dpsimpy.LogLevel.debug)
    #sw.set_parameters(1e9, 0.1)
    sw = dpsimpy.dp.ph1.Switch('StepLoad', dpsimpy.LogLevel.debug)
    sw.set_parameters(1e9, 0.01, False)
    sw.open()

    # Inizializzazione tensioni dei nodi
    n1.set_initial_voltage(complex(0,0))
    
    # Connessione componenti
    cs.connect([gnd, n1])
    r1.connect([gnd, n1])
    r2.connect([n2, n1])
    sw.connect([n2, gnd])

    # Setup sistema
    system = dpsimpy.SystemTopology(FREQUENZA, [gnd, n1, n2], [cs, r1, r2, sw])
    
    # Setup simulazione
    sim = dpsimpy.Simulation(name)
    sim.set_domain(dpsimpy.Domain.DP)
    sim.set_system(system)
    
    _time_step = TIME_STEP_MILLIS/1000
    logger.info(f'LAB B TIMESTEP = {TIME_STEP_MILLIS} ms')
    sim.set_time_step(_time_step)
    
    _time_stop = TIME_STOP
    sim.set_final_time(_time_stop)

    # Events
    sw_on = dpsimpy.event.SwitchEvent(0.1, sw, True)
    sim.add_event(sw_on)

    sw_off = dpsimpy.event.SwitchEvent(0.2, sw, False)
    sim.add_event(sw_off)

    sim.start()

    return sim,cs,n1

def next_simulation(sim,cs,n1,current_phasor,sequence,time_step):
    
    inizio = time_module.perf_counter()

    cs.set_parameters(I_ref=current_phasor)

    sim.next()
    sequence=sequence+1
            
    # Lettura tensione ai capi del resistore
    v_out = n1.attr("v")
    
    real_part = v_out.get()[0, 0].real # Parte reale
    imag_part = v_out.get()[0, 0].imag # Parte immaginaria
    
    payload = [{
        "sequence": sequence,
        "data": [{
            "real": real_part,
            "imag": imag_part
        }]
    }]
    
    # Invio risultato
    sock_tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_tx.sendto(json.dumps(payload).encode(), (HOST_DEST, PORT_DEST))
    logger.debug(f"Sent voltage to {HOST_DEST}: {payload}")

    fine = time_module.perf_counter()
    tempo_esecuzione = fine - inizio
    
    if tempo_esecuzione <= (time_step*1000):
        logger.debug(f"Risolto LAB B in: {str(tempo_esecuzione*1000)} msec")
        time_module.sleep((TAU_MILLIS - TIME_STEP_MILLIS)/1000)
    
    return complex(real_part,imag_part)

def udp_receiver(sim,cs,n1):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST_SOURCE, PORT_SOURCE))
    _time_step = TIME_STEP_MILLIS/1000
    _tau = TAU_MILLIS/1000
    sock.settimeout(_tau)  # Timeout di TAU_MILLIS sec per il polling
    
    first_value_received = False
    sequence = 0
    while (sequence <= ITERATIONS):
        try:
            sequence = sequence+1
            if not first_value_received:
                # Invia tensione di bootstrap
                send_bootstrap_voltage(sequence)
                logger.info("Waiting for first current value...")
            
            # Prova a ricevere dati
            data, _ = sock.recvfrom(1024)
            
            logger.debug(f"Received from {HOST_DEST}: {data}")

            current_source = json.loads(data.decode())
            i_real = current_source[0]['data'][0]['real']
            i_imag = current_source[0]['data'][0]['imag']
            
            sequence = current_source[0]['sequence']
            ts = current_source[0]['ts']

            # Log con timestamp_ns per analisi delay
            timestamp_ns = time.time_ns()
            logger.info(f"Campione: {sequence} | ricevuto | timestamp_ns={timestamp_ns} | ts={ts}")
            
            #sequence = current_source[0]['sequence']
            logger.debug(f"Received from {HOST_DEST}: {current_source}")
            
            # Imposta il flag dopo aver ricevuto il primo valore
            first_value_received = True

            # Esegui la simulazione con il valore ricevuto
            next_simulation(sim,cs,n1,complex(i_real, i_imag),sequence,_time_step)
            
        except socket.timeout:
            # Se non abbiamo ancora ricevuto il primo valore, continua il bootstrap
            if not first_value_received:
                continue
            else:
                # Se abbiamo già ricevuto almeno un valore, usa l'ultimo valore valido
                logger.warning("Timeout: no new current value received")
        
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Errore nel parsing JSON: {str(e)}")
        except Exception as e:
            logger.error(f"Errore receiver: {str(e)}")
    logger.info("Simulation completed")
    sys.exit()

def setup_realtime_scheduling():
    param = os.sched_param(os.sched_get_priority_max(os.SCHED_RR))
    os.sched_setscheduler(0, os.SCHED_RR, param)
    logger.info(f"Scheduling configurato: {os.sched_getscheduler(0)}")

if __name__ == "__main__":
    time_module.sleep(2)
    setup_realtime_scheduling()
    sim,cs,n1 = start_simulation()
    udp_receiver(sim,cs,n1)