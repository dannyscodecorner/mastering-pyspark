# Multiline text in the presentation surface

Import `dedent` from `helper` when a string should follow the indentation of the surrounding Incan code without carrying that margin into the rendered slide:

```incan
from helper import dedent
from surface import Surface, code_block

def example() -> Surface:
    return code_block(dedent("""
        if ready:
            run()
        done()
    """).strip())
```

`dedent(value: str) -> str` removes the common space/tab prefix across all nonblank lines. It preserves relative indentation, Unicode content and trailing whitespace on content lines. Tabs are compared literally with tabs; they are not expanded or treated as spaces. Whitespace-only lines become empty lines and do not reduce the shared margin.

Leading and trailing newlines remain in the result. The example uses a separate `.strip()` to remove surrounding whitespace because the displayed snippet should start and end with code. Leave that call off when boundary whitespace matters. CRLF endings on content lines are preserved; whitespace-only lines are normalized to empty LF lines.

`code_block` itself preserves the exact string supplied to it. Existing literals and slides are unaffected unless they explicitly call `dedent`.

The helper is written entirely in Incan, with no production renderer dependencies or additional packages. It lives in `slides/src/helper.incn` for now and can move into Incan's standard library later. Its contract follows [Python 3.14's `textwrap.dedent`](https://docs.python.org/3.14/library/textwrap.html#textwrap.dedent) for Unicode scalar strings. Python strings containing lone surrogates are outside Incan's UTF-8 string model. Earlier Python versions differ in their handling of whitespace-only lines.

Only spaces and tabs count as removable indentation. Blank-line detection also recognizes Unicode whitespace and the four Python control separators U+001C–U+001F. Their literal characters are isolated in a named constant because the pinned Incan 0.5.1 compiler does not interpret hexadecimal escapes in text literals.

The implementation splits once, reuses that line list, and makes sequential character scans to find the shared margin. Prefix comparisons use a list rather than repeatedly indexing Unicode strings. Once the margin reaches zero, indentation comparisons stop; later blank lines are still normalized. The algorithm uses linear time and linear auxiliary space in the input size. This avoids the former repeated rescanning and extra line/result lists; it does not imply allocation-free execution on the current compiler.

The focused tests live alongside the helper in its `module tests:` block. They are omitted from normal builds. Run them from the repository root, with the build directories kept local to this checkout:

```sh
INCAN_HOME="$PWD/.build/incan-home" CARGO_TARGET_DIR="$PWD/.build/cargo" incan test slides/src/helper.incn --fail-on-empty
```

For a broader differential check, run `python3 tools/check_dedent.py` with Python 3.14. It compiles the actual Incan helper and compares its output with Python's implementation across mixed prefixes, every Python whitespace character, Unicode content, CRLF, long input and seeded random cases. Each result is also checked for idempotence. The comparison uses an isolated temporary native build beneath `.build/` and leaves the authored files untouched.

Then run `python3 tools/course.py build` and `python3 tools/course.py verify`. The first migrated example is `slide_pyspark_code` in `slides/src/chapters/chapter_01/pyspark_code.incn`; its rendered code is unchanged.
