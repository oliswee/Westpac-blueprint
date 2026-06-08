"""
Execute all 6 notebooks sequentially and generate HTML outputs.
Uses cached parquet files to avoid memory issues with raw CSVs.
"""
import os
import sys
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from nbconvert import HTMLExporter
from nbconvert.preprocessors import CellExecutionError

NOTEBOOK_DIR = r"D:\Download_edge\Homeloan_DA\notebooks"
OUTPUT_DIR = os.path.join(NOTEBOOK_DIR, "html_outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

NOTEBOOKS = [
    "01_data_acquisition.ipynb",
    "02_eda_user_profiling.ipynb",
    "03_feature_engineering.ipynb",
    "04_predictive_modeling.ipynb",
    "05_business_simulation.ipynb",
    "06_executive_summary.ipynb",
]


def execute_notebook(notebook_path, output_path, timeout=900):
    """Execute a single notebook and save as HTML."""
    notebook_name = os.path.basename(notebook_path)
    print(f"\n{'='*70}")
    print(f"EXECUTING: {notebook_name}")
    print(f"{'='*70}")

    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)

    ep = ExecutePreprocessor(timeout=timeout, kernel_name='python3')

    if 'kernelspec' not in nb.metadata:
        nb.metadata['kernelspec'] = {
            'display_name': 'Python 3',
            'language': 'python',
            'name': 'python3'
        }

    try:
        ep.preprocess(nb, {'metadata': {'path': NOTEBOOK_DIR}})

        html_exporter = HTMLExporter()
        html_exporter.template_name = 'classic'
        (body, resources) = html_exporter.from_notebook_node(nb)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(body)

        print(f"  ✓ SUCCESS → {output_path}")
        return True

    except CellExecutionError as e:
        print(f"  ✗ CELL ERROR: {str(e)[:500]}")
        return False
    except Exception as e:
        print(f"  ✗ ERROR: {type(e).__name__}: {str(e)[:500]}")
        return False


if __name__ == '__main__':
    print("=" * 70)
    print("WESTPAC BLUEPRINT — BATCH NOTEBOOK EXECUTION")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 70)

    results = {}
    for nb_file in NOTEBOOKS:
        nb_path = os.path.join(NOTEBOOK_DIR, nb_file)
        html_file = nb_file.replace('.ipynb', '.html')
        out_path = os.path.join(OUTPUT_DIR, html_file)

        if not os.path.exists(nb_path):
            print(f"  ✗ NOT FOUND: {nb_path}")
            results[nb_file] = False
            continue

        success = execute_notebook(nb_path, out_path, timeout=900)
        results[nb_file] = success

    print("\n" + "=" * 70)
    print("EXECUTION SUMMARY")
    print("=" * 70)

    all_ok = True
    for nb_file, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"  {status}: {nb_file}")
        if not success:
            all_ok = False

    print(f"\nHTML files saved to: {OUTPUT_DIR}")
    if all_ok:
        print("\nAll 6 notebooks executed successfully!")
    else:
        print("\nSome notebooks had errors. Check output above.")

    sys.exit(0 if all_ok else 1)
