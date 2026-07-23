# InsightLens - testing guide

> Status note (July 22, 2026): The app now runs on Render as a web service with a Neon Postgres database and uses OpenAI as its single AI provider. Test against the live app at https://insightlens-wz4n.onrender.com or a local build. Any Replit-specific or Hugging Face-specific steps elsewhere in the docs are historical. The test scenarios below still apply.

## Overview

This guide gives step-by-step test cases for the main features of InsightLens. Each case lists what to do and what you should see. The live app is a server-rendered Flask app, so pages load as full HTML, not a single-page client.

Note on cold starts: the live app is on Render's free tier. If it has been idle, the first request can take up to about a minute while the service wakes, and you may see a brief 404 or a spinner on the very first hit. Reload once and it settles.

## How to reach the app

1. Open https://insightlens-wz4n.onrender.com
2. Expected: the home page loads with the InsightLens header, a document upload form, and an EDGAR search box.

## Test category 1: getting a document in

### Feature 1: EDGAR search for a public filing

Test steps:
1. On the home page, find the EDGAR search box.
2. Enter a well-known company name, for example "Apple".
3. Submit the search.
4. Expected: a results list appears with matching companies and their CIK numbers (for Apple, "Apple Inc." with a real CIK).
5. Pick a company and select a 10-K filing to import.
6. Expected: the filing is fetched and a document is created, then analysis begins.

### Feature 2: PDF upload

Test steps:
1. On the home page, use the upload form to select a company financial PDF (for example a 10-K you already have).
2. Submit the upload.
3. Expected: the file is accepted, a document record is created, and the app starts generating insights.
4. Expected: no error banner. The document appears in the document list.

## Test category 2: insights

### Feature 3: insight cards

Test steps:
1. After a document is processed, open its insights page.
2. Expected: structured insight cards appear across categories such as business summary, moat and edge, financial health, and management snapshot (7 categories in total).
3. Expected: each card contains real generated analysis text, not a placeholder or an error string.

### Feature 4: regenerate a single category

Test steps:
1. On the insights page, choose one category and trigger a regenerate for it.
2. Expected: only that category's card refreshes with new analysis. The other cards are unchanged.

## Test category 3: comparison

### Feature 5: compare two companies

Test steps:
1. Process at least two documents (two different companies).
2. Open the comparison page.
3. Expected: the page loads with a 200 response and shows the two companies side by side across the insight categories.
4. Expected: no server error. (An earlier build returned a 500 here from a blueprint name mismatch; the live app returns the comparison correctly.)

## Test category 4: export

### Feature 6: export insights to PDF

Test steps:
1. On a document's insights page, use the export to PDF action.
2. Expected: a PDF file downloads.
3. Expected: opening the file shows a valid PDF (starts with %PDF) containing the document's insights. The download is served as application/pdf.

## Test category 5: sharing

### Feature 7: create and open a shareable link

Test steps:
1. On a document, create a shareable link. Optionally set a name and an expiry in days (for example 7).
2. Expected: a link is returned with a unique token and an expiry date.
3. Open the shared link in a private or logged-out browser window.
4. Expected: the shared insights page renders for anyone with the link, without requiring login.
5. If the link is expired or deactivated, expected: an "link expired" page rather than the insights.

## Test category 6: admin cost dashboard

### Feature 8: API usage and budget

Test steps:
1. Navigate to the admin dashboard and log in with the admin username and password.
2. Expected: a view of API usage and monthly spend against the configured budget (default 20.0 USD).
3. Expected: usage rows accumulate as documents are processed.

## Error handling

Test steps:
1. Submit the upload form with no file.
2. Expected: a clear validation message, not a stack trace.
3. Search EDGAR for a nonsense string.
4. Expected: an empty result or a friendly "no matches" message, not an error page.

## Reporting issues

Use this format for anything that fails:

```
Feature: [feature name]
Test step: [the step that failed]
Expected: [what should happen]
Actual: [what happened]
Severity: high / medium / low
```

*Last updated: July 22, 2026*
*Coverage: the seven user-facing features verified during the Render migration, plus the admin dashboard.*
