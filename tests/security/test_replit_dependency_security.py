"""Ensure Replit scanner remediation never installs unnecessary packages."""
from __future__ import annotations

from pathlib import Path
import importlib.util
import subprocess

SCRIPT = Path(__file__).resolve().parents[2] / 'scripts' / 'replit_dependency_security.py'
spec = importlib.util.spec_from_file_location('replit_dependency_security', SCRIPT)
security = importlib.util.module_from_spec(spec)
spec.loader.exec_module(security)


def test_release_numbers_do_not_accept_prereleases():
    assert security.release_numbers('2026.10.23') > security.release_numbers('2026.7.22')
    assert security.release_numbers('2.16.0') > security.release_numbers('2.9.1')
    try:
        security.release_numbers('2.16.0rc1')
    except ValueError:
        pass
    else:
        raise AssertionError('prereleases must not be accepted as safe')


def test_clean_environment_does_not_install_unneeded_optional_packages(monkeypatch):
    versions = {'certifi': '2026.10.23'}
    monkeypatch.setattr(security, 'installed_version', lambda pkg: versions.get(pkg))
    calls = []
    monkeypatch.setattr(security.subprocess, 'check_call', lambda command: calls.append(command))
    assert security.run('upgrade') == 0
    assert calls == []


def test_outdated_reported_packages_receive_only_required_updates(monkeypatch):
    versions = {
        'certifi': '2026.7.22',
        'httpx2': '2.9.1',
        'httpcore2': '2.9.1',
        'Pygments': '2.9.0',
    }
    monkeypatch.setattr(security, 'installed_version', lambda pkg: versions.get(pkg))
    calls = []

    def fake_install(command):
        calls.append(command)
        for package in versions:
            versions[package] = security.MINIMUM_SAFE[package]

    monkeypatch.setattr(security.subprocess, 'check_call', fake_install)
    assert security.run('upgrade') == 0
    assert len(calls) == 1
    assert set(calls[0][5:]) == {f'{pkg}>={minimum}' for pkg, minimum in security.MINIMUM_SAFE.items()}


def test_check_mode_reports_old_packages_without_installs(monkeypatch):
    monkeypatch.setattr(security, 'installed_version', lambda pkg: '2026.7.22' if pkg == 'certifi' else None)
    monkeypatch.setattr(security.subprocess, 'check_call', lambda command: (_ for _ in ()).throw(AssertionError('unexpected install')))
    assert security.run('check') == 1


def test_requirements_and_replit_build_are_wired_correctly():
    root = SCRIPT.parents[1]
    req = (root / 'requirements.txt').read_text()
    assert 'certifi>=2026.10.23' in req
    assert '\nhttpx2' not in req
    assert '\nhttpcore2' not in req
    assert '\nPygments' not in req
    replit = (root / '.replit').read_text()
    assert 'scripts/build_replit.sh' in replit
    build = (root / 'scripts/build_replit.sh').read_text()
    assert 'python -m pip install -r requirements.txt' in build
    assert 'python scripts/replit_dependency_security.py --upgrade' in build
    assert 'bash scripts/build_frontend.sh' in build
