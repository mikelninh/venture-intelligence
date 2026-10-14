# v0.5 independent verification

The local offline test session completed **19 pytest tests**; one actual LangGraph integration test was skipped because its dependency could not be installed in the isolated environment. The local Chromium browser smoke also completed.

GitHub Actions is configured to install the actual `langgraph` package and execute the suite with `VI_WORKFLOW_ENGINE=langgraph`. An Actions green build is the first independent verification that the real StateGraph path works on a network-connected runner.

All example businesses are fictional; metrics are based only on 30 synthetic PDFs and do **not** demonstrate real-world extraction accuracy. This project does not make investment decisions.

Review the exact scope and limits in [docs/VERIFICATION.md](../docs/VERIFICATION.md).
