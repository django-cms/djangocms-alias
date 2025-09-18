#!/usr/bin/env python
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

COMPILE_SETTINGS = {
    "py311-dj52-cms50": [],
    "py312-dj52-cms50": [],
    "py313-dj52-cms50": [],
    "py312-dj60-cms50": [],
    "py313-dj60-cms50": [],
    "py313-djmain-cmsdev": [],
    "py313-djmain-cms50": [],
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
        f"python{py_ver[2]}.{py_ver[3:]}",
        *common_args,
        "-P",
        django_dict[dj_ver],
        "-P",
        cms_dict[cms_ver],
        *value,
        "-o",
        key,
    ]


def run(*args, **kwargs):
    try:
        print(" ".join(args[0]))
        subprocess.run(*args, **kwargs)
    except Exception as e:
        print(f"Failed {' '.join(args[0])}: {e}")


if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    os.environ["CUSTOM_COMPILE_COMMAND"] = "requirements/compile.py"
    os.environ.pop("PIP_REQUIRE_VIRTUALENV", None)
    common_args = [
        "-m",
        "piptools",
        "compile",
        # temporarily remove "--generate-hashes", until all dependencies are actual releases
        "--allow-unsafe",
    ] + sys.argv[1:]

    print("Upgrading pip-tools")
    for py_ver in {key.split("-")[0] for key in COMPILE_SETTINGS.keys()}:
        args = [
            f"python{py_ver[2]}.{py_ver[3:]}",
            "-m",
            "pip",
            "install",
            "--upgrade",
            "pip-tools",
        ]
        subprocess.run(args, capture_output=True, check=False)

    print("Creating requirement files")
    for key, value in COMPILE_SETTINGS.items():
        run(
            get_args(key + "-default.txt", value, common_args),
            check=True,
            capture_output=True,
        )
        run(
            get_args(key + "-versioning.txt", value, common_args),
            check=True,
            capture_output=True,
        )
