"""Install the distribution wheel and exercise it without the source checkout."""

import os
import shutil
import subprocess
import sys
import tarfile
import tomllib
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    destination = Path(sys.argv[1]).resolve()
    metadata = tomllib.loads((root / "pyproject.toml").read_text())["project"]
    name, version = metadata["name"], metadata["version"]
    wheel = root / "dist" / f"{name}-{version}-py3-none-any.whl"
    sdist = root / "dist" / f"{name}-{version}.tar.gz"
    artifacts = set((root / "dist").iterdir())
    if artifacts != {wheel, sdist}:
        raise RuntimeError(f"Expected exactly {wheel.name} and {sdist.name}, found {artifacts}")
    with tarfile.open(sdist) as archive:
        for required in ("pyproject.toml", "uv.lock", "UNLICENSE", "src/newspaper3kli/cli.py"):
            archive.getmember(f"{name}-{version}/{required}")

    environment = os.environ.copy()
    for variable in ("PYTHONPATH", "PYTHONHOME", "NIX_PYTHONPATH", "VIRTUAL_ENV"):
        environment.pop(variable, None)
    python = destination / "venv" / "bin" / "python"
    subprocess.run(
        ["uv", "pip", "install", "--python", str(python), "--no-deps", str(wheel)],
        check=True,
        env=environment,
        cwd=destination,
    )
    subprocess.run(
        [
            str(python),
            "-I",
            "-c",
            "import sys, newspaper3kli; from pathlib import Path; "
            "from importlib.metadata import version; "
            "assert Path(newspaper3kli.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()); "
            f"assert version('newspaper3kli') == {version!r}",
        ],
        check=True,
        env=environment,
        cwd=destination,
    )
    shutil.copytree(root / "tests", destination / "tests", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy2(root / "pyproject.toml", destination / "pyproject.toml")
    subprocess.run(
        [str(python), "-I", "-m", "pytest"],
        check=True,
        env=environment,
        cwd=destination,
    )


if __name__ == "__main__":
    main()
