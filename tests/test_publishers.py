"""Unit tests for the publisher functions (Medium, Substack, Listverse)."""

import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from agent import publish_to_medium, publish_to_substack, publish_to_listverse


@pytest.fixture
def mock_playwright():
    """Create a mock Playwright context with page actions."""
    mock_page = AsyncMock()
    mock_browser = AsyncMock()
    mock_browser.new_page.return_value = mock_page
    mock_browser.close = AsyncMock()

    mock_chromium = AsyncMock()
    mock_chromium.launch.return_value = mock_browser

    mock_pw_instance = MagicMock()
    mock_pw_instance.chromium = mock_chromium

    mock_pw_context = AsyncMock()
    mock_pw_context.__aenter__ = AsyncMock(return_value=mock_pw_instance)
    mock_pw_context.__aexit__ = AsyncMock(return_value=False)

    return mock_pw_context, mock_page, mock_browser


class TestPublishToMedium:
    """Tests for Medium publishing."""

    @patch("agent.async_playwright")
    @patch("agent.MEDIUM_EMAIL", "test@example.com")
    @patch("agent.MEDIUM_PASS", "password123")
    @pytest.mark.asyncio
    async def test_logs_in_and_publishes(self, mock_async_pw):
        mock_page = AsyncMock()
        mock_browser = AsyncMock()
        mock_browser.new_page.return_value = mock_page

        mock_chromium = AsyncMock()
        mock_chromium.launch.return_value = mock_browser

        mock_pw = MagicMock()
        mock_pw.chromium = mock_chromium

        mock_async_pw.return_value.__aenter__ = AsyncMock(return_value=mock_pw)
        mock_async_pw.return_value.__aexit__ = AsyncMock(return_value=False)

        await publish_to_medium("Test Title", "Test Content")

        mock_chromium.launch.assert_called_once_with(headless=True)
        mock_page.goto.assert_any_call("https://medium.com/login")
        mock_page.fill.assert_any_call('input[name="email"]', "test@example.com")
        mock_page.fill.assert_any_call('input[name="password"]', "password123")
        mock_page.click.assert_any_call('button[type="submit"]')
        mock_page.goto.assert_any_call("https://medium.com/new-story")
        mock_page.fill.assert_any_call('h1[data-testid="postTitle"]', "Test Title")
        mock_browser.close.assert_called_once()

    @patch("agent.async_playwright")
    @patch("agent.MEDIUM_EMAIL", "test@example.com")
    @patch("agent.MEDIUM_PASS", "password123")
    @pytest.mark.asyncio
    async def test_closes_browser_on_error(self, mock_async_pw):
        mock_page = AsyncMock()
        mock_page.goto.side_effect = Exception("Navigation failed")
        mock_browser = AsyncMock()
        mock_browser.new_page.return_value = mock_page

        mock_chromium = AsyncMock()
        mock_chromium.launch.return_value = mock_browser

        mock_pw = MagicMock()
        mock_pw.chromium = mock_chromium

        mock_async_pw.return_value.__aenter__ = AsyncMock(return_value=mock_pw)
        mock_async_pw.return_value.__aexit__ = AsyncMock(return_value=False)

        await publish_to_medium("Title", "Content")

        mock_browser.close.assert_called_once()

    @patch("agent.async_playwright")
    @patch("agent.MEDIUM_EMAIL", "test@example.com")
    @patch("agent.MEDIUM_PASS", "password123")
    @pytest.mark.asyncio
    async def test_launches_headless_browser(self, mock_async_pw):
        mock_page = AsyncMock()
        mock_browser = AsyncMock()
        mock_browser.new_page.return_value = mock_page

        mock_chromium = AsyncMock()
        mock_chromium.launch.return_value = mock_browser

        mock_pw = MagicMock()
        mock_pw.chromium = mock_chromium

        mock_async_pw.return_value.__aenter__ = AsyncMock(return_value=mock_pw)
        mock_async_pw.return_value.__aexit__ = AsyncMock(return_value=False)

        await publish_to_medium("Title", "Content")

        mock_chromium.launch.assert_called_once_with(headless=True)


class TestPublishToSubstack:
    """Tests for Substack publishing."""

    @patch("agent.async_playwright")
    @patch("agent.SUBSTACK_EMAIL", "sub@example.com")
    @patch("agent.SUBSTACK_PASS", "subpass")
    @patch("agent.SUBSTACK_PUBLICATION", "mysubstack.substack.com")
    @pytest.mark.asyncio
    async def test_logs_in_and_publishes(self, mock_async_pw):
        mock_page = AsyncMock()
        mock_browser = AsyncMock()
        mock_browser.new_page.return_value = mock_page

        mock_chromium = AsyncMock()
        mock_chromium.launch.return_value = mock_browser

        mock_pw = MagicMock()
        mock_pw.chromium = mock_chromium

        mock_async_pw.return_value.__aenter__ = AsyncMock(return_value=mock_pw)
        mock_async_pw.return_value.__aexit__ = AsyncMock(return_value=False)

        await publish_to_substack("Sub Title", "Sub Content")

        mock_page.goto.assert_any_call("https://mysubstack.substack.com/signin")
        mock_page.fill.assert_any_call('input[name="email"]', "sub@example.com")
        mock_page.fill.assert_any_call('input[name="password"]', "subpass")
        mock_page.goto.assert_any_call("https://mysubstack.substack.com/publish")
        mock_page.fill.assert_any_call('input[name="title"]', "Sub Title")
        mock_page.fill.assert_any_call('div[contenteditable="true"]', "Sub Content")
        mock_browser.close.assert_called_once()

    @patch("agent.async_playwright")
    @patch("agent.SUBSTACK_EMAIL", "sub@example.com")
    @patch("agent.SUBSTACK_PASS", "subpass")
    @patch("agent.SUBSTACK_PUBLICATION", "mysubstack.substack.com")
    @pytest.mark.asyncio
    async def test_closes_browser_on_error(self, mock_async_pw):
        mock_page = AsyncMock()
        mock_page.goto.side_effect = Exception("Timeout")
        mock_browser = AsyncMock()
        mock_browser.new_page.return_value = mock_page

        mock_chromium = AsyncMock()
        mock_chromium.launch.return_value = mock_browser

        mock_pw = MagicMock()
        mock_pw.chromium = mock_chromium

        mock_async_pw.return_value.__aenter__ = AsyncMock(return_value=mock_pw)
        mock_async_pw.return_value.__aexit__ = AsyncMock(return_value=False)

        await publish_to_substack("Title", "Content")

        mock_browser.close.assert_called_once()

    @patch("agent.async_playwright")
    @patch("agent.SUBSTACK_EMAIL", "sub@example.com")
    @patch("agent.SUBSTACK_PASS", "subpass")
    @patch("agent.SUBSTACK_PUBLICATION", "mysubstack.substack.com")
    @pytest.mark.asyncio
    async def test_clicks_publish_button(self, mock_async_pw):
        mock_page = AsyncMock()
        mock_browser = AsyncMock()
        mock_browser.new_page.return_value = mock_page

        mock_chromium = AsyncMock()
        mock_chromium.launch.return_value = mock_browser

        mock_pw = MagicMock()
        mock_pw.chromium = mock_chromium

        mock_async_pw.return_value.__aenter__ = AsyncMock(return_value=mock_pw)
        mock_async_pw.return_value.__aexit__ = AsyncMock(return_value=False)

        await publish_to_substack("Title", "Content")

        mock_page.click.assert_any_call('button:has-text("Publish")')


class TestPublishToListverse:
    """Tests for Listverse publishing."""

    @patch("agent.async_playwright")
    @patch("agent.LISTVERSE_EMAIL", "lv@example.com")
    @patch("agent.LISTVERSE_PASS", "lvpass")
    @pytest.mark.asyncio
    async def test_logs_in_and_submits(self, mock_async_pw):
        mock_page = AsyncMock()
        mock_browser = AsyncMock()
        mock_browser.new_page.return_value = mock_page

        mock_chromium = AsyncMock()
        mock_chromium.launch.return_value = mock_browser

        mock_pw = MagicMock()
        mock_pw.chromium = mock_chromium

        mock_async_pw.return_value.__aenter__ = AsyncMock(return_value=mock_pw)
        mock_async_pw.return_value.__aexit__ = AsyncMock(return_value=False)

        await publish_to_listverse("LV Title", "LV Content")

        mock_page.goto.assert_any_call("https://listverse.com/wp-login.php")
        mock_page.fill.assert_any_call('#user_login', "lv@example.com")
        mock_page.fill.assert_any_call('#user_pass', "lvpass")
        mock_page.click.assert_any_call('#wp-submit')
        mock_page.goto.assert_any_call("https://listverse.com/submit-a-list/")
        mock_page.fill.assert_any_call('input[name="your-name"]', "AI Agent")
        mock_page.fill.assert_any_call('input[name="your-email"]', "lv@example.com")
        mock_page.fill.assert_any_call('input[name="your-subject"]', "LV Title")
        mock_page.fill.assert_any_call('textarea[name="your-message"]', "LV Content")
        mock_page.click.assert_any_call('input[type="submit"]')
        mock_browser.close.assert_called_once()

    @patch("agent.async_playwright")
    @patch("agent.LISTVERSE_EMAIL", "lv@example.com")
    @patch("agent.LISTVERSE_PASS", "lvpass")
    @pytest.mark.asyncio
    async def test_closes_browser_on_error(self, mock_async_pw):
        mock_page = AsyncMock()
        mock_page.goto.side_effect = Exception("DNS error")
        mock_browser = AsyncMock()
        mock_browser.new_page.return_value = mock_page

        mock_chromium = AsyncMock()
        mock_chromium.launch.return_value = mock_browser

        mock_pw = MagicMock()
        mock_pw.chromium = mock_chromium

        mock_async_pw.return_value.__aenter__ = AsyncMock(return_value=mock_pw)
        mock_async_pw.return_value.__aexit__ = AsyncMock(return_value=False)

        await publish_to_listverse("Title", "Content")

        mock_browser.close.assert_called_once()

    @patch("agent.async_playwright")
    @patch("agent.LISTVERSE_EMAIL", "lv@example.com")
    @patch("agent.LISTVERSE_PASS", "lvpass")
    @pytest.mark.asyncio
    async def test_navigates_to_submit_page_after_login(self, mock_async_pw):
        mock_page = AsyncMock()
        mock_browser = AsyncMock()
        mock_browser.new_page.return_value = mock_page

        mock_chromium = AsyncMock()
        mock_chromium.launch.return_value = mock_browser

        mock_pw = MagicMock()
        mock_pw.chromium = mock_chromium

        mock_async_pw.return_value.__aenter__ = AsyncMock(return_value=mock_pw)
        mock_async_pw.return_value.__aexit__ = AsyncMock(return_value=False)

        await publish_to_listverse("Title", "Content")

        goto_calls = [call[0][0] for call in mock_page.goto.call_args_list]
        login_idx = goto_calls.index("https://listverse.com/wp-login.php")
        submit_idx = goto_calls.index("https://listverse.com/submit-a-list/")
        assert login_idx < submit_idx
