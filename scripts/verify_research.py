"""One permitted research command before independent labels: software fixtures only."""
from pathlib import Path
import os
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
env={**os.environ,'PYTHONPATH':str(root/'research')}
subprocess.run([sys.executable,'-m','unittest','discover','-s','research/tests','-v'],cwd=root,env=env,check=True)
subprocess.run([sys.executable,'-m','pip','check'],cwd=root,env=env,check=True)
print('Permitted software checks complete. No real-data training, annotation or performance claims produced.')
