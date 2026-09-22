#!/usr/bin/env python3
"""Publish the verified course build to this repository's gh-pages branch."""

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

# Support both the documented script command and imports through the tools package.
if __package__:
    from . import course
else:
    import course

REPOSITORY = "dannyscodecorner/mastering-pyspark"
SITE_URL = "https://dannyscodecorner.github.io/mastering-pyspark/"
BRANCH = "gh-pages"


def git(*args: str, cwd: Path = course.ROOT) -> str:
    """Run Git in the chosen checkout and return its stripped standard output."""
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def publication_source() -> tuple[str, str, dict[str, str]]:
    """Require committed build inputs, the intended origin and an existing author identity."""
    dirty = git("status", "--porcelain", "--untracked-files=all", "--", "slides", "labs", "tools")
    if dirty:
        raise ValueError("Commit the slide, lab and tool changes before publishing.\n" + dirty)
    source_commit = git("rev-parse", "HEAD")
    remote = git("remote", "get-url", "origin")
    allowed = {
        f"https://github.com/{REPOSITORY}.git",
        f"https://github.com/{REPOSITORY}",
        f"git@github.com:{REPOSITORY}.git",
    }
    if remote not in allowed:
        raise ValueError(f"Expected origin to point to {REPOSITORY}; got {remote}.")
    identity = {key: git("config", "--get", f"user.{key}") for key in ("name", "email")}
    return source_commit, remote, identity


def prepare_checkout(checkout: Path, remote: str, identity: dict[str, str]) -> None:
    """Seed a disposable publication checkout while retaining any existing branch history."""
    git("init", "--quiet", "--initial-branch", BRANCH, cwd=checkout)
    git("remote", "add", "origin", remote, cwd=checkout)
    for key, value in identity.items():
        git("config", f"user.{key}", value, cwd=checkout)
    if not git("ls-remote", "--heads", "origin", f"refs/heads/{BRANCH}", cwd=checkout):
        return
    git("fetch", "--quiet", "origin", f"refs/heads/{BRANCH}", cwd=checkout)
    # Only this newly created checkout is reset, never the author's working tree.
    git("reset", "--quiet", "--mixed", "FETCH_HEAD", cwd=checkout)


def stage_site(checkout: Path, expected: dict[str, str]) -> bool:
    """Copy and stage the verified site, rejecting changed bytes or unexpected staged paths."""
    shutil.copytree(course.DIST, checkout, dirs_exist_ok=True)
    if course.tree_hashes(checkout) != expected:
        raise ValueError("The site changed while preparing publication; rebuild and retry.")
    git("add", "--all", "--force", ".", cwd=checkout)
    staged = set(git("ls-files", "-z", cwd=checkout).split("\0")) - {""}
    if staged != set(expected):
        raise ValueError("The publication file list differs from the verified site.")
    return bool(git("diff", "--cached", "--name-only", cwd=checkout))


def publish(dry_run: bool = False) -> None:
    """Prepare a verified publication and push normally unless this is a dry run."""
    course.verify(None)
    source_commit, remote, identity = publication_source()
    expected = course.tree_hashes(course.DIST)
    if ".nojekyll" not in expected:
        raise ValueError("The site needs .nojekyll; rebuild before publishing.")
    with tempfile.TemporaryDirectory(prefix="pages-", dir=course.BUILD) as temporary:
        checkout = Path(temporary)
        prepare_checkout(checkout, remote, identity)
        if not stage_site(checkout, expected):
            print(f"The gh-pages branch already contains this build: {SITE_URL}")
            return
        git("commit", "--quiet", "-m", f"Publish course from {source_commit}", cwd=checkout)
        print(f"Prepared {len(expected)} website files from source {source_commit[:12]}.")
        if dry_run:
            print("Dry run complete. No remote changes were made.")
            return
        # A concurrent publication must fail as non-fast-forward, never be overwritten.
        git("push", "origin", f"HEAD:refs/heads/{BRANCH}", cwd=checkout)
    print(f"Published gh-pages. GitHub Pages will deploy it to {SITE_URL}")


def main() -> None:
    """Parse publication options and preserve the explicit dry-run behaviour."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true", help="Prepare publication without pushing it."
    )
    args = parser.parse_args()
    publish(args.dry_run)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error))
