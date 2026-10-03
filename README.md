# PMProTest_Bot

Read-only QA tester for a target Telegram bot/project.

Flow:
1. In chat send /start.
2. Send the target bot name.
3. Send the target bot username.
4. Open the Mini App.
5. Press TEST.
6. Review 41 categories, errors/warnings, GitHub/Render status and history.

The tester only reads target GitHub files, reads Render service/deploy information, and probes the target health endpoint. It does not contain target-project write, deploy, restart, environment-variable update, or file-edit operations.

Required environment variables:
- TELEGRAM_BOT_TOKEN (secret)
- TARGET_REPO
- TARGET_URL
- TARGET_RENDER_SERVICE_ID
- RENDER_API_KEY (secret, read-only use)
- GITHUB_TOKEN (secret if the target repository is private)

Optional:
- WEBAPP_URL
- AI_API_KEY
- AI_BASE_URL
- AI_MODEL
