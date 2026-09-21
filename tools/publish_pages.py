#!/usr/bin/env python3
"""Publish the verified course build to this repository's gh-pages branch."""

import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

import course


REPOSITORY = "dannyscodecorner/mastering-pyspark"
SITE_URL = "https://dannyscodecorner.github.io/mastering-pyspark/"
BRANCH = "gh-pages"


def git(*args, cwd=course.ROOT):
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def publish(dry_run=False):
    course.verify(None)
    # Unrelated documentation edits need not block a release, but every build
    # input must be committed so the published site has a recoverable source.
    dirty = git("status", "--porcelain", "--untracked-files=all", "--", "slides", "labs", "tools")
    if dirty:
        raise ValueError("Commit the slide, lab and tool changes before publishing.\n" + dirty)
    source_commit = git("rev-parse", "HEAD")
    remote = git("remote", "get-url", "origin")
    allowed = {f"https://github.com/{REPOSITORY}.git", f"https://github.com/{REPOSITORY}", f"git@github.com:{REPOSITORY}.git"}
    if remote not in allowed:
        raise ValueError(f"Expected origin to point to {REPOSITORY}; got {remote}.")
    identity = {key: git("config", "--get", f"user.{key}") for key in ("name", "email")}
    expected = course.tree_hashes(course.DIST)
    if ".nojekyll" not in expected:
        raise ValueError("The site needs .nojekyll; rebuild before publishing.")

    # Use a disposable checkout; never switch branches or stage source files
    # in the author's working tree. Existing publication history is retained.
    with tempfile.TemporaryDirectory(prefix="pages-", dir=course.BUILD) as temporary:
        checkout = Path(temporary)
        git("init", "--quiet", "--initial-branch", BRANCH, cwd=checkout)
        git("remote", "add", "origin", remote, cwd=checkout)
        for key, value in identity.items():
            git("config", f"user.{key}", value, cwd=checkout)
        if git("ls-remote", "--heads", "origin", f"refs/heads/{BRANCH}", cwd=checkout):
            git("fetch", "--quiet", "origin", f"refs/heads/{BRANCH}", cwd=checkout)
            # This new checkout contains only .git. Seed its branch and index,
            # then replace the previous website with the verified build.
            git("reset", "--quiet", "--mixed", "FETCH_HEAD", cwd=checkout)
        shutil.copytree(course.DIST, checkout, dirs_exist_ok=True)
        if course.tree_hashes(checkout) != expected:
            raise ValueError("The site changed while preparing publication; rebuild and retry.")
        git("add", "--all", "--force", ".", cwd=checkout)
        staged = set(git("ls-files", "-z", cwd=checkout).split("\0")) - {""}
        if staged != set(expected):
            raise ValueError("The publication file list differs from the verified site.")
        changed = git("diff", "--cached", "--name-only", cwd=checkout)
        if not changed:
            print(f"The gh-pages branch already contains this build: {SITE_URL}")
            return
        git("commit", "--quiet", "-m", f"Publish course from {source_commit}", cwd=checkout)
        print(f"Prepared {len(expected)} website files from source {source_commit[:12]}.")
        if dry_run:
            print("Dry run complete. No remote changes were made.")
            return
        # A concurrent publisher causes a normal non-fast-forward rejection.
        # Never force-push over another publication.
        git("push", "origin", f"HEAD:refs/heads/{BRANCH}", cwd=checkout)
    print(f"Published gh-pages. GitHub Pages will deploy it to {SITE_URL}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Verify and prepare the publication without pushing it.")
    args = parser.parse_args()
    publish(args.dry_run)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error))
