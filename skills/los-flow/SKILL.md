---
name: los-flow
description: Root-cause analysis for LOS integration failures — reads the integration source code for the failing workflow, reproduces the flow in a Playwright browser, and diagnoses DOM changes, timing issues, or logic errors. Use when a LOS automation/workflow error is reported.
arguments: [los, action, error]
argument-hint: <los-name> <action/workflow> <error-message>
---

# MISSION: ROOT CAUSE ANALYSIS (RCA) WITH PLAYWRIGHT MCP

<context>
Target System: "$los"
Target Workflow: "$action"
Reported Error:
"""
$error
"""
</context>

<investigation_protocol>
1.  **CONTEXT LOADING (Mandatory First Step):**
    -   Locate the source code for "$action" within `app/los-integration-service` (likely under a folder named "$los").
    -   Read `app/los-integration-service/.env` to load environment config.
    -   *Constraint:* Do NOT start the browser until you have read the source code and understood the logic flow.

2.  **REPRODUCTION (Browser Execution):**
    -   Use `mcp-server-playwright` to open the browser.
    -   Manually execute the steps exactly as defined in the source code.
    -   **Goal:** Try to trigger the reported error.

3.  **DIAGNOSIS:**
    -   Compare the code's expected selector/behavior vs. the actual browser state.
    -   Determine if the issue is:
        a) **DOM Change:** Selectors no longer match.
        b) **Timing/Race Condition:** Script is too fast for the UI.
        c) **Logic Error:** The business logic in the code is flawed.
</investigation_protocol>

<output>
Provide a concise analysis and the corrected code block (if applicable).
</output>