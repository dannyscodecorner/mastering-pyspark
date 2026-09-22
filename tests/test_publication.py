"""Check publication guards without making Git calls or changing a remote."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import publish_pages


class PublicationTests(unittest.TestCase):
    """Preserve source checks, dry-run behaviour and normal non-forced publication."""

    def test_dirty_sources_fail_before_remote_operations(self) -> None:
        """An uncommitted build input must stop publication before any remote is consulted."""
        with patch.object(publish_pages, "git", return_value=" M tools/course.py") as git:
            with self.assertRaisesRegex(ValueError, "Commit the slide, lab and tool changes"):
                publish_pages.publication_source()
            git.assert_called_once_with(
                "status", "--porcelain", "--untracked-files=all", "--", "slides", "labs", "tools"
            )

    def test_unexpected_origin_is_rejected(self) -> None:
        """Do not prepare a publication when origin identifies a different repository."""
        with patch.object(
            publish_pages, "git", side_effect=["", "abc123", "https://example.com/wrong"]
        ):
            with self.assertRaisesRegex(ValueError, "Expected origin"):
                publish_pages.publication_source()

    def test_changed_site_fails_before_staging(self) -> None:
        """The prepared checkout must still contain the verified bytes before Git stages it."""
        with (
            patch.object(publish_pages.shutil, "copytree"),
            patch.object(
                publish_pages.course, "tree_hashes", return_value={"index.html": "changed"}
            ),
            patch.object(publish_pages, "git") as git,
        ):
            with self.assertRaisesRegex(ValueError, "site changed"):
                publish_pages.stage_site(Path("/unused-checkout"), {"index.html": "original"})
            git.assert_not_called()

    def test_staged_file_mismatch_is_rejected(self) -> None:
        """Reject a Git index containing anything beyond the verified site file list."""
        expected = {"index.html": "original"}
        with (
            patch.object(publish_pages.shutil, "copytree"),
            patch.object(publish_pages.course, "tree_hashes", return_value=expected),
            patch.object(publish_pages, "git", side_effect=["", "index.html\0unexpected.txt\0"]),
        ):
            with self.assertRaisesRegex(ValueError, "file list differs"):
                publish_pages.stage_site(Path("/unused-checkout"), expected)

    def run_publication(self, *, dry_run: bool, changed: bool) -> list[tuple[str, ...]]:
        """Exercise publication orchestration with all filesystem and Git effects isolated."""
        with tempfile.TemporaryDirectory() as temporary, contextlib.ExitStack() as stack:
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            stack.enter_context(patch.object(publish_pages.course, "BUILD", Path(temporary)))
            stack.enter_context(patch.object(publish_pages.course, "verify"))
            stack.enter_context(
                patch.object(
                    publish_pages.course, "tree_hashes", return_value={".nojekyll": "hash"}
                )
            )
            stack.enter_context(
                patch.object(
                    publish_pages, "publication_source", return_value=("abc123", "origin", {})
                )
            )
            stack.enter_context(patch.object(publish_pages, "prepare_checkout"))
            stack.enter_context(patch.object(publish_pages, "stage_site", return_value=changed))
            git = stack.enter_context(patch.object(publish_pages, "git"))
            publish_pages.publish(dry_run=dry_run)
            return [call.args for call in git.call_args_list]

    def test_dry_run_never_pushes(self) -> None:
        """A dry run may prepare a local commit but must not send it to a remote."""
        calls = self.run_publication(dry_run=True, changed=True)
        self.assertEqual([args[0] for args in calls], ["commit"])

    def test_unchanged_site_never_commits_or_pushes(self) -> None:
        """An already published tree should be a no-op even without dry-run mode."""
        self.assertEqual(self.run_publication(dry_run=False, changed=False), [])

    def test_publish_keeps_normal_non_forced_push(self) -> None:
        """Concurrent publications remain protected by Git's non-fast-forward rejection."""
        calls = self.run_publication(dry_run=False, changed=True)
        self.assertEqual([args[0] for args in calls], ["commit", "push"])
        self.assertEqual(calls[-1], ("push", "origin", "HEAD:refs/heads/gh-pages"))


if __name__ == "__main__":
    unittest.main()
