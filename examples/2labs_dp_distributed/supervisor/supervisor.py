#!/usr/bin/env python3
"""
Supervisore per container Docker DESF

Questo script monitora lo stato dei container specificati e termina tutti
i container quando uno di essi termina l'esecuzione.
"""

import os
import sys
import time
import json
import signal
import subprocess
import logging
from datetime import datetime

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('supervisor')

# Configurazione
PROJECT_NAME = os.getenv('PROJECT_NAME', '2labs_dp')
CONTAINERS_TO_MONITOR = os.getenv('CONTAINERS_TO_MONITOR', 'dpsim_lab_a,dpsim_lab_b').split(',')
CHECK_INTERVAL = float(os.getenv('CHECK_INTERVAL', '1.0'))
GRACE_PERIOD = float(os.getenv('GRACE_PERIOD', '10.0'))
COMPLETION_MESSAGE = os.getenv('COMPLETION_MESSAGE', 'Simulation completed')

def get_container_status(container_name):
    """
    Ottiene lo stato di un container.
    
    Args:
        container_name: Nome del container
        
    Returns:
        dict: Stato del container o None se non trovato
    """
    try:
        cmd = ['docker', 'inspect', f"{PROJECT_NAME}-{container_name}-1", '--format', '{{json .State}}']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.warning(f"Container {container_name} non trovato")
            return None
        
        return json.loads(result.stdout)
    except Exception as e:
        logger.error(f"Errore nell'ispezione del container {container_name}: {str(e)}")
        return None

def get_container_logs(container_name, tail=10):
    """
    Ottiene gli ultimi log di un container.
    
    Args:
        container_name: Nome del container
        tail: Numero di righe da recuperare
        
    Returns:
        str: Log del container o stringa vuota se non trovato
    """
    try:
        cmd = ['docker', 'logs', f"{PROJECT_NAME}-{container_name}-1", '--tail', str(tail)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.warning(f"Impossibile ottenere i log del container {container_name}")
            return ""
        
        return result.stdout
    except Exception as e:
        logger.error(f"Errore nel recupero dei log per {container_name}: {str(e)}")
        return ""

def get_all_containers():
    """
    Ottiene tutti i container del progetto.
    
    Returns:
        list: Lista dei nomi dei container
    """
    try:
        cmd = ['docker', 'ps', '-a', '--filter', f"name={PROJECT_NAME}", '--format', '{{.Names}}']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Errore nell'ottenere la lista dei container: {result.stderr}")
            return []
        
        # Filtra il container supervisore stesso
        containers = [c.strip() for c in result.stdout.split('\n') if c.strip()]
        containers = [c for c in containers if 'supervisor' not in c]
        return containers
    except Exception as e:
        logger.error(f"Errore nell'ottenere la lista dei container: {str(e)}")
        return []

def stop_all_containers():
    """
    Ferma tutti i container del progetto.
    """
    try:
        logger.info(f"Arresto di tutti i container del progetto {PROJECT_NAME}...")
        
        # Ottieni tutti i container del progetto
        containers = get_all_containers()
        
        if not containers:
            logger.warning("Nessun container trovato da arrestare")
            return
        
        # Arresta ogni container individualmente
        for container in containers:
            logger.info(f"Arresto del container {container}...")
            cmd = ['docker', 'stop', container]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Errore nell'arresto del container {container}: {result.stderr}")
            else:
                logger.info(f"Container {container} arrestato con successo")
        
        logger.info("Tutti i container sono stati arrestati con successo")
    except Exception as e:
        logger.error(f"Errore nell'arresto dei container: {str(e)}")

def check_simulation_completed(container_name):
    """
    Verifica se la simulazione è completata controllando i log.
    
    Args:
        container_name: Nome del container
        
    Returns:
        bool: True se la simulazione è completata, False altrimenti
    """
    try:
        logs = get_container_logs(container_name, tail=50)  # Aumentato il numero di righe da controllare
        if not logs:
            return False
            
        # Cerca il messaggio di completamento nei log
        if COMPLETION_MESSAGE in logs:
            logger.info(f"Messaggio '{COMPLETION_MESSAGE}' trovato nei log di {container_name}")
            return True
            
        return False
    except Exception as e:
        logger.error(f"Errore nel controllo del completamento per {container_name}: {str(e)}")
        return False

def check_containers_status():
    """
    Verifica lo stato di tutti i container monitorati.
    
    Returns:
        dict: Dizionario con lo stato di ciascun container
    """
    status = {}
    for container_name in CONTAINERS_TO_MONITOR:
        state = get_container_status(container_name)
        if state is None:
            # Container non trovato, potrebbe essere già terminato
            status[container_name] = {
                'running': False,
                'exists': False
            }
        else:
            status[container_name] = {
                'running': state.get('Running', False),
                'exists': True,
                'exit_code': state.get('ExitCode', None)
            }
    
    return status

def are_all_containers_stopped():
    """
    Verifica se tutti i container monitorati sono terminati.
    
    Returns:
        bool: True se tutti i container sono terminati, False altrimenti
    """
    status = check_containers_status()
    
    # Conta quanti container sono ancora in esecuzione
    running_containers = [name for name, state in status.items() if state['running']]
    
    if not running_containers:
        logger.info("Tutti i container monitorati sono terminati")
        return True
    else:
        logger.debug(f"Container ancora in esecuzione: {', '.join(running_containers)}")
        return False

def is_any_container_stopped():
    """
    Verifica se almeno uno dei container monitorati è terminato.
    
    Returns:
        tuple: (terminato, nome_container)
    """
    status = check_containers_status()
    
    # Verifica se c'è almeno un container che esiste ma non è in esecuzione
    for name, state in status.items():
        if state['exists'] and not state['running']:
            logger.info(f"Container {name} è terminato")
            return True, name
    
    return False, None

def main():
    """
    Funzione principale.
    """
    logger.info(f"Avvio del supervisore per il progetto {PROJECT_NAME}")
    logger.info(f"Monitoraggio dei container: {', '.join(CONTAINERS_TO_MONITOR)}")
    logger.info(f"Il supervisore terminerà tutti i container quando uno di essi termina")
    
    # Gestione dei segnali
    def handle_signal(sig, frame):
        logger.info("Segnale di interruzione ricevuto, arresto in corso...")
        stop_all_containers()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    # Verifica iniziale per assicurarsi che i container esistano
    initial_status = check_containers_status()
    
    # Verifica se tutti i container sono già terminati all'avvio
    if are_all_containers_stopped():
        logger.info("Tutti i container monitorati sono già terminati. Il supervisore terminerà immediatamente.")
        sys.exit(0)  # Termina con codice di uscita 0 (successo)
    
    # Verifica se nessun container esiste
    if not any(status['exists'] for status in initial_status.values()):
        logger.warning("Nessuno dei container monitorati è stato trovato. Uscita.")
        sys.exit(1)  # Termina con codice di uscita 1 (errore)
    
    # Memorizza i container inizialmente in esecuzione
    running_initially = [name for name, state in initial_status.items() if state['running']]
    if not running_initially:
        logger.warning("Nessun container monitorato è in esecuzione. Il supervisore terminerà.")
        sys.exit(0)  # Termina con codice di uscita 0 (successo)
        
    logger.info(f"Container inizialmente in esecuzione: {', '.join(running_initially)}")
    
    # Loop principale
    try:
        while True:
            # Verifica se tutti i container sono terminati
            if are_all_containers_stopped():
                logger.info("Tutti i container monitorati sono terminati. Il supervisore terminerà.")
                sys.exit(0)  # Termina con codice di uscita 0 (successo)
            
            # Verifica se almeno un container è terminato
            stopped, container_name = is_any_container_stopped()
            if stopped:
                logger.info(f"Container {container_name} è terminato. Arresto di tutti gli altri container...")
                
                # Attendi un periodo di grazia
                logger.info(f"Attesa di {GRACE_PERIOD} secondi prima di arrestare gli altri container...")
                time.sleep(GRACE_PERIOD)
                
                # Ferma tutti gli altri container
                stop_all_containers()
                logger.info("Tutti i container sono stati arrestati. Il supervisore terminerà.")
                sys.exit(0)  # Termina con codice di uscita 0 (successo)
            
            # Verifica anche se la simulazione è completata in uno dei container
            for container_name in CONTAINERS_TO_MONITOR:
                if check_simulation_completed(container_name):
                    logger.info(f"Rilevato messaggio di completamento nei log di {container_name}")
                    logger.info(f"Arresto di tutti i container...")
                    
                    # Attendi un periodo di grazia
                    logger.info(f"Attesa di {GRACE_PERIOD} secondi prima di arrestare tutti i container...")
                    time.sleep(GRACE_PERIOD)
                    
                    # Ferma tutti i container
                    stop_all_containers()
                    logger.info("Tutti i container sono stati arrestati. Il supervisore terminerà.")
                    sys.exit(0)  # Termina con codice di uscita 0 (successo)
            
            # Attendi prima del prossimo controllo
            time.sleep(CHECK_INTERVAL)
    
    except KeyboardInterrupt:
        logger.info("Interruzione manuale, arresto in corso...")
        stop_all_containers()
        sys.exit(130)  # Codice di uscita standard per SIGINT
    except Exception as e:
        logger.error(f"Errore nel supervisore: {str(e)}")
        # Ferma i container anche in caso di errore
        logger.info("Arresto di tutti i container a causa di un errore...")
        stop_all_containers()
        sys.exit(1)  # Termina con codice di uscita 1 (errore)

if __name__ == "__main__":
    main()
