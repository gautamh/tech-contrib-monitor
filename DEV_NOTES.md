# Developer Notes

This document provides a more detailed look at the architecture, design decisions, and development process for the Tech Contributions Monitor site.

## Architecture Overview

The project is designed as a static site with a data pipeline that runs on a schedule. This provides excellent performance, security, and zero hosting cost (via GitHub Pages) while ensuring the data remains up-to-date.

### Frontend

-   **Framework:** SvelteKit, chosen for its performance and simple, component-based architecture.
-   **Adapter:** Configured with `@sveltejs/adapter-static` to pre-render the entire site into static HTML, CSS, and JavaScript.
-   **Styling:** Uses the Tailwind CSS CDN for rapid prototyping. For a production-grade setup, this should be replaced with a full PostCSS build process as recommended by the official Tailwind docs.
-   **Data Consumption:** The frontend is deliberately kept simple. It fetches a single, pre-processed `formatted_contributions.json` file and is responsible only for rendering that data. All complex logic (grouping, summarization, etc.) is handled on the client-side within the Svelte component for maximum UI flexibility.

### Data Pipeline

The data pipeline is managed by a single GitHub Actions workflow defined in `.github/workflows/deploy.yml`. It runs on a daily schedule.

1.  **`scripts/fetch_data.py`:**
    -   **Responsibility:** Queries the live FEC API for two sets of raw data: individual contributions (Schedule A) and PAC expenditures (Schedule B).
    -   **Output:** Saves the raw, unmodified API results into two separate files: `static/data/contributions.json` and `static/data/pac_contributions.json`.
    -   **Design:** This script is designed to be robust against API flakiness. It includes a retry mechanism with delays to handle transient network errors and timeouts.

2.  **`scripts/format_data.py`:**
    -   **Responsibility:** Takes the raw JSON files from the fetch step and transforms them into a single, clean, and structured file optimized for the frontend.
    -   **Key Logic:**
        -   **Deduplication:** Removes duplicate records from the raw API data based on `transaction_id`.
        -   **Name Normalization:** Cleans and standardizes contributor names to group records from the same individual.
        -   **Filtering:** Filters PAC expenditures to isolate true contributions and removes negative-value transactions (refunds).
        -   **Clustering:** Groups individual contributions to detect "executive clusters" using a chaining logic where each contribution must be within 30 days of the previous one.
    -   **Output:** A single `static/data/formatted_contributions.json` file.

## Design Decisions & Debugging Journey

Several key decisions and bug fixes shaped the final implementation:

-   **Two-Step Data Pipeline:** Separating the `fetch` and `format` steps was a deliberate choice. It makes the pipeline more resilient and easier to debug. The raw data is always available, so the formatting script can be re-run locally without needing to hit the live API every time.

-   **Client-Side Summarization:** The decision to perform summarization (e.g., grouping PAC donations by month) on the client-side was made for flexibility. It allows the UI to be changed without requiring a change in the data processing scripts. The dataset is small enough that this does not pose a performance issue.

-   **Key Bugs & Fixes:**
    -   **Date Parsing:** A recurring issue was the browser failing to parse date strings in the format `YYYY-MM-DD`. This was definitively fixed by using `c.date.replace(/-/g, '/')` before passing the string to the `new Date()` constructor, which is a more robust method.
    -   **`$0` Summaries:** The summarization logic was initially producing `$0` totals. Debugging revealed that the raw FEC data contained negative values for refunds. The fix was to filter out these negative values in `format_data.py`.
    -   **Duplicate Entries:** The UI was showing what appeared to be duplicate summarized entries. This was traced back to duplicate records in the raw FEC API response. The fix was to add a `drop_duplicates()` step in `format_data.py`.
    -   **Styling & CSS:** The party-color styling initially failed to appear due to a misunderstanding of how the Tailwind CSS CDN works. Dynamic class generation (`text-{color}-600`) is not supported. This was fixed first by attempting a `class:` directive, and then definitively by using inline `style="color: ..."` attributes with `!important` to ensure the style was applied.

## Future Improvements

-   **Install Full Tailwind CSS:** Replace the CDN link with a proper PostCSS and `tailwind.config.js` setup for better performance and access to all of Tailwind's features.
-   **More Advanced Name Normalization:** The current name normalization is simple. A more advanced implementation could use a library like `thefuzz` to handle typos (e.g., "SMTIH" vs "SMITH").
-   **Error Handling:** The frontend could be improved to more gracefully display errors if the `formatted_contributions.json` file fails to load.
