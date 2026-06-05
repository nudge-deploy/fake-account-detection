import os
import json
import io
import sys
from contextlib import redirect_stdout

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
notebook_path = os.path.join(BASE_DIR, 'notebooks', '05_graph_analytics.ipynb')

print(f"Reading notebook from: {notebook_path}")
if not os.path.exists(notebook_path):
    print("Notebook file does not exist!")
    sys.exit(1)

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Global dictionary to maintain state across cell executions
execution_globals = {}

cell_count = 1
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source_code = "".join(cell['source'])
        print(f"\n--- Running Code Cell {cell_count} ---")
        print(source_code[:120] + "..." if len(source_code) > 120 else source_code)
        
        # Capture stdout
        f_stdout = io.StringIO()
        try:
            with redirect_stdout(f_stdout):
                exec(source_code, execution_globals)
            output_text = f_stdout.getvalue()
            status = "SUCCESS"
        except Exception as e:
            import traceback
            output_text = f_stdout.getvalue() + f"\nException during execution:\n{traceback.format_exc()}"
            status = "FAILED"
            print(f"Error in cell execution: {e}")
            
        print(f"Status: {status}")
        if output_text:
            print("Output:\n" + output_text.strip())
            
        # Update cell outputs in notebook format
        cell['outputs'] = []
        if output_text:
            cell['outputs'].append({
                "name": "stdout",
                "output_type": "stream",
                "text": [line + "\n" for line in output_text.splitlines() if line]
            })
        cell['execution_count'] = cell_count
        cell_count += 1

print(f"\nSaving notebook with execution outputs back to {notebook_path}...")
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("Execution and saving completed successfully!")
