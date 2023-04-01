#!/usr/bin/env python
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def run(*args, **kwargs):
    try:
        print(" ".join(args[0]))
        subprocess.run(*args, **kwargs)
    except Exception as e:
        print(f'Failed {" ".join(args[0])}: {e}')


if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    os.environ["CUSTOM_COMPILE_COMMAND"] = "requirements/compile.py"
    os.environ.pop("PIP_REQUIRE_VIRTUALENV", None)
    common_args = [
        "-m",
        "piptools",
        "compile",
        # "--generate-hashes",  # Disabled since references to git branches change hash regularly.
        "--allow-unsafe",
    ] + sys.argv[1:]
    run(
        [
            "python3.8",
            *common_args,
            "-P",
            "Django>=3.2,<3.3",
            "-P",
            "django-treebeard==4.5.1",
            "-P",
            "django-classy-tags<4.0",
            "-o",
            "py38-dj32-cms40-default.txt",
        ],
        check=True,
        capture_output=True,
    )
    run(
        [
            "python3.8",
            *common_args,
            "-P",
            "Django>=3.2,<3.3",
            "-P",
            "django-treebeard==4.5.1",
            "-P",
            "django-classy-tags<4.0",
            "-o",
            "py38-dj32-cms40-versioning.txt",
        ],
        check=True,
        capture_output=True,
    )
    run(
        [
            "python3.8",
            *common_args,
            "-P",
            "Django>=3.2,<3.3",
            # "-P",
            # "django-cms==4.1rc1",
            "-o",
            "py38-dj32-cms41-default.txt",
        ],
        check=True,
        capture_output=True,
    )
    run(
        [
            "python3.8",
            *common_args,
            "-P",
            "Django>=3.2,<3.3",
            # "-P",
            # "django-cms==4.1rc1",
            "-o",
            "py38-dj32-cms41-versioning.txt",
        ],
        check=True,
        capture_output=True,
    )
    run(
        [
            "python3.9",
            *common_args,
            "-P",
            "Django>=3.2,<3.3",
            # "-P",
            # "django-cms==4.1rc1",
            "-o",
            "py39-dj32-cms41-default.txt",
        ],
        check=True,
        capture_output=True,
    )
    run(
        [
            "python3.9",
            *common_args,
            "-P",
            "Django>=3.2,<3.3",
            # "-P",
            # "django-cms==4.1rc1",
            "-o",
            "py39-dj32-cms41-versioning.txt",
        ],
        check=True,
        capture_output=True,
    )
    run(
        [
            "python3.9",
            *common_args,
            "-P",
            "Django>=4.0,<4.1",
            # "-P",
            # "django-cms==4.1rc1",
            "-o",
            "py39-dj40-cms41-default.txt",
        ],
        check=True,
        capture_output=True,
    )
    run(
        [
            "python3.9",
            *common_args,
            "-P",
            "Django>=4.0,<4.1",
            # "-P",
            # "django-cms==4.1rc1",
            "-o",
            "py39-dj40-cms41-versioning.txt",
        ],
        check=True,
        capture_output=True,
    )
    run(
        [
            "python3.10",
            *common_args,
            "-P",
            "Django>=3.2,<3.3",
            # "-P",
            # "django-cms==4.1rc1",
            "-o",
            "py310-dj32-cms41-default.txt",
        ],
        check=True,
        capture_output=True,
    )
    run(
        [
            "python3.10",
            *common_args,
            "-P",
            "Django>=3.2,<3.3",
            # "-P",
            # "django-cms==4.1rc1",
            "-o",
            "py310-dj32-cms41-versioning.txt",
        ],
        check=True,
        capture_output=True,
    )
    run(
        [
            "python3.10",
            *common_args,
            "-P",
            "Django>=4.0,<4.1",
            # "-P",
            # "django-cms==4.1rc1",
            "-o",
            "py310-dj40-cms41-default.txt",
        ],
        check=True,
        capture_output=True,
    )
    run(
        [
            "python3.10",
            *common_args,
            "-P",
            "Django>=4.0,<4.1",
            # "-P",
            # "django-cms==4.1rc1",
            "-o",
            "py310-dj40-cms41-versioning.txt",
        ],
        check=True,
        capture_output=True,
    )
    run(
        [
            "python3.11",
            *common_args,
            "-P",
            "Django>=4.1,<4.2",
            # "-P",
            # "django-cms==4.1rc1",
            "-o",
            "py311-dj41-cms41-default.txt",
        ],
        check=True,
        capture_output=True,
    )
    run(
        [
            "python3.11",
            *common_args,
            "-P",
            "Django>=4.1,<4.2",
            # "-P",
            # "django-cms==4.1rc1",
            "-o",
            "py311-dj41-cms41-versioning.txt",
        ],
        check=True,
        capture_output=True,
    )
