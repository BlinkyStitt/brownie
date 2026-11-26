"""Package metadata must honor the selected dependency contract."""

import runpy
from pathlib import Path

import pytest
import setuptools


@pytest.mark.parametrize("platform", ["linux", "win32"])
@pytest.mark.parametrize("library_mode", [False, True])
def test_requirement_selection(monkeypatch, platform, library_mode):
    root = Path(__file__).resolve().parents[2]
    monkeypatch.chdir(root)
    monkeypatch.setattr("sys.platform", platform)
    monkeypatch.setenv("BROWNIE_LIB", "1" if library_mode else "0")
    metadata = {}
    monkeypatch.setattr(setuptools, "setup", lambda **kwargs: metadata.update(kwargs))
    runpy.run_path(str(root / "setup.py"), run_name="brownie_setup_test")
    requirements = metadata["install_requires"]
    # The Windows library input includes the shared lock, plus colorama.
    if library_mode and platform != "win32":
        assert "hypothesis<7" in requirements
        assert "hypothesis==6.15.0" not in requirements
    else:
        assert "hypothesis==6.15.0" in requirements
        assert "hypothesis<7" not in requirements
    assert all(not r.startswith(("-r", "-e", "#")) for r in requirements)
    if platform == "win32":
        assert any(r.startswith("colorama") for r in requirements)
