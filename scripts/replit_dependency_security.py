#!/usr/bin/env python3
"""Check or remediate the exact packages flagged by Replit on 2026-10-24.

No HTTPX2/Pygments dependencies are added to SkillShift. Replit may install
these outside our app requirements, so only touch them *if already present*.

Use --check to return a non-zero status for detected outdated packages.
Use --upgrade to upgrade outdated installed packages and verify the result.

This is a package-version hygiene check, not a replacement for pip-audit and
not proof that the entire Replit system image has no vulnerabilities.
"""
from __future__ import annotations

import argparse
from importlib import metadata
import subprocess
import sys

# certifi 2026.10.19 removes compromised emSign roots; the later 2026.10.23
# release is the current patched version as of 2026-10-24.
# HTTPX2 and HTTPCORE2 are distinct from SkillShift's actual 'httpx' client.
MINIMUM_SAFE = {
    'certifi': '2026.10.23',
    'httpx2': '2.16.0',
    'httpcore2': '2.16.0',
    'Pygments': '2.20.0',
}
OPTIONAL = frozenset({'httpx2', 'httpcore2', 'Pygments'})


def installed_version(package: str) -> str | None:
    try:
        return metadata.version(package)
    except metadata.PackageNotFoundError:
        return None


def release_numbers(version: str) -> tuple[int, ...]:
    """Compare releases without pulling in a new third-party dependency.

    Fail closed on unexpected/non-release formats rather than accidentally
    treating a prerelease as a safe stable release.
    """
    if not version or not all(piece.isascii() and piece.isdecimal() for piece in version.split('.')):
        raise ValueError(f'Unsupported package version: {version!r}')
    return tuple(int(piece) for piece in version.split('.'))


def outdated_installed() -> list[tuple[str, str | None, str]]:
    outdated = []
    for package, minimum in MINIMUM_SAFE.items():
        current = installed_version(package)
        if current is None:
            if package not in OPTIONAL:
                outdated.append((package, None, minimum))
            continue
        try:
            vulnerable = release_numbers(current) < release_numbers(minimum)
        except ValueError:
            # Nonstandard/prerelease versions deserve manual review.
            vulnerable = True
        if vulnerable:
            outdated.append((package, current, minimum))
    return outdated


def run(mode: str) -> int:
    outdated = outdated_installed()
    if mode == 'upgrade' and outdated:
        packages = [f'{package}>={minimum}' for package, _, minimum in outdated]
        print('Updating reported installed packages:', ', '.join(package for package, _, _ in outdated), flush=True)
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', *packages])
        outdated = outdated_installed()

    if outdated:
        for package, actual, minimum in outdated:
            print(f'OUTDATED {package}: {actual or "missing"} (requires >= {minimum})')
        return 1

    print('PASS: no outdated packages among the four reported Replit package families.')
    for package in MINIMUM_SAFE:
        print(f'  {package}: {installed_version(package) or "not installed (not needed by application)"}')
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--check', action='store_true', help='check without changing packages')
    action.add_argument('--upgrade', action='store_true', help='upgrade only installed outdated packages')
    args = parser.parse_args()
    return run('upgrade' if args.upgrade else 'check')


if __name__ == '__main__':
    raise SystemExit(main())
