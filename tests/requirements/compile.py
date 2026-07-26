#!/usr/bin/env python
"""Compile the pinned test requirements in this directory from requirements.in.

Run it through tox, which provides both pip-tools and the interpreters:

  * whole matrix, one tox env per Python version::

        tox run -m compile

  * a single Python version::

        tox run -e compile-py313

  * extra arguments after ``--`` are passed on to pip-compile, e.g. to see what
    would be resolved without writing the files::

        tox run -m compile -- --dry-run

pip-tools resolves against the interpreter it runs on, so the matrix cannot be
compiled from a single environment: each ``compile-pyXYZ`` env in ``tox.ini``
runs this script with its own interpreter, and the script compiles only the
:data:`COMPILE_SETTINGS` rows belonging to that Python version. Running the
script directly works the same way, for the Python you invoke it with::

    python tests/requirements/compile.py

Every Python version in :data:`COMPILE_SETTINGS` therefore needs a matching
``compile-pyXYZ`` env in the ``compile`` label in ``tox.ini``; tox skips the
versions whose interpreter is not installed. After editing ``requirements.in``,
recompile and commit the regenerated ``*.txt`` files.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

COMPILE_SETTINGS = {
    "py311-dj52-cms50": [],
    "py312-dj52-cms50": [],
    "py313-dj52-cms50": [],
    "py314-dj52-cms50": [],
    "py312-dj60-cms50": [],
    "py313-dj60-cms50": [],
    "py314-dj60-cms50": [],
    "py313-djmain-cmsdev": [],
    "py313-djmain-cms50": [],
    "py314-djmain-cmsdev": [],
    "py314-djmain-cms50": [],
}

django_dict = {
    "djmain": "https://github.com/django/django/tarball/main#egg=Django",
    "dj42": "Django>=4.2,<5",
    "dj50": "Django>=5.0,<5.1",
    "dj51": "Django>=5.1,<5.2",
    "dj52": "Django>=5.2,<5.3",
    "dj60": "Django>=6.0a1,<6.1",
}

cms_dict = {
    "cms50": "django-cms>=5.0,<5.1",
    "cmsdev": "https://github.com/django-cms/django-cms/tarball/main#egg=django-cms",
}


def get_args(key, value, common_args):
    py_ver, dj_ver, cms_ver, mode = key.split("-")
    assert py_ver[:2] == "py"
    assert mode.endswith(".txt")
    return [
        # The interpreter running this script -- pip-tools compiles for it.
        sys.executable,
        *common_args,
        "-P",
        django_dict[dj_ver],
        "-P",
        cms_dict[cms_ver],
        *value,
        "-o",
        key,
    ]


def run(args):
    """Run pip-compile, reporting its output only when it fails."""
    print(" ".join(args))
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        print(f"Failed {' '.join(args)}", file=sys.stderr)
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
    return result.returncode


if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    os.environ["CUSTOM_COMPILE_COMMAND"] = "tox run -m compile"
    os.environ.pop("PIP_REQUIRE_VIRTUALENV", None)
    common_args = [
        "-m",
        "piptools",
        "compile",
        "-U",
        # temporarily remove "--generate-hashes", until all dependencies are actual releases
        "--allow-unsafe",
    ] + sys.argv[1:]

    current = f"py3{sys.version_info[1]}"
    keys = [key for key in COMPILE_SETTINGS if key.split("-")[0] == current]
    if not keys:
        supported = ", ".join(sorted({key.split("-")[0] for key in COMPILE_SETTINGS}))
        sys.exit(f"Nothing to compile for {current}. Supported: {supported}")

    print(f"Creating requirement files for {current}")
    failures = 0
    for key in keys:
        value = COMPILE_SETTINGS[key]
        for mode in ("default", "versioning"):
            failures += run(get_args(f"{key}-{mode}.txt", value, common_args))
    sys.exit(1 if failures else 0)
