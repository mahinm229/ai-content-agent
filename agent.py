import os
import re
import asyncio
import json
import logging
from datetime import datetime
from playwright.async_api import async_playwright
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ====== Environment Variable Validation ======
REQUIRED_ENV_VARS = [
    "OPENROUTER_API_KEY",
    "MEDIUM_EMAIL", "MEDIUM_PASS",
    "SUBSTACK_EMAIL", "SUBSTACK_PASS", "SUBSTACK_PUBLICATION",
    "LISTVERSE_EMAIL", "LISTVERSE_PASS",
]


def _validate_env_vars():
    """Validate all required environment variables are set."""
    missing = [v for v in REQUIRED_ENV_VARS if not os.getenv(v)]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Set them in GitHub Secrets or your local environment."
        )


def _validate_publication_name(name):
    """Validate SUBSTACK_PUBLICATION to prevent URL injection/SSRF."""
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-]{0,62}\.substack\.com$', name):
        raise ValueError(
            f"Invalid SUBSTACK_PUBLICATION: '{name}'. "
            "Expected format: 'yourname.substack.com'"
        )


# ====== এনভায়রনমেন্ট ভেরিয়েবল (GitHub Secrets থেকে আসবে) ======
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
MEDIUM_EMAIL = os.getenv("MEDIUM_EMAIL", "")
MEDIUM_PASS = os.getenv("MEDIUM_PASS", "")
SUBSTACK_EMAIL = os.getenv("SUBSTACK_EMAIL", "")
SUBSTACK_PASS = os.getenv("SUBSTACK_PASS", "")
SUBSTACK_PUBLICATION = os.getenv("SUBSTACK_PUBLICATION", "")
LISTVERSE_EMAIL = os.getenv("LISTVERSE_EMAIL", "")
LISTVERSE_PASS = os.getenv("LISTVERSE_PASS", "")

# প্রতিদিন রোটেট করার জন্য niches
NICHES = [
    "Artificial Intelligence in Healthcare",
    "Impact of AI on World Economy",
    "Personal Finance Tips for 2026",
    "Cryptocurrency Trends",
    "Future of Work with AI"
]

# ====== ১. কন্টেন্ট জেনারেশন (OpenRouter - ফ্রি) ======
def generate_article(niche, platform):
    """OpenRouter ব্যবহার করে আর্টিকেল জেনারেট করে"""
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
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                                 headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        if "choices" not in data or not data["choices"]:
            raise ValueError("API returned empty choices")
        content = data['choices'][0]['message']['content']
        # JSON ক্লিনআপ
        if content.startswith('```json'): 
            content = content[7:-3]
        return json.loads(content)
    except requests.exceptions.HTTPError as e:
        logger.error(f"API request failed with status {e.response.status_code}")
        return {"title": f"Guide to {niche}", "content": f"Full article about {niche}..."}
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        logger.error(f"Failed to parse API response: {type(e).__name__}")
        return {"title": f"Guide to {niche}", "content": f"Full article about {niche}..."}
    except Exception as e:
        logger.error(f"Generation failed: {type(e).__name__}")
        return {"title": f"Guide to {niche}", "content": f"Full article about {niche}..."}

# ====== ২. পাবলিশার (Playwright দিয়ে API ছাড়া) ======
async def publish_to_medium(title, content):
    """Medium-এ লগইন করে পোস্ট করুন"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
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
            logger.error(f"Medium publish error: {type(e).__name__}")
        finally:
            await browser.close()

async def publish_to_substack(title, content):
    """Substack-এ লগইন করে পোস্ট করুন"""
    _validate_publication_name(SUBSTACK_PUBLICATION)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
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
            logger.error(f"Substack publish error: {type(e).__name__}")
        finally:
            await browser.close()

async def publish_to_listverse(title, content):
    """Listverse-এ লগইন করে সাবমিট করুন"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
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
            logger.error(f"Listverse submit error: {type(e).__name__}")
        finally:
            await browser.close()

# ====== ৩. ভোকাল মিডিয়ার জন্য প্রস্তুত করা ======
def _sanitize_filename(name):
    """Sanitize a string for safe use as a filename."""
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', name)[:40]


def prepare_for_vocal(niche):
    """Vocal Media-র জন্য কন্টেন্ট তৈরি করে JSON ফাইল করে"""
    article = generate_article(niche, "Vocal Media")
    safe_name = _sanitize_filename(niche)
    with open(f"vocal_{safe_name}.json", "w") as f:
        json.dump(article, f)
    logger.info(f"Vocal Media content ready: {article['title']}")
    return article

# ====== ৪. মেইন ওয়ার্কফ্লো ======
async def main():
    _validate_env_vars()

    # আজকের niche নির্ধারণ (দিন অনুযায়ী রোটেট)
    today_niche = NICHES[datetime.now().day % len(NICHES)]
    logger.info(f"Starting automation for niche: {today_niche}")
    
    # ১. Medium
    article = generate_article(today_niche, "Medium")
    await publish_to_medium(article['title'], article['content'])
    
    # ২. Substack
    article = generate_article(today_niche, "Substack")
    await publish_to_substack(article['title'], article['content'])
    
    # ৩. Listverse
    article = generate_article(today_niche, "Listverse")
    await publish_to_listverse(article['title'], article['content'])
    
    # ৪. Vocal (শুধু জেনারেট করে ফাইলে রাখে)
    prepare_for_vocal(today_niche)
    logger.info("All tasks completed!")

if __name__ == "__main__":
    asyncio.run(main())
