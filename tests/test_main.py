"""Unit tests for the main workflow orchestration."""

from datetime import datetime
from unittest.mock import patch, AsyncMock

import pytest

from agent import main, NICHES


class TestMainWorkflow:
    """Tests for the main orchestration function."""

    @patch("agent.prepare_for_vocal")
    @patch("agent.publish_to_listverse", new_callable=AsyncMock)
    @patch("agent.publish_to_substack", new_callable=AsyncMock)
    @patch("agent.publish_to_medium", new_callable=AsyncMock)
    @patch("agent.generate_article")
    @pytest.mark.asyncio
    async def test_calls_all_publishers(
        self, mock_gen, mock_medium, mock_substack, mock_listverse, mock_vocal
    ):
        mock_gen.return_value = {"title": "Test", "content": "Body"}
        mock_vocal.return_value = {"title": "Vocal", "content": "V"}

        await main()

        assert mock_medium.called
        assert mock_substack.called
        assert mock_listverse.called
        assert mock_vocal.called

    @patch("agent.prepare_for_vocal")
    @patch("agent.publish_to_listverse", new_callable=AsyncMock)
    @patch("agent.publish_to_substack", new_callable=AsyncMock)
    @patch("agent.publish_to_medium", new_callable=AsyncMock)
    @patch("agent.generate_article")
    @pytest.mark.asyncio
    async def test_generates_articles_for_each_platform(
        self, mock_gen, mock_medium, mock_substack, mock_listverse, mock_vocal
    ):
        mock_gen.return_value = {"title": "T", "content": "C"}
        mock_vocal.return_value = {"title": "V", "content": "VC"}

        await main()

        # generate_article should be called 3 times (Medium, Substack, Listverse)
        # prepare_for_vocal calls it internally but is mocked here
        assert mock_gen.call_count == 3
        platforms = [call[0][1] for call in mock_gen.call_args_list]
        assert "Medium" in platforms
        assert "Substack" in platforms
        assert "Listverse" in platforms

    @patch("agent.prepare_for_vocal")
    @patch("agent.publish_to_listverse", new_callable=AsyncMock)
    @patch("agent.publish_to_substack", new_callable=AsyncMock)
    @patch("agent.publish_to_medium", new_callable=AsyncMock)
    @patch("agent.generate_article")
    @pytest.mark.asyncio
    async def test_uses_niche_based_on_day(
        self, mock_gen, mock_medium, mock_substack, mock_listverse, mock_vocal
    ):
        mock_gen.return_value = {"title": "T", "content": "C"}
        mock_vocal.return_value = {"title": "V", "content": "VC"}

        with patch("agent.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 15)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            await main()

        expected_niche = NICHES[15 % len(NICHES)]
        niche_used = mock_gen.call_args_list[0][0][0]
        assert niche_used == expected_niche

    @patch("agent.prepare_for_vocal")
    @patch("agent.publish_to_listverse", new_callable=AsyncMock)
    @patch("agent.publish_to_substack", new_callable=AsyncMock)
    @patch("agent.publish_to_medium", new_callable=AsyncMock)
    @patch("agent.generate_article")
    @pytest.mark.asyncio
    async def test_passes_generated_content_to_publishers(
        self, mock_gen, mock_medium, mock_substack, mock_listverse, mock_vocal
    ):
        mock_gen.return_value = {"title": "Generated Title", "content": "Generated Body"}
        mock_vocal.return_value = {"title": "V", "content": "VC"}

        await main()

        mock_medium.assert_called_once_with("Generated Title", "Generated Body")
        mock_substack.assert_called_once_with("Generated Title", "Generated Body")
        mock_listverse.assert_called_once_with("Generated Title", "Generated Body")


class TestNichesConfig:
    """Tests for the NICHES configuration."""

    def test_niches_list_is_not_empty(self):
        assert len(NICHES) > 0

    def test_niches_are_strings(self):
        for niche in NICHES:
            assert isinstance(niche, str)
            assert len(niche) > 0

    def test_niche_rotation_wraps_around(self):
        # Ensure day-based rotation covers all niches
        seen = set()
        for day in range(1, len(NICHES) + 1):
            seen.add(NICHES[day % len(NICHES)])
        assert len(seen) == len(NICHES)
