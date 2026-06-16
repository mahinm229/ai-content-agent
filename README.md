# AI Content Agent

This is a fully automated system that generates articles daily using AI and publishes them on Medium, Substack, and Listverse.

## Features
- Generates content daily across different niches
- Uses OpenRouter (Gemini) to generate high-quality articles
- Uses Playwright for browser automation and auto-publishing
- Can run on GitHub Actions for a completely free setup

## Secrets Setup
GitHub Repository → Settings → Secrets and variables → Actions 
Add the following secrets:
- OPENROUTER_API_KEY
- MEDIUM_EMAIL, MEDIUM_PASS
- SUBSTACK_EMAIL, SUBSTACK_PASS, SUBSTACK_PUBLICATION
- LISTVERSE_EMAIL, LISTVERSE_PASS
