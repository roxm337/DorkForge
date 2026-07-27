"""DorkForge CLI — Google dorking & CVE hunting from the terminal."""

from __future__ import annotations

import logging
import sys
import time
from typing import Optional

import click

from dorkforge import __version__
from dorkforge.data.categories import RECON_CATEGORIES, RECON_ALL_DORKS, CVE_INTEL
from dorkforge.engine.dorker import DorkEngine
from dorkforge.engine.enrich import Enricher
from dorkforge.engine.prober import ProbeEngine
from dorkforge.exporters import EXPORTER_MAP
from dorkforge.models.result import DorkResult

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def progress_cb(current: int, total: int, msg: str):
    click.echo(f"  [{current}/{total}] {msg}", err=True)


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="DorkForge")
@click.option("--verbose", "-v", is_flag=True, help="Verbose debug output")
@click.pass_context
def cli(ctx: click.Context, verbose: bool):
    """DorkForge — Google dorking & CVE hunting platform.

    Search Google with dorks, enrich results, export in multiple formats.
    """
    setup_logging(verbose)
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.argument("dorks", nargs=-1)
@click.option("--file", "-f", type=click.Path(exists=True), help="File with dorks (one per line)")
@click.option("--category", "-c", multiple=True, help= f"Category name (choices: {', '.join(RECON_CATEGORIES.keys())})")
@click.option("--all-categories", is_flag=True, help="Use all built-in recon categories")
@click.option("--pages", "-p", default=2, show_default=True, help="Pages per dork")
@click.option("--delay", "-d", default=4, show_default=True, help="Delay between pages (seconds)")
@click.option("--headless/--no-headless", default=True, help="Run browser headless")
@click.option("--proxy", help="Proxy URL (e.g. http://127.0.0.1:8080)")
@click.option("--scope", "-s", help="Comma-separated domains to scope results")
@click.option("--enrich", is_flag=True, help="Deep enrich (status, tech, endpoints, forms)")
@click.option("--probe", is_flag=True, help="Probe results with CloakBrowser for CVE-specific vuln endpoints")
@click.option("--export", "export_fmt", type=click.Choice(["json", "csv", "urls", "html"]), help="Export results")
@click.option("--output", "-o", default="dork_results", help="Output file path (without extension)")
@click.option("--discord-webhook", envvar="DORKFORGE_DISCORD_WEBHOOK", help="Discord webhook URL")
@click.option("--slack-webhook", envvar="DORKFORGE_SLACK_WEBHOOK", help="Slack webhook URL")
def search(
    dorks: tuple[str, ...],
    file: Optional[str],
    category: tuple[str, ...],
    all_categories: bool,
    pages: int,
    delay: int,
    headless: bool,
    proxy: Optional[str],
    scope: Optional[str],
    enrich: bool,
    probe: bool,
    export_fmt: Optional[str],
    output: str,
    discord_webhook: Optional[str],
    slack_webhook: Optional[str],
):
    """Run dork queries against Google."""
    dork_list: list[str] = list(dorks)

    if file:
        with open(file) as f:
            dork_list.extend(line.strip() for line in f if line.strip() and not line.startswith("#"))

    if all_categories:
        dork_list.extend(RECON_ALL_DORKS)

    for cat in category:
        if cat in RECON_CATEGORIES:
            dork_list.extend(RECON_CATEGORIES[cat])
        else:
            click.echo(f"Unknown category: {cat}", err=True)
            sys.exit(1)

    if not dork_list:
        click.echo("No dorks specified. Provide dorks, a file, or a category.", err=True)
        sys.exit(1)

    scope_domains = [s.strip() for s in scope.split(",")] if scope else []

    click.echo(f"DorkForge v{__version__}")
    click.echo(f"Dorks: {len(dork_list)} | Pages/dork: {pages} | Delay: {delay}s")
    if scope:
        click.echo(f"Scope: {', '.join(scope_domains)}")
    click.echo("")

    engine = DorkEngine(
        headless=headless,
        pages=pages,
        delay=delay,
        proxy=proxy,
        scope_domains=scope_domains,
    )

    all_results: list[DorkResult] = []
    for dork in dork_list:
        start = time.time()
        try:
            results = engine.search(dork, progress_cb=progress_cb)
            elapsed = time.time() - start
            click.echo(f"  → {len(results)} results ({elapsed:.1f}s)\n")
            all_results.extend(results)
        except Exception as e:
            click.echo(f"  ✗ Error: {e}\n", err=True)

    click.echo(f"\nTotal unique results: {len(all_results)}")

    if enrich:
        click.echo("Enriching...")
        enricher = Enricher()
        all_results = enricher.enrich(all_results)

    if probe and all_results:
        click.echo("Probing targets with CloakBrowser (CVE-specific endpoints)...")
        click.echo("  This bypasses Cloudflare/WAF to check actual vuln reachability.\n")
        prober = ProbeEngine(headless=headless, proxy=proxy)
        probe_results = prober.probe(all_results, progress_cb=progress_cb)

        interesting = [p for p in probe_results if p.is_interesting]
        click.echo(f"\nProbe complete — {len(probe_results)} checks, {len(interesting)} interesting:\n")
        for p in interesting[:30]:
            click.echo(f"  [{p.verdict}] {p.cve} — {p.url}")
        if len(interesting) > 30:
            click.echo(f"  ... and {len(interesting) - 30} more")

        # Save probe results
        probe_path = f"{output}_probes.txt"
        with open(probe_path, "w") as f:
            for p in interesting:
                f.write(f"[{p.verdict}] {p.cve} | {p.url}\n")
        click.echo(f"Probe results saved to {probe_path}")

    if export_fmt:
        exporter_cls = EXPORTER_MAP.get(export_fmt)
        if exporter_cls:
            path = f"{output}.{exporter_cls.extension}"
            exporter_cls().export(all_results, path)
            click.echo(f"Exported to {path}")

    if discord_webhook:
        from dorkforge.notifiers.discord import DiscordNotifier
        DiscordNotifier(discord_webhook).send(all_results)
        click.echo("Sent to Discord webhook")

    if slack_webhook:
        from dorkforge.notifiers.slack import SlackNotifier
        SlackNotifier(slack_webhook).send(all_results)
        click.echo("Sent to Slack webhook")

    return all_results


@cli.command()
def categories():
    """List all built-in recon categories."""
    click.echo(f"DorkForge v{__version__} — Recon Categories\n")
    for name, dorks in RECON_CATEGORIES.items():
        click.echo(f"  {name}")
        for d in dorks:
            click.echo(f"    - {d}")
        click.echo("")


@cli.command()
def cve():
    """List active CVE intel with dorks."""
    click.echo(f"DorkForge v{__version__} — CVE Intel\n")
    for cve_name, info in CVE_INTEL.items():
        click.echo(f"  {cve_name}")
        click.echo(f"    CVSS:      {info.get('cvss', '?')}")
        click.echo(f"    Type:      {info.get('type', '?')}")
        click.echo(f"    Product:   {info.get('product', '?')}")
        click.echo(f"    Status:    {info.get('status', '?')}")
        click.echo(f"    Detection: {info.get('detection', '?')}")
        click.echo(f"    PoC:       {info.get('poc', '?')}")
        click.echo(f"    Dorks:     {info.get('dorks', '?')}")
        click.echo("")


if __name__ == "__main__":
    cli()
