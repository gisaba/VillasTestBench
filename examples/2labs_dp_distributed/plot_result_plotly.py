import json
import pandas as pd
import numpy as np
import math
import glob
import argparse
import os
import re
from datetime import datetime
from plotly.subplots import make_subplots
import plotly.graph_objects as go

def parse_log_file(filepath):
    magnitudes = []
    phases = []
    
    with open(filepath, 'r') as file:
        for line in file:
            try:
                data = json.loads(line)
                if isinstance(data['data'][0], dict):
                    real = data['data'][0]['real']
                    imag = data['data'][0]['imag']
                    magnitude = (real**2 + imag**2)**0.5
                    phase = np.angle(complex(real, imag))
                else:
                    magnitude = data['data'][0]
                    phase = 0  # Se non è un numero complesso, la fase è 0
                magnitudes.append(magnitude)
                phases.append(phase)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Errore durante l'elaborazione della riga: {line.strip()}")
                print(f"Errore: {e}")
    
    return magnitudes, phases

def get_most_recent_file(directory, pattern):
    """
    Trova il file più recente in una directory che corrisponde a un pattern.
    
    Args:
        directory (str): Directory in cui cercare
        pattern (str): Pattern regex per filtrare i file
        
    Returns:
        str: Percorso completo al file più recente o None se non trovato
    """
    if not os.path.isdir(directory):
        print(f"Errore: La directory '{directory}' non esiste.")
        return None
        
    # Trova tutti i file che corrispondono al pattern
    files = []
    pattern_re = re.compile(pattern)
    
    for file in os.listdir(directory):
        if pattern_re.match(file):
            full_path = os.path.join(directory, file)
            if os.path.isfile(full_path):
                files.append((full_path, os.path.getmtime(full_path)))
    
    if not files:
        print(f"Nessun file trovato in '{directory}' che corrisponde al pattern '{pattern}'")
        return None
        
    # Ordina per data di modifica (più recente prima)
    files.sort(key=lambda x: x[1], reverse=True)
    return files[0][0]

def parse_arguments():
    """
    Analizza gli argomenti da riga di comando.
    
    Returns:
        argparse.Namespace: Gli argomenti analizzati
    """
    parser = argparse.ArgumentParser(description='Visualizza i risultati della simulazione DESF e DPSim')
    
    # Argomenti obbligatori
    parser.add_argument('--desf-dir', '-d', required=True,
                        help='Directory contenente i file di log DESF')
    parser.add_argument('--dpsim-dir', '-p', required=True,
                        help='Directory contenente i file CSV di DPSim')
    
    # Argomenti opzionali
    parser.add_argument('--current-pattern', default=r'log_current.*\.log$',
                        help='Pattern regex per i file di corrente DESF (default: log_current.*\.log$)')
    parser.add_argument('--voltage-pattern', default=r'log_voltage.*\.log$',
                        help='Pattern regex per i file di tensione DESF (default: log_voltage.*\.log$)')
    parser.add_argument('--csv-pattern', default=r'.*\.csv$',
                        help='Pattern regex per i file CSV DPSim (default: .*\.csv$)')
    parser.add_argument('--title', '-t', default='Confronto Modulo e Fase - Corrente e Tensione',
                        help='Titolo del grafico')
    parser.add_argument('--output', '-o', 
                        help='Percorso dove salvare il grafico come file HTML')
    
    return parser.parse_args()

def main():
    # Analizza gli argomenti da riga di comando
    args = parse_arguments()
    
    # Trova i file più recenti nelle directory specificate
    current_file = get_most_recent_file(args.desf_dir, args.current_pattern)
    voltage_file = get_most_recent_file(args.desf_dir, args.voltage_pattern)
    csv_file = get_most_recent_file(args.dpsim_dir, args.csv_pattern)
    
    # Verifica che i file siano stati trovati
    if not current_file or not voltage_file or not csv_file:
        print("Errore: Impossibile trovare tutti i file necessari.")
        return
    
    print(f"File corrente DESF: {current_file}")
    print(f"File tensione DESF: {voltage_file}")
    print(f"File CSV DPSim: {csv_file}")
    
    # Parsing dei file di log
    current_dp_magnitudes, current_dp_phases = parse_log_file(current_file)
    voltage_dp_magnitudes, voltage_dp_phases = parse_log_file(voltage_file)
    
    # Dividi il modulo DP per sqrt(2)
    current_dp_magnitudes = [magnitude / math.sqrt(2) for magnitude in current_dp_magnitudes]
    voltage_dp_magnitudes = [magnitude / math.sqrt(2) for magnitude in voltage_dp_magnitudes]
    
    # Converti la fase da radianti a gradi
    current_dp_phases = np.degrees(current_dp_phases)
    voltage_dp_phases = np.degrees(voltage_dp_phases)
    
    # Leggi il file CSV
    try:
        data = pd.read_csv(csv_file)
    except Exception as e:
        print(f"Errore durante la lettura del file CSV: {e}")
        return

    # Rimuovi eventuali spazi extra dai nomi delle colonne
    data.columns = data.columns.str.strip()

    # Calcola il modulo e la fase della tensione per n3.v.im e n3.v.re
    data['n3.v.magnitude'] = (data['n3.v.im']**2 + data['n3.v.re']**2)**0.5 / math.sqrt(2)
    data['n3.v.phase'] = np.degrees(np.angle(data['n3.v.re'] + 1j * data['n3.v.im']))

    # Calcola il modulo e la fase della corrente per r1.i_intf.im e r1.i_intf.re
    data['r1.i.magnitude'] = (data['r1.i_intf.im']**2 + data['r1.i_intf.re']**2)**0.5 / math.sqrt(2)
    data['r1.i.phase'] = np.degrees(np.angle(data['r1.i_intf.re'] + 1j * data['r1.i_intf.im']))

    # Creazione di una figura con più subplot
    fig = make_subplots(
        rows=4, cols=1,
        subplot_titles=(
            "Confronto Modulo - Corrente",
            "Confronto Fase - Corrente",
            "Confronto Modulo - Tensione",
            "Confronto Fase - Tensione"
        )
    )

    # Modulo Corrente
    fig.add_trace(go.Scatter(y=current_dp_magnitudes, mode='lines', name='Modulo Corrente DP (DESF)', line=dict(color='green')), row=1, col=1)
    fig.add_trace(go.Scatter(y=data['r1.i.magnitude'], mode='lines', name='Modulo Corrente DP (DPSIM)', line=dict(color='blue', dash='dot')), row=1, col=1)

    # Fase Corrente
    fig.add_trace(go.Scatter(y=current_dp_phases, mode='lines', name='Fase Corrente DP (DESF)', line=dict(color='orange')), row=2, col=1)
    fig.add_trace(go.Scatter(y=data['r1.i.phase'], mode='lines', name='Fase Corrente DP (DPSIM)', line=dict(color='blue', dash='dot')), row=2, col=1)

    # Modulo Tensione
    fig.add_trace(go.Scatter(y=voltage_dp_magnitudes, mode='lines', name='Modulo Tensione n3 DP (DESF)', line=dict(color='green')), row=3, col=1)
    fig.add_trace(go.Scatter(y=data['n3.v.magnitude'], mode='lines', name='Modulo Tensione n3 DP (DPSIM)', line=dict(color='blue', dash='dot')), row=3, col=1)

    # Fase Tensione
    fig.add_trace(go.Scatter(y=voltage_dp_phases, mode='lines', name='Fase Tensione n3 DP (DESF)', line=dict(color='orange')), row=4, col=1)
    fig.add_trace(go.Scatter(y=data['n3.v.phase'], mode='lines', name='Fase Tensione n3 DP (DPSIM)', line=dict(color='blue', dash='dot')), row=4, col=1)

    # Layout del grafico
    fig.update_layout(
        title=args.title,
        height=1200,  # Altezza totale del grafico
        margin=dict(t=150, b=50, l=50, r=50),  # Margini per il layout
        showlegend=True,  # Abilita la legenda globale
        legend=dict(
            orientation="h",  # Orientamento orizzontale
            x=0,  # Posizione orizzontale (sinistra)
            y=1.1,  # Posizione verticale (sopra il grafico)
            xanchor="left",  # Allinea la legenda a sinistra
            yanchor="bottom"  # Allinea la legenda in basso rispetto alla posizione specificata
        )
    )

    # Mostra o salva il grafico
    if args.output:
        fig.write_html(args.output)
        print(f"Grafico salvato come: {args.output}")
    else:
        fig.show()

if __name__ == "__main__":
    main()