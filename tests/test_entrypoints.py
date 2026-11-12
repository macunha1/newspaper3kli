"""Run the installed interfaces from outside the checkout."""

import os
import subprocess
import sys
import sysconfig
from importlib.metadata import distribution
from pathlib import Path

import pytest

import newspaper3kli
from newspaper3kli import cli


def installed_command():
    suffix = ".exe" if os.name == "nt" else ""
    return str(Path(sysconfig.get_path("scripts")) / ("newspaper3kli" + suffix))


def test_console_script_metadata():
    (entrypoint,) = [
        entry
        for entry in distribution("newspaper3kli").entry_points
        if entry.group == "console_scripts" and entry.name == "newspaper3kli"
    ]
    assert entrypoint.load() is cli.main


def test_original_main_entrypoint(monkeypatch):
    monkeypatch.setattr(cli, "main", lambda: 7)
    assert newspaper3kli.main() == 7


@pytest.mark.parametrize("interface", ["console", "module"])
@pytest.mark.parametrize("mode", ["help", "empty-input", "invalid-option"])
def test_installed_interface(tmp_path, interface, mode):
    command = [installed_command()] if interface == "console" else [sys.executable, "-m", "newspaper3kli"]
    if mode == "help":
        command.append("--help")
    elif mode == "empty-input":
        command.extend(["--output", str(tmp_path / "articles")])
    else:
        command.append("--not-an-option")
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)

    result = subprocess.run(
        command,
        cwd=tmp_path,
        env=environment,
        input="",
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == (2 if mode == "invalid-option" else 0), result.stderr
    if mode == "help":
        assert "usage: newspaper3kli" in result.stdout
        assert "--keep-html" in result.stdout
    elif mode == "empty-input":
        assert (tmp_path / "articles").is_dir()
    else:
        assert "unrecognized arguments" in result.stderr
