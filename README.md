# Live Logs Handler

Thread-Safe Structured Logging SDK for Jupyter Notebooks. Captures all output from notebook cells (print statements, logging calls, errors) and writes them to structured log files in JSON or logfmt format.

## Installation

```
pip install --upgrade setuptools wheel

python3 setup.py sdist bdist_wheel

pip install dist/singlestore_pulse-0.1-py3-none-any.whl

```

### Install from GitHub

You can install this package directly from GitHub using pip:

```bash
pip install git+https://github.com/dgalas2/live-logs-handler.git
```

### Install a specific branch or tag

```bash
# Install from a specific branch
pip install git+https://github.com/dgalas2/live-logs-handler.git@branch-name

# Install from a specific tag/release
pip install git+https://github.com/dgalas2/live-logs-handler.git@v0.1.0
