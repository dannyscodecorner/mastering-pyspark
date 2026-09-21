#!/usr/bin/env python3
"""Compare the native Incan helper with Python 3.14's textwrap.dedent."""

import itertools
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import textwrap


ROOT = Path(__file__).resolve().parents[1]


def incan_literal(value):
    # Incan 0.5.1 supports these text escapes; JSON's \u and \x escapes are
    # not interchangeable. Other Unicode scalars are literal fixture data.
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return '"' + escaped.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t") + '"'


def examples():
    yield from ("", "a", "\n", "\n\n", "  ", "\t", "  a\n    b", "    a\n        b")
    yield from ("  a\r\n  \r\n  b", "  a\rb\n  c", "\tfirst\n    second", "first\n  \n  last")

    prefixes = ["".join(chars) for size in range(5) for chars in itertools.product(" \t", repeat=size)]
    for left, right in itertools.product(prefixes, repeat=2):
        yield "\n" + left + "first\n \t\n" + right + "second\n"

    whitespace = [chr(codepoint) for codepoint in range(sys.maxunicode + 1) if chr(codepoint).isspace()]
    for char in whitespace:
        yield char
        yield "  first\n" + char + "\n  last"
        yield "  first\n \t" + char + "\t \n  last"
        yield char + "first\n  last"
        yield "  first" + char + "last\n  second"
    for char in ("\x00", "\x1b", "\u180e", "\u200b", "\u2060", "\ufeff", "\u0301"):
        yield "  first\n" + char + "\n  last"

    rng = random.Random(20260921)
    words = ("code()", "café", "日本語", "🐍", '"quoted"', "back\\slash", "{value}", "x\x00y")
    for _ in range(1500):
        lines = []
        for _ in range(rng.randrange(1, 12)):
            if rng.randrange(4) == 0:
                lines.append("".join(rng.choices(whitespace, k=rng.randrange(6))))
            else:
                lines.append(rng.choice(prefixes) + rng.choice(words) + rng.choice(("", " ", "\t", "\r")))
        yield "\n".join(lines)

    yield " " * 4096 + "first\n" + " " * 4096 + "  nested"
    yield "\t" * 4096 + "first\n" + "\t" * 4095 + " second"
    yield "    " + "café 日本語 🐍 " * 1024 + "\n    tail"
    yield "first\n" + "  indented\n" * 1024 + " \t\n"


def main():
    if sys.version_info[:2] != (3, 14):
        raise SystemExit("Run this comparison with Python 3.14; earlier dedent versions differ on blank lines.")
    cases = list(examples())
    source = [
        "from helper import dedent", "",
        "def check_cases(cases: list[tuple[str, str]], first_index: int) -> None:",
        "    mut index = first_index",
        "    for value, expected in cases:",
        "        actual = dedent(value)",
        '        assert actual == str(expected), f"Python parity failed at case {index}"',
        '        assert dedent(actual) == actual, f"Idempotence failed at case {index}"',
        "        index += 1",
    ]
    # Keep fixture construction in small functions: one giant literal makes
    # the native optimizer spend minutes on test data rather than the helper.
    starts = range(0, len(cases), 100)
    for start in starts:
        source.extend(["", f"def cases_{start}() -> None:", "    cases: list[tuple[str, str]] = ["])
        source.extend(f"        ({incan_literal(value)}, {incan_literal(textwrap.dedent(value))})," for value in cases[start:start + 100])
        source.extend(["    ]", f"    check_cases(cases, {start})"])
    source.extend(["", "def main() -> None:"])
    source.extend(f"    cases_{start}()" for start in starts)
    source.append(f'    print("{len(cases)} Python parity cases and idempotence checks passed.")')
    build = ROOT / ".build"
    build.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="dedent-parity-", dir=build) as temporary:
        probe = Path(temporary)
        shutil.copy2(ROOT / "slides/src/helper.incn", probe / "helper.incn")
        (probe / "main.incn").write_text("\n".join(source) + "\n", encoding="utf-8")
        env = {**os.environ, "INCAN_HOME": str(probe / ".incan-home"), "CARGO_TARGET_DIR": str(probe / ".cargo")}
        compiler = os.environ.get("INCAN_BINARY", "incan")
        result = subprocess.run([compiler, "build", "main.incn", "native"], cwd=probe, env=env, capture_output=True, text=True)
        if result.returncode:
            raise SystemExit(result.stdout + result.stderr)
        executable = "main.exe" if os.name == "nt" else "main"
        subprocess.run([str(probe / "native/oven/release" / executable)], cwd=probe, env=env, check=True)
    print(f"Reference: Python {sys.version.split()[0]} textwrap.dedent.")


if __name__ == "__main__":
    main()
