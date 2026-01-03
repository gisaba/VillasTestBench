import re
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Seleziona automaticamente il file di log più recente
import glob
import os
log_files = glob.glob('lab_b/app/logs/dpsim_log_lab_b_*.log')
if not log_files:
    print("Nessun file di log trovato.")
    exit(1)
LOG_FILE = max(log_files, key=os.path.getmtime)
print(f"Analizzo il file di log più recente: {LOG_FILE}")

# Regex per estrarre il delta
pattern = re.compile(r"Delta log-origine: ([\d\.]+) ms")

deltas = []

with open(LOG_FILE, 'r') as f:
    for line in f:
        match = pattern.search(line)
        if match:
            deltas.append(float(match.group(1)))

if not deltas:
    print("Nessun delta trovato nel log.")
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
