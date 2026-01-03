import re
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
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

# Regex per estrarre sequence e timestamp_ns
pattern_a = re.compile(r"Campione:? ?(\d+)[ -]*\| trasmesso.*timestamp_ns=(\d+)")
pattern_b = re.compile(r"Campione:? ?(\d+)[ -]*\| ricevuto.*timestamp_ns=(\d+)")

# Estrai {sequence: timestamp_ns} da lab_a
seq2ns_a = {}
with open(log_file_a, 'r') as f:
    for line in f:
        match = pattern_a.search(line)
        if match:
            sequence = int(match.group(1))
            ts_ns = int(match.group(2))
            seq2ns_a[sequence] = ts_ns

# Estrai {sequence: timestamp_ns} da lab_b
seq2ns_b = {}
with open(log_file_b, 'r') as f:
    for line in f:
        match = pattern_b.search(line)
        if match:
            sequence = int(match.group(1))
            ts_ns = int(match.group(2))
            seq2ns_b[sequence] = ts_ns

# Diagnostica: mostra i primi/ultimi 10 sequence
seqs_a = sorted(seq2ns_a.keys())
seqs_b = sorted(seq2ns_b.keys())
print(f"Sequence in lab_a: {seqs_a[:10]} ... {seqs_a[-10:] if len(seqs_a)>10 else ''}")
print(f"Sequence in lab_b: {seqs_b[:10]} ... {seqs_b[-10:] if len(seqs_b)>10 else ''}")
seqs_common = sorted(set(seq2ns_a.keys()) & set(seq2ns_b.keys()))
print(f"Sequence in comune: {seqs_common[:10]} ... {seqs_common[-10:] if len(seqs_common)>10 else ''}")

# Calcola il delay per ogni sequence in comune (in ms)
deltas = []
for seq in seqs_common:
    delay_ms = (seq2ns_b[seq] - seq2ns_a[seq]) / 1_000_000
    deltas.append(delay_ms)

if not deltas:
    print("Nessun delay calcolato tra lab_a e lab_b.")
    exit(1)

plt.figure(figsize=(10,6))
sns.histplot(deltas, bins=50, color='skyblue', edgecolor='black', stat='density', label='Istogramma')

# Calcola la PDF usando il kernel density estimation
kde = sns.kdeplot(deltas, color='red', linewidth=2, label='PDF (KDE)')

# Calcola il valore per cui la PDF è massima
x = kde.get_lines()[0].get_xdata()
y = kde.get_lines()[0].get_ydata()

if len(x) > 0 and len(y) > 0:
    max_idx = np.argmax(y)
    max_x = x[max_idx]
    max_y = y[max_idx]
    plt.axvline(max_x, color='green', linestyle='--', label=f'Max PDF: {max_x:.2f} ms')
    plt.text(max_x, max_y, f'{max_x:.2f} ms', color='green', fontsize=10, ha='left', va='bottom')
    print(f"Valore massimo PDF: {max_y:.4f} (densità) per delta log-origine = {max_x:.2f} ms")

plt.title('PDF Delta log-origine (ms)')
plt.xlabel('Delta log-origine [ms]')
plt.ylabel('Densità')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

now = datetime.now()
timestamp_ns = time.time_ns()
logger.info(f"Campione: {sequence} - | trasmesso | timestamp_ns={timestamp_ns}")
