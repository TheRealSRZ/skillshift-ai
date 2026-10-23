"""Isolate file-backed abuse counters between tests and repeated test runs."""
import pytest


@pytest.fixture(autouse=True)
def isolated_public_rate_db(monkeypatch, tmp_path):
    monkeypatch.setenv('API_RATE_DB_PATH', str(tmp_path / 'rate_limit.sqlite3'))
    monkeypatch.setenv('API_RATE_PER_MINUTE', '120')
    monkeypatch.setenv('API_MAX_BODY_BYTES', '32768')
