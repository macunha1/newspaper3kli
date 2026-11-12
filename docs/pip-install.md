# Newspaper3kli installation with pip

Install Newspaper3kli with Python and pip in a virtual environment. Python 3.15.2
or newer is required for this checkout. Nix and uv are not required to install
or run the Python package.

## Prepare Python

Install a compatible Python from [python.org](https://www.python.org/downloads/)
or your operating system's package manager. Confirm the interpreter before
creating the environment:

```bash
python3.15 --version
python3.15 -m venv ~/.venvs/newspaper3kli
source ~/.venvs/newspaper3kli/bin/activate
python -m pip install --upgrade pip
```

These commands use Bash on Linux or macOS. On Windows, use PowerShell:

```powershell
py -3.15 --version
py -3.15 -m venv "$HOME\.venvs\newspaper3kli"
& "$HOME\.venvs\newspaper3kli\Scripts\Activate.ps1"
python -m pip install --upgrade pip
```

If your interpreter uses a different executable name, substitute that name after
confirming its version. Always use `python -m pip` after activation so pip installs
into the selected environment. Some Linux distributions provide `venv` in a
separate package matching the Python version.

## Install and run

To install the version available on PyPI:

```bash
python -m pip install newspaper3kli
newspaper3kli --help
```

PyPI releases may differ from this checkout. Install from source to use the CLI
and options documented in this repository:

```bash
git clone https://github.com/macunha1/newspaper3kli.git
cd newspaper3kli
python -m pip install .
newspaper3kli --help
```

pip installs the package and its required dependencies automatically. Installation
needs access to the package index. No NLTK models or image downloads are required.

With the environment activated, the command works from any directory:

```bash
newspaper3kli --output articles https://example.com/article
cat urls.txt | newspaper3kli --output articles --concurrency 8
```

`python -m newspaper3kli` exposes the same interface. See the [README](../README.md)
for options, output files, and exit codes. Use `deactivate` to leave the environment;
activate it again before the next run, or invoke its `bin/newspaper3kli` executable
directly (`Scripts\newspaper3kli.exe` on Windows).

## Upgrade or remove

```bash
python -m pip install --upgrade newspaper3kli
python -m pip uninstall newspaper3kli
```

For a source installation, update the checkout and run `python -m pip install .`
again. To preserve an environment's resolved versions for later recreation:

```bash
python -m pip freeze > requirements.txt
# In another compatible environment:
python -m pip install -r requirements.txt
```

A freeze can contain local source paths and platform-specific packages; review it
before sharing or moving it.

For an installation that includes its own Python runtime, see
[the Nix installation guide](nix-build.md).

References: Python's [virtual environments](https://docs.python.org/3/library/venv.html),
and pip's [installation options](https://pip.pypa.io/en/stable/cli/pip_install/).
