"""Unit tests for the generate_article function."""

import json
from unittest.mock import patch, MagicMock

import pytest

from agent import generate_article


class TestGenerateArticleSuccess:
    """Tests for successful article generation."""

    @patch("agent.requests.post")
    def test_returns_parsed_json_from_api(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": '{"title": "AI in Healthcare", "content": "Full article..."}'
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        result = generate_article("AI in Healthcare", "Medium")

        assert result["title"] == "AI in Healthcare"
        assert result["content"] == "Full article..."

    @patch("agent.requests.post")
    def test_strips_json_code_fences(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": '```json\n{"title": "Test", "content": "Body"}\n```'
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        result = generate_article("Test Niche", "Substack")

        assert result["title"] == "Test"
        assert result["content"] == "Body"

    @patch("agent.requests.post")
    def test_sends_correct_headers_and_payload(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"title": "T", "content": "C"}'}}]
        }
        mock_post.return_value = mock_response

        with patch("agent.OPENROUTER_API_KEY", "test-key-123"):
            generate_article("Crypto", "Medium")

        call_args = mock_post.call_args
        assert call_args[1]["headers"]["Authorization"] == "Bearer test-key-123"
        assert call_args[1]["headers"]["Content-Type"] == "application/json"
        payload = call_args[1]["json"]
        assert payload["model"] == "google/gemini-2.0-flash-exp:free"
        assert payload["max_tokens"] == 4000
        assert "Crypto" in payload["messages"][0]["content"]
        assert "Medium" in payload["messages"][0]["content"]

    @patch("agent.requests.post")
    def test_uses_correct_api_url(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"title": "T", "content": "C"}'}}]
        }
        mock_post.return_value = mock_response

        generate_article("Finance", "Listverse")

        url = mock_post.call_args[0][0]
        assert url == "https://openrouter.ai/api/v1/chat/completions"

    @patch("agent.requests.post")
    def test_timeout_is_set(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"title": "T", "content": "C"}'}}]
        }
        mock_post.return_value = mock_response

        generate_article("AI", "Medium")

        assert mock_post.call_args[1]["timeout"] == 60


class TestGenerateArticleErrorHandling:
    """Tests for error handling in article generation."""

    @patch("agent.requests.post")
    def test_returns_fallback_on_network_error(self, mock_post):
        mock_post.side_effect = Exception("Connection timeout")

        result = generate_article("AI in Healthcare", "Medium")

        assert result["title"] == "Guide to AI in Healthcare"
        assert "AI in Healthcare" in result["content"]

    @patch("agent.requests.post")
    def test_returns_fallback_on_invalid_json(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "not valid json at all"}}]
        }
        mock_post.return_value = mock_response

        result = generate_article("Crypto Trends", "Substack")

        assert result["title"] == "Guide to Crypto Trends"
        assert "Crypto Trends" in result["content"]

    @patch("agent.requests.post")
    def test_returns_fallback_on_missing_choices_key(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "rate limited"}
        mock_post.return_value = mock_response

        result = generate_article("Finance", "Listverse")

        assert result["title"] == "Guide to Finance"
        assert "Finance" in result["content"]

    @patch("agent.requests.post")
    def test_returns_fallback_on_empty_choices(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": []}
        mock_post.return_value = mock_response

        result = generate_article("Work AI", "Medium")

        assert result["title"] == "Guide to Work AI"


class TestGenerateArticlePlatformPrompts:
    """Tests verifying platform-specific prompt content."""

    @patch("agent.requests.post")
    def test_medium_prompt_mentions_personal_stories(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"title": "T", "content": "C"}'}}]
        }
        mock_post.return_value = mock_response

        generate_article("AI", "Medium")

        prompt = mock_post.call_args[1]["json"]["messages"][0]["content"]
        assert "personal stories" in prompt

    @patch("agent.requests.post")
    def test_substack_prompt_mentions_deep_analysis(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"title": "T", "content": "C"}'}}]
        }
        mock_post.return_value = mock_response

        generate_article("AI", "Substack")

        prompt = mock_post.call_args[1]["json"]["messages"][0]["content"]
        assert "deep analysis" in prompt

    @patch("agent.requests.post")
    def test_listverse_prompt_mentions_list_format(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"title": "T", "content": "C"}'}}]
        }
        mock_post.return_value = mock_response

        generate_article("AI", "Listverse")

        prompt = mock_post.call_args[1]["json"]["messages"][0]["content"]
        assert "list format" in prompt
