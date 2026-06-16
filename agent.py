import os
import asyncio
import json
import logging
import sys
from datetime import datetime
from playwright.async_api import async_playwright
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ArticleGenerationError(Exception):
    """Raised when article generation via OpenRouter fails."""


class PublishError(Exception):
    """Raised when publishing to a platform fails."""


class ConfigError(Exception):
    """Raised when required environment variables are missing."""


# ====== এনভায়রনমেন্ট ভেরিয়েবল (GitHub Secrets থেকে আসবে) ======
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MEDIUM_EMAIL = os.getenv("MEDIUM_EMAIL")
MEDIUM_PASS = os.getenv("MEDIUM_PASS")
SUBSTACK_EMAIL = os.getenv("SUBSTACK_EMAIL")
SUBSTACK_PASS = os.getenv("SUBSTACK_PASS")
SUBSTACK_PUBLICATION = os.getenv("SUBSTACK_PUBLICATION")
LISTVERSE_EMAIL = os.getenv("LISTVERSE_EMAIL")
LISTVERSE_PASS = os.getenv("LISTVERSE_PASS")

# প্রতিদিন রোটেট করার জন্য niches
NICHES = [
    "Artificial Intelligence in Healthcare",
    "Impact of AI on World Economy",
    "Personal Finance Tips for 2026",
    "Cryptocurrency Trends",
    "Future of Work with AI"
]


def validate_env_vars(required_vars):
    """Validate that all required environment variables are set.

    Returns a list of missing variable names, empty if all are present.
    """
    missing = [var for var in required_vars if not os.getenv(var)]
    return missing


# ====== ১. কন্টেন্ট জেনারেশন (OpenRouter - ফ্রি) ======
def generate_article(niche, platform):
    """OpenRouter ব্যবহার করে আর্টিকেল জেনারেট করে।

    Raises:
        ArticleGenerationError: If the API call fails, returns an unexpected
            response, or the response cannot be parsed as JSON.
    """
    if not OPENROUTER_API_KEY:
        raise ConfigError("OPENROUTER_API_KEY is not set")

    prompt = f"""
    Write a detailed article on "{niche}" for publishing on {platform}.
    Guidelines:
    - Medium: 1500 words, personal stories, actionable tips.
    - Substack: 2000 words, deep analysis, data-driven.
    - Listverse: 10-point list format, 1500 words, fascinating facts.
    Return ONLY JSON: {{"title": "...", "content": "..."}}
    """

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "google/gemini-2.0-flash-exp:free",  # ফ্রি মডেল
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4000
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers, json=payload, timeout=60
        )
        response.raise_for_status()
    except requests.RequestException as e:
        raise ArticleGenerationError(
            f"OpenRouter API request failed: {e}"
        ) from e

    try:
        data = response.json()
    except ValueError as e:
        raise ArticleGenerationError(
            f"Failed to parse API response as JSON: {e}"
        ) from e

    try:
        content = data['choices'][0]['message']['content']
    except (KeyError, IndexError, TypeError) as e:
        raise ArticleGenerationError(
            f"Unexpected API response structure: {e} — response: {data}"
        ) from e

    # JSON ক্লিনআপ
    if content.startswith('```json'):
        content = content[7:-3]

    try:
        article = json.loads(content)
    except json.JSONDecodeError as e:
        raise ArticleGenerationError(
            f"Failed to parse article JSON from model output: {e}"
        ) from e

    if "title" not in article or "content" not in article:
        raise ArticleGenerationError(
            f"Article JSON missing required keys 'title'/'content': {list(article.keys())}"
        )

    return article


# ====== ২. পাবলিশার (Playwright দিয়ে API ছাড়া) ======
async def publish_to_medium(title, content):
    """Medium-এ লগইন করে পোস্ট করুন।

    Raises:
        PublishError: If any step of the publish flow fails.
        ConfigError: If Medium credentials are not set.
    """
    if not MEDIUM_EMAIL or not MEDIUM_PASS:
        raise ConfigError("MEDIUM_EMAIL and MEDIUM_PASS must be set")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            await page.goto("https://medium.com/login")
            await page.fill('input[name="email"]', MEDIUM_EMAIL)
            await page.fill('input[name="password"]', MEDIUM_PASS)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(5000)

            await page.goto("https://medium.com/new-story")
            await page.wait_for_timeout(3000)
            await page.fill('h1[data-testid="postTitle"]', title)
            await page.keyboard.press('Tab')
            await page.keyboard.type(content)
            await page.click('button[data-testid="publishButton"]')
            await page.wait_for_timeout(3000)
            await page.click('button[data-testid="confirmPublishButton"]')
            await page.wait_for_timeout(5000)
            logger.info(f"Published to Medium: {title}")
        except Exception as e:
            raise PublishError(f"Medium publish failed: {e}") from e
        finally:
            await browser.close()


async def publish_to_substack(title, content):
    """Substack-এ লগইন করে পোস্ট করুন।

    Raises:
        PublishError: If any step of the publish flow fails.
        ConfigError: If Substack credentials are not set.
    """
    if not SUBSTACK_EMAIL or not SUBSTACK_PASS or not SUBSTACK_PUBLICATION:
        raise ConfigError(
            "SUBSTACK_EMAIL, SUBSTACK_PASS, and SUBSTACK_PUBLICATION must be set"
        )

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            await page.goto(f"https://{SUBSTACK_PUBLICATION}/signin")
            await page.fill('input[name="email"]', SUBSTACK_EMAIL)
            await page.fill('input[name="password"]', SUBSTACK_PASS)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(5000)

            await page.goto(f"https://{SUBSTACK_PUBLICATION}/publish")
            await page.wait_for_timeout(3000)
            await page.fill('input[name="title"]', title)
            await page.fill('div[contenteditable="true"]', content)
            await page.click('button:has-text("Publish")')
            await page.wait_for_timeout(3000)
            logger.info(f"Published to Substack: {title}")
        except Exception as e:
            raise PublishError(f"Substack publish failed: {e}") from e
        finally:
            await browser.close()


async def publish_to_listverse(title, content):
    """Listverse-এ লগইন করে সাবমিট করুন।

    Raises:
        PublishError: If any step of the submit flow fails.
        ConfigError: If Listverse credentials are not set.
    """
    if not LISTVERSE_EMAIL or not LISTVERSE_PASS:
        raise ConfigError("LISTVERSE_EMAIL and LISTVERSE_PASS must be set")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            await page.goto("https://listverse.com/wp-login.php")
            await page.fill('#user_login', LISTVERSE_EMAIL)
            await page.fill('#user_pass', LISTVERSE_PASS)
            await page.click('#wp-submit')
            await page.wait_for_timeout(5000)

            await page.goto("https://listverse.com/submit-a-list/")
            await page.wait_for_timeout(3000)
            await page.fill('input[name="your-name"]', "AI Agent")
            await page.fill('input[name="your-email"]', LISTVERSE_EMAIL)
            await page.fill('input[name="your-subject"]', title)
            await page.fill('textarea[name="your-message"]', content)
            await page.click('input[type="submit"]')
            await page.wait_for_timeout(5000)
            logger.info(f"Submitted to Listverse: {title}")
        except Exception as e:
            raise PublishError(f"Listverse submit failed: {e}") from e
        finally:
            await browser.close()


# ====== ৩. ভোকাল মিডিয়ার জন্য প্রস্তুত করা ======
def prepare_for_vocal(niche):
    """Vocal Media-র জন্য কন্টেন্ট তৈরি করে JSON ফাইল করে।

    Raises:
        ArticleGenerationError: If article generation fails.
        OSError: If writing the JSON file fails.
    """
    article = generate_article(niche, "Vocal Media")
    filename = f"vocal_{niche.replace(' ', '_')[:20]}.json"
    try:
        with open(filename, "w") as f:
            json.dump(article, f)
    except OSError as e:
        raise OSError(f"Failed to write Vocal Media file '{filename}': {e}") from e
    logger.info(f"Vocal Media content ready: {article['title']}")
    return article


# ====== ৪. মেইন ওয়ার্কফ্লো ======
async def main():
    # Validate that required env vars are set before doing any work
    missing = validate_env_vars([
        "OPENROUTER_API_KEY",
        "MEDIUM_EMAIL", "MEDIUM_PASS",
        "SUBSTACK_EMAIL", "SUBSTACK_PASS", "SUBSTACK_PUBLICATION",
        "LISTVERSE_EMAIL", "LISTVERSE_PASS",
    ])
    if missing:
        logger.warning(
            "Missing environment variables: %s — "
            "platforms that need them will be skipped",
            ", ".join(missing),
        )

    # আজকের niche নির্ধারণ (দিন অনুযায়ী রোটেট)
    today_niche = NICHES[datetime.now().day % len(NICHES)]
    logger.info(f"Starting automation for niche: {today_niche}")

    failures = []

    # ১. Medium
    try:
        article = generate_article(today_niche, "Medium")
        await publish_to_medium(article['title'], article['content'])
    except (ArticleGenerationError, PublishError, ConfigError) as e:
        logger.error(f"Medium pipeline failed: {e}")
        failures.append(("Medium", e))

    # ২. Substack
    try:
        article = generate_article(today_niche, "Substack")
        await publish_to_substack(article['title'], article['content'])
    except (ArticleGenerationError, PublishError, ConfigError) as e:
        logger.error(f"Substack pipeline failed: {e}")
        failures.append(("Substack", e))

    # ৩. Listverse
    try:
        article = generate_article(today_niche, "Listverse")
        await publish_to_listverse(article['title'], article['content'])
    except (ArticleGenerationError, PublishError, ConfigError) as e:
        logger.error(f"Listverse pipeline failed: {e}")
        failures.append(("Listverse", e))

    # ৪. Vocal (শুধু জেনারেট করে ফাইলে রাখে)
    try:
        prepare_for_vocal(today_niche)
    except (ArticleGenerationError, OSError, ConfigError) as e:
        logger.error(f"Vocal Media pipeline failed: {e}")
        failures.append(("Vocal Media", e))

    if failures:
        failed_names = ", ".join(name for name, _ in failures)
        logger.error(f"Completed with failures on: {failed_names}")
        sys.exit(1)

    logger.info("All tasks completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
