#!/usr/bin/env python
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

COMPILE_SETTINGS = {
    "py39-dj42-cms41": [],
    "py310-dj42-cms41": [],
    "py311-dj42-cms41": [],
    "py312-dj42-cms41": [],
    "py310-dj50-cms41": [],
    "py311-dj50-cms41": [],
    "py312-dj50-cms41": [],
    "py39-dj51-cms41": [],
    "py310-dj51-cms41": [],
    "py311-dj51-cms41": [],
    "py311-dj52-cms41": [],
    "py312-dj52-cms41": [],
    "py313-dj52-cms41": [],
    "py311-dj52-cms50": [],
    "py312-dj52-cms50": [],
    "py313-dj52-cms50": [],
    "py313-djmain-cmsdev": [],
    "py313-djmain-cms41": [],
}

django_dict = {
    "djmain": "https://github.com/django/django/tarball/main#egg=Django",
    "dj32": "Django>=3.2,<4",
    "dj42": "Django>=4.2,<5",
    "dj50": "Django>=5.0,<5.1",
    "dj51": "Django>=5.1,<5.2",
    "dj52": "Django>=5.2,<5.3",
}

cms_dict = {
    "cms40": "https://github.com/django-cms/django-cms/tarball/release/4.0.1.x#egg=django-cms",
    "cms41": "django-cms>=4.1,<4.2",
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
