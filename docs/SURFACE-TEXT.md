# Multiline text in the presentation surface

Import `dedent` from `surface` when a string should follow the indentation of the surrounding Incan code without carrying that margin into the rendered slide:

```incan
from surface import Surface, code_block, dedent

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

The helper is written entirely in Incan, with no renderer dependencies or additional packages. It lives in `slides/src/surface.incn` for now and can move into Incan's standard library later. It follows Python-style dedenting for ordinary space/tab-indented blocks; it is not a claim of complete Python Unicode-whitespace compatibility.

Run its focused native tests from the repository root, with the build directories kept local to this checkout:

```sh
INCAN_HOME="$PWD/.build/incan-home" CARGO_TARGET_DIR="$PWD/.build/cargo" incan test slides/src/test_surface.incn --fail-on-empty
```

Then run `python3 tools/course.py build` and `python3 tools/course.py verify`. The first migrated example is `slide_pyspark_code` in `chapter_01.incn`; its rendered code is unchanged.
