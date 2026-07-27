# DorkForge

> A desktop and command-line workspace for authorized search-based reconnaissance.

DorkForge runs search queries, consolidates matching URLs, and optionally enriches
results with basic HTTP, technology, endpoint, and form information. It is designed
to help security teams triage assets they are authorized to assess.

## Features

- Run individual queries, a file of queries, or built-in recon categories
- Limit results to approved domains with a scope filter
- Deduplicate search results across queries
- Enrich discovered URLs with status, detected technologies, endpoints, and forms
- Export results as JSON, CSV, newline-delimited URLs, or an HTML triage report
- Send result summaries to Discord or Slack webhooks
- Use a PyQt6 desktop interface for queue management and result review
- Review the bundled CVE-intelligence entries from the CLI or GUI

## Responsible use

Use DorkForge only against systems you own or have explicit permission to test.
Search results can expose sensitive material; treat output as confidential, keep
collection proportional to the engagement scope, and follow the terms and policies
of the search provider and target organization. The `--scope` option is strongly
recommended for every assessment.

## Requirements

- Python 3.10 or newer
- A supported local browser environment for `cloakbrowser`
- Network access appropriate to your authorized engagement

## Installation

Clone the repository and install the package in an isolated virtual environment:

```bash
git clone https://github.com/0x1337/dorkforge.git
cd dorkforge

python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

You can also use the provided Make targets:

```bash
make install
```

## Quick start

List the available query categories, then run a scoped query and export an HTML
report:

```bash
dorkforge categories

dorkforge search 'site:example.com inurl:admin' \
  --scope example.com \
  --pages 2 \
  --enrich \
  --export html \
  --output assessment-results
```

The example writes `assessment-results.html` in the current directory.

## Command-line usage

```text
dorkforge [--verbose] COMMAND [OPTIONS]

Commands:
  search       Run one or more search queries
  categories   List bundled recon categories and their queries
  cve          List bundled CVE-intelligence entries
```

### Search inputs

```bash
# One query
dorkforge search 'site:example.com filetype:pdf'

# Multiple query arguments
dorkforge search 'site:example.com inurl:login' 'site:example.com inurl:admin'

# Load one query per line; lines beginning with # are ignored
dorkforge search --file queries.txt --scope example.com

# Run a named built-in category (list names with `dorkforge categories`)
dorkforge search --category 'Exposed Files' --scope example.com

# Run every bundled category, with a conservative page and delay configuration
dorkforge search --all-categories --scope example.com --pages 1 --delay 5
```

### Filtering, enrichment, and exports

```bash
dorkforge search 'site:example.com inurl:api' \
  --scope example.com,portal.example.com \
  --pages 3 \
  --delay 4 \
  --proxy http://127.0.0.1:8080 \
  --enrich \
  --export csv \
  --output scoped-api-results
```

| Option | Purpose |
| --- | --- |
| `--scope`, `-s` | Comma-separated domains permitted in results |
| `--pages`, `-p` | Search-result pages per query (default: `2`) |
| `--delay`, `-d` | Delay between pages in seconds (default: `4`) |
| `--enrich` | Collect status, technology, endpoint, and form details |
| `--export` | Output format: `json`, `csv`, `urls`, or `html` |
| `--output`, `-o` | Destination path without the export extension |
| `--headless` / `--no-headless` | Run the browser with or without a visible window |
| `--proxy` | Proxy URL for browser traffic |
| `--verbose`, `-v` | Enable diagnostic logging |

## Desktop application

Launch the graphical workspace with either command:

```bash
dorkforge-gui
# or
python -m dorkforge gui
```

The GUI provides a query queue, category presets, live result filtering, export
controls, CVE-intelligence review, and runtime settings for pages, delay, browser
mode, proxy, and webhooks.

## Notifications

Pass a webhook per run or configure it through the environment:

```bash
export DORKFORGE_DISCORD_WEBHOOK='https://discord.com/api/webhooks/...'
export DORKFORGE_SLACK_WEBHOOK='https://hooks.slack.com/services/...'

dorkforge search 'site:example.com inurl:login' --scope example.com --export json
```

Webhook URLs may also be supplied with `--discord-webhook` and `--slack-webhook`.
Keep these values out of source control and shared shell histories.

## Development

```bash
make test
make lint
```

Equivalent commands:

```bash
pytest tests/ -v -x
ruff check dorkforge/ tests/
ruff format --check dorkforge/ tests/
```

## Project layout

```text
dorkforge/
├── cli.py          # Click command-line interface
├── data/           # Query categories and CVE-intelligence data
├── engine/         # Browser search and result enrichment
├── exporters/      # JSON, CSV, URL, and HTML report exporters
├── notifiers/      # Discord and Slack webhook integrations
└── ui/             # PyQt6 desktop application
tests/              # Automated test suite
```

## Support

For installation help or feature requests, open an issue in the project repository.

## License

This project is published under the MIT license, as declared in `pyproject.toml`.
