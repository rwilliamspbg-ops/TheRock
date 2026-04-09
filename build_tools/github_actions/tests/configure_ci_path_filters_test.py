# Copyright Advanced Micro Devices, Inc.
# SPDX-License-Identifier: MIT

from pathlib import Path
import os
import sys
import subprocess
import unittest
from typing import Any
from unittest.mock import patch

sys.path.insert(0, os.fspath(Path(__file__).parent.parent))

from configure_ci_path_filters import get_git_modified_paths, is_ci_run_required


class ConfigureCIPathFiltersTest(unittest.TestCase):
    @patch("configure_ci_path_filters.subprocess.run")
    def test_get_git_modified_paths_returns_split_output(self, mock_run: Any):
        mock_run.return_value = subprocess.CompletedProcess(
            args=["git", "diff", "--name-only", "HEAD^1"],
            returncode=0,
            stdout="a.txt\nb/c.py\n",
        )

        paths = get_git_modified_paths("HEAD^1")
        self.assertEqual(paths, ["a.txt", "b/c.py"])

    @patch("configure_ci_path_filters.subprocess.run")
    def test_get_git_modified_paths_returns_none_on_bad_ref(self, mock_run: Any):
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=128,
            cmd=["git", "diff", "--name-only", "deadbeef"],
        )

        self.assertIsNone(get_git_modified_paths("deadbeef"))

    @patch("configure_ci_path_filters.subprocess.run")
    def test_get_git_modified_paths_returns_none_on_timeout(self, mock_run: Any):
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=["git", "diff", "--name-only", "HEAD^1"],
            timeout=60,
        )

        self.assertIsNone(get_git_modified_paths("HEAD^1"))

    def test_run_ci_if_source_file_edited(self):
        paths = ["source_file.h"]
        run_ci = is_ci_run_required(paths)
        self.assertTrue(run_ci)

    def test_dont_run_ci_if_only_markdown_files_edited(self):
        paths = ["README.md", "build_tools/README.md"]
        run_ci = is_ci_run_required(paths)
        self.assertFalse(run_ci)

    def test_dont_run_ci_if_only_experimental_files_edited(self):
        paths = ["experimental/file.h"]
        run_ci = is_ci_run_required(paths)
        self.assertFalse(run_ci)

    def test_run_ci_if_related_workflow_file_edited(self):
        paths = [".github/workflows/ci.yml"]
        run_ci = is_ci_run_required(paths)
        self.assertTrue(run_ci)

        paths = [".github/workflows/build_portable_linux_artifacts.yml"]
        run_ci = is_ci_run_required(paths)
        self.assertTrue(run_ci)

        paths = [".github/workflows/build_artifact.yml"]
        run_ci = is_ci_run_required(paths)
        self.assertTrue(run_ci)

    def test_dont_run_ci_if_unrelated_workflow_file_edited(self):
        paths = [".github/workflows/pre-commit.yml"]
        run_ci = is_ci_run_required(paths)
        self.assertFalse(run_ci)

        paths = [".github/workflows/test_jax_dockerfile.yml"]
        run_ci = is_ci_run_required(paths)
        self.assertFalse(run_ci)

    def test_run_ci_if_source_file_and_unrelated_workflow_file_edited(self):
        paths = ["source_file.h", ".github/workflows/pre-commit.yml"]
        run_ci = is_ci_run_required(paths)
        self.assertTrue(run_ci)


if __name__ == "__main__":
    unittest.main()
