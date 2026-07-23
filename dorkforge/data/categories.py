"""Built-in recon categories and CVE intel data."""

from typing import Any

RECON_CATEGORIES: dict[str, list[str]] = {
    "Exposed Panels": [
        'intitle:"login" intitle:"admin"', 'inurl:/admin/login.php',
        'inurl:/wp-admin', 'inurl:/administrator',
        'intitle:"phpMyAdmin"', 'intitle:"Webmin"',
        'intitle:"Kibana" "dashboard"', 'intitle:"Grafana"',
        'inurl:/swagger-ui.html', 'inurl:/graphql',
    ],
    "Directory Listing": [
        'intitle:index.of', 'intitle:index.of "parent directory"',
        'intitle:"Apache Tomcat"', 'intitle:"Directory Listing"',
    ],
    "Exposed Files": [
        'filetype:env DB_PASSWORD', 'filetype:sql "INSERT INTO" "password"',
        'filetype:log "password"', 'filetype:json "api_key"',
        'filetype:yaml "aws_access_key_id"', 'filetype:bak "password"',
        'filetype:cfg "password"', 'filetype:ini "password"',
    ],
    "Cloud & Infra": [
        'site:s3.amazonaws.com "password"',
        'site:blob.core.windows.net "password"',
        'site:cloudfront.net ".env"',
        'site:amazonaws.com "AccessKeyId"',
        'site:digitaloceanspaces.com "secret"',
    ],
    "Git & Code": [
        'inurl:/.git "index of"', 'inurl:/.svn "index of"',
        'site:github.com "password" "filename:env"',
        'site:gist.github.com "api_key"',
        'site:github.com "SECRET_KEY"',
    ],
    "Paste Leaks": [
        'site:pastebin.com "password"', 'site:pastebin.com "api_key"',
        'site:pastebin.com "ssh"', 'site:pastebin.com "aws"',
        'site:pastebin.com "PRIVATE KEY"',
    ],
    "CVE: wp2shell (WordPress RCE)": [
        'inurl:/wp-json/batch/v1',
        'inurl:?rest_route=/batch/v1',
        'inurl:/wp-json/wp/v2/users',
        'intitle:"index of" wp-content/plugins',
        'inurl:/wp-admin "generator" "6.9"',
        'inurl:/wp-admin "generator" "7.0"',
        'intitle:"WordPress" "generator" "6.9."',
        'intitle:"WordPress" "generator" "7.0."',
    ],
    "CVE: cPanel Auth Bypass": [
        'intitle:"cPanel" "login" inurl:2083',
        'intitle:"WHM" "login" inurl:2087',
        'inurl:cpanel "login" -site:cpanel.net',
        'intitle:"Web Host Manager" "login"',
    ],
    "CVE: PAN-OS RCE": [
        'intitle:"PAN-OS" "login"',
        'intitle:"GlobalProtect" "login"',
        'inurl:/php/phpinfo.php "PAN-OS"',
    ],
    "CVE: Ivanti EPMM": [
        'intitle:"Ivanti" "MobileIron" "login"',
        'inurl:/mifs/user/login',
        'intitle:"Ivanti EPMM"',
    ],
    "CVE: Nginx UI": [
        'intitle:"Nginx UI"',
        'intitle:"Nginx Web UI" "login"',
    ],
    "CVE: Exchange OWA": [
        'inurl:/owa/auth/logon.aspx',
        'intitle:"Outlook Web App" "sign in"',
        'inurl:/ecp/login.aspx',
    ],
}

RECON_ALL_DORKS: list[str] = []
for dorks in RECON_CATEGORIES.values():
    RECON_ALL_DORKS.extend(dorks)

CVE_INTEL: dict[str, dict[str, str]] = {
    "CVE-2026-63030 + CVE-2026-60137 (wp2shell)": {
        "cvss": "9.8 (Critical)",
        "type": "Pre-auth RCE chain (route-confusion + SQLi via WP_Query)",
        "product": "WordPress Core 6.9.0-6.9.4, 7.0.0-7.0.1",
        "status": "Actively exploited in the wild (Jul 2026). ~8.6M vulnerable instances.",
        "patch": "Update to 6.9.5 / 7.0.2",
        "detection": "POST /?rest_route=/batch/v1 with nested batch + SLEEP payload in author_exclude",
        "poc": "Public PoCs: 0xsha/wp2shell, Icex0/wp2shell-poc, sergiointel/wp2shell-poc",
        "nuclei": "CVE-2026-63030.yaml in nuclei-templates",
        "dorks": "inurl:/wp-json/batch/v1 | inurl:?rest_route=/batch/v1 | intitle:WordPress generator:6.9 or 7.0",
    },
    "CVE-2026-41940 (cPanel)": {
        "cvss": "9.1 (Critical)",
        "type": "Authentication Bypass → RCE",
        "product": "cPanel & WHM (multiple versions)",
        "status": "Actively exploited — ransomware + webshell deployment chain",
        "patch": "Update to latest cPanel version",
        "detection": "Access /cpanel without auth, attempt API calls",
        "poc": "Public PoC available on Exploit-DB",
        "dorks": "intitle:cPanel inurl:2083 | intitle:WHM inurl:2087",
    },
    "CVE-2026-0300 (PAN-OS)": {
        "cvss": "9.3 (Critical)",
        "type": "Out-of-bounds Write / Remote Code Execution",
        "product": "Palo Alto PAN-OS (multiple versions)",
        "status": "CISA KEV — actively exploited by state-sponsored actors",
        "patch": "Apply PAN-OS security hotfix from Palo Alto",
        "detection": "Check for PAN-OS login page, try known paths",
        "poc": "Public PoC available",
        "dorks": 'intitle:"PAN-OS" "login" | intitle:"GlobalProtect" "login"',
    },
    "CVE-2026-33032 (Nginx UI)": {
        "cvss": "9.8 (Critical)",
        "type": "Missing Authentication → Full Control",
        "product": "Nginx UI <= 2.3.3",
        "status": "Actively exploited since Apr 2026",
        "patch": "Update to Nginx UI 2.3.4+",
        "detection": "Access Nginx UI page — no login prompt = vulnerable",
        "poc": "Public PoC on GitHub (metarget/nginx-ui-CVE-2026-33032)",
        "dorks": 'intitle:"Nginx UI" | intitle:"Nginx Web UI" "login"',
    },
    "CVE-2026-20122/128/133 (Cisco SD-WAN)": {
        "cvss": "9.1-9.8 (Critical)",
        "type": "Authentication Bypass + Information Disclosure",
        "product": "Cisco Catalyst SD-WAN Manager",
        "status": "CISA Emergency Directive ED 26-03 — widespread scanning",
        "patch": "Apply Cisco security updates per advisory",
        "detection": "Check /api/ or /vmanage/ paths",
        "poc": "Public PoCs available on GitHub",
        "dorks": 'intitle:"Catalyst SD-WAN" "login" | intitle:"Cisco SD-WAN"',
    },
    "CVE-2026-6973 (Ivanti EPMM)": {
        "cvss": "9.8 (Critical)",
        "type": "Authentication Bypass → RCE",
        "product": "Ivanti EPMM / MobileIron Core",
        "status": "CISA KEV — actively exploited in enterprise MDM deployments",
        "patch": "Apply Ivanti EPMM security patch",
        "detection": "Access /mifs/user/login, attempt auth bypass",
        "poc": "Public PoC available",
        "dorks": 'intitle:"Ivanti" "MobileIron" | inurl:/mifs/user/login',
    },
}


def get_cve_by_name(name: str) -> dict[str, str]:
    for cve_name, info in CVE_INTEL.items():
        if cve_name.startswith(name) or name in cve_name:
            return info
    return {}


def get_cve_dorks(name: str) -> list[str]:
    for cve_name, dorks in RECON_CATEGORIES.items():
        if name in cve_name.lower():
            return dorks
    return []
