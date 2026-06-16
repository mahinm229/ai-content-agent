"""Unit tests for the prepare_for_vocal function."""

import json
import os
from unittest.mock import patch, MagicMock

import pytest

from agent import prepare_for_vocal


class TestPrepareForVocal:
    """Tests for Vocal Media content preparation."""

    @patch("agent.generate_article")
    def test_calls_generate_article_with_vocal_platform(self, mock_gen):
        mock_gen.return_value = {"title": "Vocal Article", "content": "Body text"}

        prepare_for_vocal("AI Niche")

        mock_gen.assert_called_once_with("AI Niche", "Vocal Media")

    @patch("agent.generate_article")
    def test_creates_json_file_with_article(self, mock_gen, tmp_path):
        mock_gen.return_value = {"title": "Vocal Article", "content": "Full body"}

        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            prepare_for_vocal("AI Niche")

            expected_file = tmp_path / "vocal_AI_Niche.json"
            assert expected_file.exists()

            with open(expected_file) as f:
                data = json.load(f)
            assert data["title"] == "Vocal Article"
            assert data["content"] == "Full body"
        finally:
            os.chdir(original_cwd)

    @patch("agent.generate_article")
    def test_truncates_long_niche_names_in_filename(self, mock_gen, tmp_path):
        mock_gen.return_value = {"title": "T", "content": "C"}

        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            long_niche = "This Is A Very Long Niche Name That Exceeds Twenty Characters"
            prepare_for_vocal(long_niche)

            files = list(tmp_path.glob("vocal_*.json"))
            assert len(files) == 1
            filename = files[0].name
            # filename should be truncated (niche[:20] after replace)
            assert len(filename) < len(f"vocal_{long_niche.replace(' ', '_')}.json")
        finally:
            os.chdir(original_cwd)

    @patch("agent.generate_article")
    def test_replaces_spaces_with_underscores_in_filename(self, mock_gen, tmp_path):
        mock_gen.return_value = {"title": "T", "content": "C"}

        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            prepare_for_vocal("AI Health")

            expected_file = tmp_path / "vocal_AI_Health.json"
            assert expected_file.exists()
        finally:
            os.chdir(original_cwd)

    @patch("agent.generate_article")
    def test_returns_article_dict(self, mock_gen):
        expected = {"title": "My Article", "content": "Content here"}
        mock_gen.return_value = expected

        # Use tmp directory to avoid polluting repo
        original_cwd = os.getcwd()
        os.chdir("/tmp")
        try:
            result = prepare_for_vocal("Some Niche")
            assert result == expected
        finally:
            os.chdir(original_cwd)
