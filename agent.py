import asyncio
import json
import logging
import os
from datetime import datetime

from utils import browser_session, call_openrouter, login_to_platform, navigate_and_wait

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ====== Environment variables (from GitHub Secrets) ======
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MEDIUM_EMAIL = os.getenv("MEDIUM_EMAIL")
MEDIUM_PASS = os.getenv("MEDIUM_PASS")
SUBSTACK_EMAIL = os.getenv("SUBSTACK_EMAIL")
SUBSTACK_PASS = os.getenv("SUBSTACK_PASS")
SUBSTACK_PUBLICATION = os.getenv("SUBSTACK_PUBLICATION")
LISTVERSE_EMAIL = os.getenv("LISTVERSE_EMAIL")
LISTVERSE_PASS = os.getenv("LISTVERSE_PASS")

NICHES = [
    "Artificial Intelligence in Healthcare",
    "Impact of AI on World Economy",
    "Personal Finance Tips for 2026",
    "Cryptocurrency Trends",
    "Future of Work with AI",
]


# ====== Content Generation ======
def generate_article(niche, platform):
    """Generate an article for *niche* targeting *platform* via OpenRouter."""
    prompt = f"""
    Write a detailed article on "{niche}" for publishing on {platform}.
    Guidelines:
    - Medium: 1500 words, personal stories, actionable tips.
    - Substack: 2000 words, deep analysis, data-driven.
    - Listverse: 10-point list format, 1500 words, fascinating facts.
    Return ONLY JSON: {{"title": "...", "content": "..."}}
    """
    try:
        return call_openrouter(OPENROUTER_API_KEY, prompt)
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        return {
            "title": f"Guide to {niche}",
            "content": f"Full article about {niche}...",
        }


# ====== Publishers ======
async def publish_to_medium(title, content):
    """Publish an article to Medium."""
    async with browser_session() as page:
        try:
            await login_to_platform(
                page, "https://medium.com/login", MEDIUM_EMAIL, MEDIUM_PASS
            )

            await navigate_and_wait(page, "https://medium.com/new-story")
            await page.fill('h1[data-testid="postTitle"]', title)
            await page.keyboard.press("Tab")
            await page.keyboard.type(content)
            await page.click('button[data-testid="publishButton"]')
            await page.wait_for_timeout(3000)
            await page.click('button[data-testid="confirmPublishButton"]')
            await page.wait_for_timeout(5000)
            logger.info(f"Published to Medium: {title}")
        except Exception as e:
            logger.error(f"Medium publish error: {e}")


async def publish_to_substack(title, content):
    """Publish an article to Substack."""
    async with browser_session() as page:
        try:
            await login_to_platform(
                page,
                f"https://{SUBSTACK_PUBLICATION}/signin",
                SUBSTACK_EMAIL,
                SUBSTACK_PASS,
            )

            await navigate_and_wait(page, f"https://{SUBSTACK_PUBLICATION}/publish")
            await page.fill('input[name="title"]', title)
            await page.fill('div[contenteditable="true"]', content)
            await page.click('button:has-text("Publish")')
            await page.wait_for_timeout(3000)
            logger.info(f"Published to Substack: {title}")
        except Exception as e:
            logger.error(f"Substack publish error: {e}")


async def publish_to_listverse(title, content):
    """Submit an article to Listverse."""
    async with browser_session() as page:
        try:
            await login_to_platform(
                page,
                "https://listverse.com/wp-login.php",
                LISTVERSE_EMAIL,
                LISTVERSE_PASS,
                email_selector="#user_login",
                password_selector="#user_pass",
                submit_selector="#wp-submit",
            )

            await navigate_and_wait(page, "https://listverse.com/submit-a-list/")
            await page.fill('input[name="your-name"]', "AI Agent")
            await page.fill('input[name="your-email"]', LISTVERSE_EMAIL)
            await page.fill('input[name="your-subject"]', title)
            await page.fill('textarea[name="your-message"]', content)
            await page.click('input[type="submit"]')
            await page.wait_for_timeout(5000)
            logger.info(f"Submitted to Listverse: {title}")
        except Exception as e:
            logger.error(f"Listverse submit error: {e}")


# ====== Vocal Media ======
def prepare_for_vocal(niche):
    """Generate content for Vocal Media and save to a JSON file."""
    article = generate_article(niche, "Vocal Media")
    filename = f"vocal_{niche.replace(' ', '_')[:20]}.json"
    with open(filename, "w") as f:
        json.dump(article, f)
    logger.info(f"Vocal Media content ready: {article['title']}")
    return article


# ====== Main Workflow ======
PUBLISHERS = [
    ("Medium", publish_to_medium),
    ("Substack", publish_to_substack),
    ("Listverse", publish_to_listverse),
]


async def main():
    today_niche = NICHES[datetime.now().day % len(NICHES)]
    logger.info(f"Starting automation for niche: {today_niche}")

    for platform_name, publish_fn in PUBLISHERS:
        article = generate_article(today_niche, platform_name)
        await publish_fn(article["title"], article["content"])

    prepare_for_vocal(today_niche)
    logger.info("All tasks completed!")


if __name__ == "__main__":
    asyncio.run(main())
