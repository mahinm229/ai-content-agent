"""Shared utilities for browser automation, authentication, and API calls."""

import json
import logging
from contextlib import asynccontextmanager

import requests
from playwright.async_api import Page, async_playwright

logger = logging.getLogger(__name__)


@asynccontextmanager
async def browser_session():
    """Async context manager for Playwright browser lifecycle.

    Yields a Page object and handles browser launch/cleanup.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            yield page
        finally:
            await browser.close()


async def login_to_platform(
    page: Page,
    login_url: str,
    email: str,
    password: str,
    email_selector: str = 'input[name="email"]',
    password_selector: str = 'input[name="password"]',
    submit_selector: str = 'button[type="submit"]',
):
    """Log in to a platform by filling credentials and submitting the form."""
    await page.goto(login_url)
    await page.fill(email_selector, email)
    await page.fill(password_selector, password)
    await page.click(submit_selector)
    await page.wait_for_timeout(5000)


async def navigate_and_wait(page: Page, url: str, wait_ms: int = 3000):
    """Navigate to a URL and wait for the page to settle."""
    await page.goto(url)
    await page.wait_for_timeout(wait_ms)


def parse_json_response(text: str) -> dict:
    """Strip markdown code fences and parse a JSON string."""
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return json.loads(cleaned.strip())


def call_openrouter(api_key: str, prompt: str, max_tokens: int = 4000) -> dict:
    """Call the OpenRouter API and return the parsed JSON response."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "google/gemini-2.0-flash-exp:free",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60,
    )
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    return parse_json_response(content)
