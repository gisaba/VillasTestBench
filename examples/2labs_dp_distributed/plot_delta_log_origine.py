import re
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from scipy.stats import gaussian_kde
import time
from datetime import datetime


# Seleziona automaticamente il file di log più recente

# --- Nuova versione: delay tra lab_a e lab_b usando timestamp_ns ---
import glob
import os

log_files_a = glob.glob('lab_a/app/logs/dpsim_log_lab_a_*.log')
log_files_b = glob.glob('lab_b/app/logs/dpsim_log_lab_b_*.log')
if not log_files_a or not log_files_b:
    print("Nessun file di log trovato in lab_a o lab_b.")
    exit(1)
log_file_a = max(log_files_a, key=os.path.getmtime)
log_file_b = max(log_files_b, key=os.path.getmtime)
print(f"Analizzo: {log_file_a} e {log_file_b}")

import ast
# Regex per estrarre sequence, timestamp_ns e ts
pattern_a = re.compile(r"Campione:? ?(\d+)[ -]*\| trasmesso.*timestamp_ns=(\d+)")
pattern_b = re.compile(r"Campione:? ?(\d+)[ -]*\| ricevuto.*timestamp_ns=(\d+).*ts=([^\n]+)")

# Estrai {sequence: timestamp_ns} da lab_a
seq2ns_a = {}
with open(log_file_a, 'r') as f:
    for line in f:
        match = pattern_a.search(line)
        if match:
            sequence = int(match.group(1))
            ts_ns = int(match.group(2))
            seq2ns_a[sequence] = ts_ns

# Estrai {sequence: (timestamp_ns, ts)} da lab_b
seq2ns_b = {}
seq2ts_b = {}
with open(log_file_b, 'r') as f:
    for line in f:
        match = pattern_b.search(line)
        if match:
            sequence = int(match.group(1))
            ts_ns = int(match.group(2))
            ts_str = match.group(3).strip()
            # ts_str è qualcosa come: {'origin': [1767534673, 277241046]}
            try:
                ts_dict = ast.literal_eval(ts_str)
                if isinstance(ts_dict, dict) and 'origin' in ts_dict:
                    sec, nsec = ts_dict['origin']
                    ts_origin_ns = sec * 1_000_000_000 + nsec
                    seq2ts_b[sequence] = ts_origin_ns
            except Exception as e:
                pass
            seq2ns_b[sequence] = ts_ns

# Diagnostica: mostra i primi/ultimi 10 sequence
seqs_a = sorted(seq2ns_a.keys())
seqs_b = sorted(seq2ns_b.keys())
print(f"Sequence in lab_a: {seqs_a[:10]} ... {seqs_a[-10:] if len(seqs_a)>10 else ''}")
print(f"Sequence in lab_b: {seqs_b[:10]} ... {seqs_b[-10:] if len(seqs_b)>10 else ''}")
seqs_common = sorted(set(seq2ns_a.keys()) & set(seq2ns_b.keys()))
print(f"Sequence in comune: {seqs_common[:10]} ... {seqs_common[-10:] if len(seqs_common)>10 else ''}")


# Calcola il delay tra lab_a e lab_b (in ms)
deltas = []
for seq in seqs_common:
    delay_ms = (seq2ns_b[seq] - seq2ns_a[seq]) / 1_000_000
    deltas.append(delay_ms)

# Calcola il delay tra ricezione e ts origin (in ms)
deltas_ts = []
seqs_common_ts = sorted(set(seq2ts_b.keys()) & set(seq2ns_b.keys()))
for seq in seqs_common_ts:
    delay_ms = (seq2ns_b[seq] - seq2ts_b[seq]) / 1_000_000
    deltas_ts.append(delay_ms)

if not deltas:
    print("Nessun delay calcolato tra lab_a e lab_b.")
    exit(1)


# 4 subplot: 2 istogrammi (conteggio), 2 PDF (KDE)
fig, axs = plt.subplots(2, 2, figsize=(16, 12))



# Primo plot: delay lab_a vs lab_b (conteggio)
sns.histplot(deltas, bins=50, color='skyblue', edgecolor='black', stat='count', label='Istogramma', ax=axs[0,0])
axs[0,0].set_title('Analisi delay End-to-End')
axs[0,0].set_xlabel('delay [ms]')
axs[0,0].set_ylabel('Occorrenze')
axs[0,0].legend()
axs[0,0].grid(True)


# Secondo plot: PDF delay lab_a vs lab_b
if len(deltas) > 1:
    # Calcolo KDE manuale per avere x/y e massimo
    kde = gaussian_kde(deltas)
    x_grid = np.linspace(min(deltas), max(deltas), 500)
    y_grid = kde(x_grid)
    axs[0,1].plot(x_grid, y_grid, color='red', linewidth=2, label='PDF (KDE)')
    axs[0,1].fill_between(x_grid, y_grid, color='red', alpha=0.2)
    max_idx = np.argmax(y_grid)
    max_x = x_grid[max_idx]
    max_y = y_grid[max_idx]
    axs[0,1].axvline(max_x, color='green', linestyle='--', label=f'Max PDF: {max_x:.2f} ms')
    axs[0,1].text(max_x, max_y, f'{max_x:.2f} ms', color='green', fontsize=10, ha='left', va='bottom')
    axs[0,1].set_title('PDF delay End-to-End')
    axs[0,1].set_xlabel('delay [ms]')
    axs[0,1].set_ylabel('Densità')
    axs[0,1].legend()
    axs[0,1].grid(True)
else:
    axs[0,1].set_title('PDF delay End-to-End (pochi dati)')



# Terzo plot: delay tra ricezione e ts origin (conteggio)
if deltas_ts:
    sns.histplot(deltas_ts, bins=50, color='orange', edgecolor='black', stat='count', label='Istogramma', ax=axs[1,0])
    axs[1,0].set_title('Analisi delay Villas nodes')
    axs[1,0].set_xlabel('delay [ms]')
    axs[1,0].set_ylabel('Occorrenze')
    axs[1,0].legend()
    axs[1,0].grid(True)
    # Quarto plot: PDF delay tra ricezione e ts origin
    if len(deltas_ts) > 1:
        kde2 = gaussian_kde(deltas_ts)
        x2_grid = np.linspace(min(deltas_ts), max(deltas_ts), 500)
        y2_grid = kde2(x2_grid)
        axs[1,1].plot(x2_grid, y2_grid, color='blue', linewidth=2, label='PDF (KDE)')
        axs[1,1].fill_between(x2_grid, y2_grid, color='blue', alpha=0.2)
        max_idx2 = np.argmax(y2_grid)
        max_x2 = x2_grid[max_idx2]
        max_y2 = y2_grid[max_idx2]
        axs[1,1].axvline(max_x2, color='green', linestyle='--', label=f'Max PDF: {max_x2:.2f} ms')
        axs[1,1].text(max_x2, max_y2, f'{max_x2:.2f} ms', color='green', fontsize=10, ha='left', va='bottom')
        axs[1,1].set_title('PDF delay Villas nodes')
        axs[1,1].set_xlabel('delay [ms]')
        axs[1,1].set_ylabel('Densità')
        axs[1,1].legend()
        axs[1,1].grid(True)
    else:
        axs[1,1].set_title('PDF delay Villas nodes (pochi dati)')
else:
    axs[1,0].set_title('Nessun dato ts origin trovato')
    axs[1,1].set_title('Nessun dato ts origin trovato')

plt.tight_layout()
plt.show()

now = datetime.now()
timestamp_ns = time.time_ns()
logger.info(f"Campione: {sequence} - | trasmesso | timestamp_ns={timestamp_ns}")
