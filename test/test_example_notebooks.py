import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import platform
from glob import glob
import os

python_version = platform.python_version()
if python_version[:2] == '2.':
    python_version = 'python2'
elif python_version[:2] == '3.':
    python_version = 'python3'

def test_example_notebooks():
    """ Tests that all the example ipython notebooks of format
    gw_eccentricity/examples/*.ipynb are working. Since we expect these to be
    used by our users, it would be emabarassing if our own examples failed.
    """
    notebooks_list = glob('examples/*.ipynb')
    notebooks_list.sort()

    for notebook in notebooks_list:

        print(f'testing {notebook}')
        with open(notebook) as f:
            nb = nbformat.read(f, as_version=4)

        ep = ExecutePreprocessor(timeout=None, kernel_name=python_version)
        ep.preprocess(nb, {'metadata': {'path': '.'}})
