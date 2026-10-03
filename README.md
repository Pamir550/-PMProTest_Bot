# PMProTest_Bot

Separate read-only external QA tester.

Architecture:

Telegram → Test Engine → Evidence Collector → 41 category checks → AI Analyzer → Telegram report

Environment variables on Render:

- TELEGRAM_BOT_TOKEN — BotFather token. Secret.
- TARGET_REPO — target GitHub repository, e.g. owner/repository.
- GITHUB_TOKEN — optional read-only token if TARGET_REPO is private.
- TARGET_URL — target service URL.
- AI_API_KEY — AI provider API key. Secret.
- AI_BASE_URL — OpenAI-compatible API base; default is Groq.
- AI_MODEL — model name.

The tester does not write to the target repository, deploy it, restart it, or change its settings.

AI receives the collected evidence and is instructed not to invent test results. AI analysis is a second layer; PASS/FAIL/WARNING/NOT TESTED comes from the evidence collector.
