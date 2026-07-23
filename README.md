# DorkForge

Google Dorking & CVE Hunting Platform.

Search Google with dorks via CloakBrowser (stealth, undetectable), enrich results with tech detection and endpoint discovery, export in multiple formats, and notify via Discord/Slack.

## Quick Start

```bash
pip install -r requirements.txt
pip install -e .

# CLI
dorkforge search --category "CVE: wp2shell (WordPress RCE)" --enrich --export html

# GUI
dorkforge-gui
```

## CLI Usage

```bash
# Single dork
dorkforge search 'inurl:/wp-admin' --pages 3

# Category
dorkforge search --category "Exposed Files" --enrich --export json

# Multiple categories
dorkforge search --category "CVE: wp2shell (WordPress RCE)" -c "CVE: PAN-OS RCE"

# From file
dorkforge search -f my_dorks.txt --enrich --export html

# Scope filter
dorkforge search --category "Exposed Panels" --scope target.com,sub.target.com

# With proxy
dorkforge search --category "CVE: cPanel Auth Bypass" --proxy http://127.0.0.1:8080

# List categories
dorkforge categories

# List CVE intel
dorkforge cve
```

## CVE Intel Mode

Built-in dorks for actively exploited CVEs:

| CVE | CVSS | Type |
|-----|------|------|
| CVE-2026-63030/60137 (wp2shell) | 9.8 | Pre-auth RCE in WordPress |
| CVE-2026-41940 (cPanel) | 9.1 | Auth bypass → RCE |
| CVE-2026-0300 (PAN-OS) | 9.3 | OOB Write / RCE |
| CVE-2026-33032 (Nginx UI) | 9.8 | Missing auth |
| CVE-2026-20122/128/133 (Cisco SD-WAN) | 9.1-9.8 | Auth bypass |
| CVE-2026-6973 (Ivanti EPMM) | 9.8 | Auth bypass |

## GUI

```bash
dorkforge-gui
```

Features:
- Dork queue with category presets
- Results table with live filtering and color-coded status
- Deep enrichment (tech detection, JS endpoints, forms)
- Export: JSON, CSV, URLs, HTML triage report
- CVE Intel panel with one-click dork copy
- Settings: pages, delay, headless, proxy, webhooks

## Environment Variables

- `DORKFORGE_DISCORD_WEBHOOK` — Discord webhook URL
- `DORKFORGE_SLACK_WEBHOOK` — Slack webhook URL
