# Publish as an independent GitHub repository

The desired destination is **https://github.com/mikelninh/venture-intelligence**.

## One-time GitHub action

1. Open https://github.com/new while signed in as `mikelninh`.
2. Repository name: `venture-intelligence`; visibility: **Public**.
3. Tick **Add a README file** to create the first `main` commit, then select **Create repository**.
4. Return to ChatGPT and provide the new repository URL. ChatGPT's connected GitHub tools can then commit the complete prepared source tree into the existing repository. Do not paste a personal access token.

The ChatGPT GitHub connection in this session can read/write repository contents, commits, and refs, but **cannot create a new GitHub repository**. An empty repo initialised with README allows the connector to create a single commit containing the full source, including the small synthetic sample PDFs and CI setup.

## Alternative: local git

Unzip this package, open a terminal in the extracted folder and use (after the GitHub repo exists):

```bash
git init -b main
git add .
git commit -m "Initial release: evidence-first Venture Intelligence v0.5"
git remote add origin https://github.com/mikelninh/venture-intelligence.git
git push -u origin main
```

Only use the local route if you want to push directly from your computer. GitHub will handle your credentials; never paste tokens into chat.

## Suggested repository description

`Evidence-first AI engineering prototype: PDF → cited facts → verification → human review. FastAPI, LangGraph entrypoint, synthetic evals & honest limitations.`

## Publishing checklist

- Preserve the code and PDF fixtures; do not commit `.env`, local database files, `__pycache__`, `.pytest_cache` or browser traces.
- Run `python -m pytest -q` (19 passed, 1 skipped here when LangGraph was unavailable).
- Check GitHub Actions after push. Only claim the real LangGraph runtime test passed once CI confirms it.
- Keep the public static interactive showcase separate from the unauthenticated local upload API.
- Revisit [the proposed Venture Pulse pilot](docs/PRODUCT_ROADMAP.md) **after** submitting the application and obtaining some external feedback.
