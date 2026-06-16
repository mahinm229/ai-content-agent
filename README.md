# AI Content Agent

এটি একটি সম্পূর্ণ অটোমেটেড সিস্টেম যা প্রতিদিন AI ব্যবহার করে আর্টিকেল লিখে Medium, Substack ও Listverse-এ পাবলিশ করে।

## ফিচারসমূহ
- প্রতিদিন ভিন্ন ভিন্ন Niche-তে কন্টেন্ট তৈরি করে
- OpenRouter (Gemini) দিয়ে লেখা তৈরি করে
- Playwright দিয়ে ব্রাউজার অটোমেশন করে পোস্ট করে
- GitHub Actions-এ চললে সম্পূর্ণ ফ্রি

## Secrets সেটআপ করুন
GitHub Repository → Settings → Secrets and variables → Actions-এ নিচের গুলো যোগ করুন:
- OPENROUTER_API_KEY
- MEDIUM_EMAIL, MEDIUM_PASS
- SUBSTACK_EMAIL, SUBSTACK_PASS, SUBSTACK_PUBLICATION
- LISTVERSE_EMAIL, LISTVERSE_PASS
