#!/usr/bin/env python3
"""Compare the native Incan helper with Python 3.14's textwrap.dedent."""

import itertools
import os
import random
import shutil
import subprocess
import sys
import tempfile
import textwrap
from collections.abc import Iterator, Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASE_BATCH_SIZE = 100
WORDS = ("code()", "café", "日本語", "🐍", '"quoted"', "back\\slash", "{value}", "x\x00y")


def incan_literal(value: str) -> str:
    """Encode an Incan 0.5.1 string without unsupported JSON Unicode or hex escapes."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return '"' + escaped.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t") + '"'


def whitespace_examples(whitespace: Sequence[str]) -> Iterator[str]:
    """Exercise Unicode whitespace both within lines and on otherwise blank lines."""
    for char in whitespace:
        yield char
        yield "  first\n" + char + "\n  last"
        yield "  first\n \t" + char + "\t \n  last"
        yield char + "first\n  last"
        yield "  first" + char + "last\n  second"
    for char in ("\x00", "\x1b", "\u180e", "\u200b", "\u2060", "\ufeff", "\u0301"):
        yield "  first\n" + char + "\n  last"


def random_line(rng: random.Random, prefixes: Sequence[str], whitespace: Sequence[str]) -> str:
    """Generate one deterministic blank or indented line from the supplied random state."""
    if rng.randrange(4) == 0:
        return "".join(rng.choices(whitespace, k=rng.randrange(6)))
    return rng.choice(prefixes) + rng.choice(WORDS) + rng.choice(("", " ", "\t", "\r"))


def random_examples(prefixes: Sequence[str], whitespace: Sequence[str]) -> Iterator[str]:
    """Generate a repeatable sample containing mixed indentation, Unicode and line endings."""
    rng = random.Random(20260921)
    for _ in range(1500):
        lines = [random_line(rng, prefixes, whitespace) for _ in range(rng.randrange(1, 12))]
        yield "\n".join(lines)


def examples() -> Iterator[str]:
    """Yield fixed, exhaustive-prefix, random and long-input parity cases in stable order."""
    yield from ("", "a", "\n", "\n\n", "  ", "\t", "  a\n    b", "    a\n        b")
    yield from ("  a\r\n  \r\n  b", "  a\rb\n  c", "\tfirst\n    second", "first\n  \n  last")
    prefixes = [
        "".join(chars) for size in range(5) for chars in itertools.product(" \t", repeat=size)
    ]
    for left, right in itertools.product(prefixes, repeat=2):
        yield "\n" + left + "first\n \t\n" + right + "second\n"
    whitespace = [
        chr(codepoint) for codepoint in range(sys.maxunicode + 1) if chr(codepoint).isspace()
    ]
    yield from whitespace_examples(whitespace)
    yield from random_examples(prefixes, whitespace)
    yield " " * 4096 + "first\n" + " " * 4096 + "  nested"
    yield "\t" * 4096 + "first\n" + "\t" * 4095 + " second"
    yield "    " + "café 日本語 🐍 " * 1024 + "\n    tail"
    yield "first\n" + "  indented\n" * 1024 + " \t\n"


def probe_source(cases: Sequence[str]) -> str:
    """Generate native parity assertions in small batches to bound optimiser work."""
    source = [
        "from helper import dedent",
        "",
        "def check_cases(cases: list[tuple[str, str]], first_index: int) -> None:",
        "    mut index = first_index",
        "    for value, expected in cases:",
        "        actual = dedent(value)",
        '        assert actual == str(expected), f"Python parity failed at case {index}"',
        '        assert dedent(actual) == actual, f"Idempotence failed at case {index}"',
        "        index += 1",
    ]
    starts = range(0, len(cases), CASE_BATCH_SIZE)
    for start in starts:
        source.extend(["", f"def cases_{start}() -> None:", "    cases: list[tuple[str, str]] = ["])
        source.extend(
            f"        ({incan_literal(value)}, {incan_literal(textwrap.dedent(value))}),"
            for value in cases[start : start + CASE_BATCH_SIZE]
        )
        source.extend(["    ]", f"    check_cases(cases, {start})"])
    source.extend(["", "def main() -> None:"])
    source.extend(f"    cases_{start}()" for start in starts)
    source.append(f'    print("{len(cases)} Python parity cases and idempotence checks passed.")')
    return "\n".join(source) + "\n"


def run_probe(source: str) -> None:
    """Build and execute the parity probe in an isolated, disposable compiler directory."""
    build = ROOT / ".build"
    build.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="dedent-parity-", dir=build) as temporary:
        probe = Path(temporary)
        shutil.copy2(ROOT / "slides/src/helper.incn", probe / "helper.incn")
        (probe / "main.incn").write_text(source, encoding="utf-8")
        env = {
            **os.environ,
            "INCAN_HOME": str(probe / ".incan-home"),
            "CARGO_TARGET_DIR": str(probe / ".cargo"),
        }
        compiler = os.environ.get("INCAN_BINARY", "incan")
        result = subprocess.run(
            [compiler, "build", "main.incn", "native"],
            cwd=probe,
            env=env,
            capture_output=True,
            text=True,
        )
        if result.returncode:
            raise SystemExit(result.stdout + result.stderr)
        executable = "main.exe" if os.name == "nt" else "main"
        subprocess.run(
            [str(probe / "native/oven/release" / executable)], cwd=probe, env=env, check=True
        )


def main() -> None:
    """Require Python 3.14 and compare the native helper with its dedent implementation."""
    if sys.version_info[:2] != (3, 14):
        raise SystemExit(
            "Run this comparison with Python 3.14; earlier dedent versions differ on blank lines."
        )
    run_probe(probe_source(list(examples())))
    print(f"Reference: Python {sys.version.split()[0]} textwrap.dedent.")


if __name__ == "__main__":
    main()
