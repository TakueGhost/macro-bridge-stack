#!/usr/bin/env python3
"""
setup_structure.py
Run this ONCE from the root of macro_bridge_stack.
Creates the clean folder structure and moves any existing
memo and report files into the right places.
"""

import os
import shutil
import glob

ROOT = os.path.dirname(os.path.abspath(__file__))

folders = [
    os.path.join(ROOT, "outputs", "regime_memos"),
    os.path.join(ROOT, "outputs", "narrative_reports"),
]

print("Creating folder structure...")
for folder in folders:
    os.makedirs(folder, exist_ok=True)
    print(f"  OK  {folder}")

# Move any regime_memo_*.txt from root into outputs/regime_memos/
memos = glob.glob(os.path.join(ROOT, "regime_memo_*.txt"))
for f in memos:
    dest = os.path.join(ROOT, "outputs", "regime_memos", os.path.basename(f))
    shutil.move(f, dest)
    print(f"  Moved {os.path.basename(f)} -> outputs/regime_memos/")

# Move any narrative_report_*.txt from root into outputs/narrative_reports/
reports = glob.glob(os.path.join(ROOT, "narrative_report_*.txt"))
for f in reports:
    dest = os.path.join(ROOT, "outputs", "narrative_reports", os.path.basename(f))
    shutil.move(f, dest)
    print(f"  Moved {os.path.basename(f)} -> outputs/narrative_reports/")

# Move any narrative_report_*.txt from agent2/ into outputs/narrative_reports/
agent2_reports = glob.glob(os.path.join(ROOT, "agent2", "narrative_report_*.txt"))
for f in agent2_reports:
    dest = os.path.join(ROOT, "outputs", "narrative_reports", os.path.basename(f))
    shutil.move(f, dest)
    print(f"  Moved agent2/{os.path.basename(f)} -> outputs/narrative_reports/")

print("\nDone. Your structure is now:")
print("""
macro_bridge_stack/
├── agent1/                        <- run: python main.py
├── agent2/                        <- run: python main.py
├── outputs/
│   ├── regime_memos/              <- Agent 1 saves here
│   └── narrative_reports/         <- Agent 2 saves here
├── .env
└── venv/
""")
print("Next steps:")
print("  1. Copy agent1_main.py  -> agent1/main.py")
print("  2. Copy agent2_main.py  -> agent2/main.py")
print("  3. Run this setup script once: python setup_structure.py")
print("  4. cd agent1 && python main.py")
print("  5. cd ../agent2 && python main.py")
