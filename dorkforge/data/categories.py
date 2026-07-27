"""Built-in recon categories and CVE intel data — updated July 2026.

Noise-reduced dorks: each CVE category uses anti-blog/anti-news exclusion
to avoid the security-journalism pollution that follows every major disclosure.
"""

from typing import Any

# Noise exclusion — appended to every CVE dork to filter out news/doc noise
_NX = " -blog -news -github -CVE -vulnerability -security -patch -advisory -exploit -fix -update -release -announcement -warning -disclosure -PoC -poc -trendmicro -bleepingcomputer -thehackernews -securityaffairs -helpnetsecurity -securityweek -rescana -triskelelabs"

_NX_LIGHT = " -blog -news -github"

RECON_CATEGORIES: dict[str, list[str]] = {
    "Exposed Panels": [
        'intitle:"login" intitle:"admin"' + _NX_LIGHT,
        'inurl:/admin/login.php',
        'inurl:/wp-admin',
        'inurl:/administrator',
        'intitle:"phpMyAdmin"',
        'intitle:"Webmin"',
        'intitle:"Kibana" "dashboard"',
        'intitle:"Grafana"',
        'inurl:/swagger-ui.html',
        'inurl:/graphql',
    ],
    "Directory Listing": [
        'intitle:index.of',
        'intitle:index.of "parent directory"',
        'intitle:"Apache Tomcat"',
        'intitle:"Directory Listing"',
    ],
    "Exposed Files": [
        'filetype:env DB_PASSWORD' + _NX_LIGHT,
        'filetype:sql "INSERT INTO" "password"',
        'filetype:log "password"',
        'filetype:json "api_key"',
        'filetype:yaml "aws_access_key_id"',
        'filetype:bak "password"',
        'filetype:cfg "password"',
        'filetype:ini "password"',
    ],
    "Cloud & Infra": [
        'site:s3.amazonaws.com "password"' + _NX_LIGHT,
        'site:blob.core.windows.net "password"',
        'site:cloudfront.net ".env"',
        'site:amazonaws.com "AccessKeyId"',
        'site:digitaloceanspaces.com "secret"',
    ],
    "Git & Code": [
        'inurl:/.git "index of"' + _NX_LIGHT,
        'inurl:/.svn "index of"',
        'site:github.com "password" "filename:env"',
        'site:gist.github.com "api_key"',
        'site:github.com "SECRET_KEY"',
    ],
    "Paste Leaks": [
        'site:pastebin.com "password"' + _NX_LIGHT,
        'site:pastebin.com "api_key"',
        'site:pastebin.com "ssh"',
        'site:pastebin.com "aws"',
        'site:pastebin.com "PRIVATE KEY"',
    ],
    "CVE: wp2shell (WordPress RCE)": [
        f'inurl:/wp-json/batch/v1 "generator" "6.9"{_NX}',
        f'inurl:/wp-json/batch/v1 "generator" "7.0"{_NX}',
        f'inurl:/wp-json/batch/v1 intitle:"index of"{_NX}',
        f'inurl:?rest_route=/batch/v1 inurl:/{_NX}',
        f'inurl:/wp-json/wp/v2/users intitle:"index of"{_NX}',
        f'intitle:"index of" wp-content/plugins -example{_NX}',
        f'inurl:/wp-admin "generator" "6.9" intitle:"index of"{_NX}',
        f'inurl:/wp-admin "generator" "7.0" intitle:"index of"{_NX}',
    ],
    "CVE: SharePoint RCE (50522/58644)": [
        f'inurl:/_trust/default.aspx intitle:"SharePoint"{_NX}',
        f'inurl:/_layouts/15/ intitle:"SharePoint" inurl:com{_NX}',
        f'inurl:/sites/ "Sign In" "SharePoint"{_NX}',
        f'intitle:"SharePoint" "Sign In" inurl:com{_NX}',
        f'intitle:"Windows SharePoint Services" inurl:com{_NX}',
        f'inurl:/_vti_bin/ intitle:"SharePoint"{_NX}',
        f'inurl:/layouts intitle:"SharePoint" inurl:443{_NX}',
    ],
    "CVE: ServiceNow RCE (6875)": [
        f'intitle:"ServiceNow" "sign in" "user name"{_NX}',
        f'inurl:/login.do intitle:"ServiceNow"{_NX}',
        f'inurl:/navpage.do intitle:"ServiceNow"{_NX}',
        f'inurl:/now/nav/ui/ intitle:"ServiceNow"{_NX}',
        f'inurl:/assessment_thanks.do inurl:servicenow{_NX}',
        f'intitle:"servicenow" "forgot password"{_NX}',
    ],
    "CVE: Grav CMS RCE (65008/65608)": [
        f'intitle:"Grav" "Admin" "Login"{_NX}',
        f'inurl:/admin intitle:"Grav"{_NX}',
        f'intitle:"Grav CMS" "powered by"{_NX}',
        f'intitle:"Grav" "Log in" inurl:admin{_NX}',
    ],
    "CVE: DbGate RCE (47668)": [
        f'intitle:"DbGate" inurl:8080{_NX}',
        f'intitle:"DbGate" "database"{_NX}',
        f'inurl:/runners/start intitle:"DbGate"{_NX}',
    ],
    "CVE: NGINX Rift (42533/42945)": [
        f'intitle:"Welcome to nginx" inurl:80{_NX}',
        f'intitle:"Welcome to nginx" "on" "CentOS"{_NX}',
        f'intitle:"Welcome to nginx" "Debian"{_NX}',
        f'intitle:"Welcome to nginx" "Ubuntu"{_NX}',
        f'intitle:"nginx" "403 Forbidden"{_NX}',
        f'intitle:"nginx" "401 Authorization Required"{_NX}',
    ],
    "CVE: Laravel-Mediable RCE (49972)": [
        f'inurl:/media/upload "laravel"{_NX}',
        f'intitle:"Laravel" "powered by" inurl:/media{_NX}',
        f'inurl:/media "laravel" "storage"{_NX}',
    ],
    "CVE: CodeIgniter Upload Bypass (48062)": [
        f'intitle:"CodeIgniter" "Welcome"{_NX}',
        f'inurl:/public/uploads "CodeIgniter"{_NX}',
        f'intitle:"CodeIgniter" "CI_VERSION" inurl:404{_NX}',
    ],
    "CVE: PAN-OS RCE (0300)": [
        f'intitle:"PAN-OS" "login"{_NX}',
        f'intitle:"GlobalProtect" "login"{_NX}',
        f'inurl:/php/phpinfo.php intitle:"PAN-OS"{_NX}',
    ],
    "CVE: cPanel Auth Bypass": [
        f'intitle:"cPanel" "login" inurl:2083{_NX}',
        f'intitle:"WHM" "login" inurl:2087{_NX}',
        f'inurl:cpanel "login" -site:cpanel.net{_NX}',
        f'intitle:"Web Host Manager" "login"{_NX}',
    ],
    "CVE: Ivanti EPMM RCE": [
        f'intitle:"Ivanti" "MobileIron" "login"{_NX}',
        f'inurl:/mifs/user/login intitle:"Ivanti"{_NX}',
        f'intitle:"Ivanti EPMM" "login"{_NX}',
    ],
    "CVE: Nginx UI Missing Auth": [
        f'intitle:"Nginx UI"{_NX}',
        f'intitle:"Nginx Web UI" "login"{_NX}',
    ],
    "CVE: Exchange OWA": [
        f'inurl:/owa/auth/logon.aspx intitle:"Outlook"{_NX}',
        f'intitle:"Outlook Web App" "sign in"{_NX}',
        f'inurl:/ecp/login.aspx intitle:"Exchange"{_NX}',
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
        "status": "ACTIVELY EXPLOITED — CISA KEV. ~8.6M vulnerable. 69+ public PoCs on GitHub.",
        "patch": "Update to 6.9.5 / 7.0.2",
        "detection": "POST /?rest_route=/batch/v1 with nested batch + SLEEP in author_exclude",
        "poc": "GitHub: 0xsha/wp2shell, Icex0/wp2shell-poc, sergiointel/wp2shell-poc",
        "nuclei": "CVE-2026-63030.yaml in nuclei-templates",
        "dorks": "inurl:/wp-json/batch/v1 with version generator tag + noise exclusion",
    },
    "CVE-2026-50522 (SharePoint Deserialization RCE)": {
        "cvss": "9.8 (Critical)",
        "type": "Unauthenticated Deserialization RCE (BinaryFormatter)",
        "product": "Microsoft SharePoint Server (on-prem, all versions)",
        "status": "ACTIVELY EXPLOITED — CISA KEV added Jul 22. Machine key theft in wild.",
        "patch": "Apply July 2026 Patch Tuesday (16.0.19725.20434+)",
        "detection": "POST /_trust/default.aspx with crafted SecurityContextToken cookie",
        "poc": "GitHub: 4minx/CVE-2026-50522. Pwn2Own Berlin. ysoserial BinaryFormatter gadget.",
        "nuclei": "CVE-2026-50522.yaml in nuclei-templates",
        "dorks": "inurl:/_trust/default.aspx intitle:SharePoint — excludes docs/news",
    },
    "CVE-2026-58644 (SharePoint Pwn2Own RCE)": {
        "cvss": "9.8 (Critical)",
        "type": "Unauthenticated RCE (paired with 50522)",
        "product": "Microsoft SharePoint Server (on-prem)",
        "status": "ACTIVELY EXPLOITED — CISA KEV. Paired Pwn2Own bug.",
        "patch": "Apply July 2026 Patch Tuesday",
        "detection": "Same /_trust/ deserialization vector as 50522",
        "poc": "Pwn2Own Berlin 2026. Exploit integrated into offensive frameworks.",
        "dorks": "inurl:/_trust/default.aspx intitle:SharePoint",
    },
    "CVE-2026-6875 (ServiceNow Pre-Auth RCE)": {
        "cvss": "9.5 (Critical)",
        "type": "Pre-auth Sandbox Escape RCE (JS injection → Java RCE)",
        "product": "ServiceNow AI Platform (Brazil, Australia, Zurich, Yokohama)",
        "status": "ACTIVELY EXPLOITED — Defused confirmed Jul 18. Two distinct gadget chains.",
        "patch": "KB3137947 — Apply Guarded Script update for self-hosted instances.",
        "detection": "POST /assessment_thanks.do with sysparm_assessable_type=javascript:...",
        "poc": "GitHub: tc4dy/CVE-2026-6875-PoC-Exploit. Searchlight Cyber disclosure.",
        "nuclei": "CVE-2026-6875.yaml in nuclei-templates",
        "dorks": "intitle:ServiceNow sign in user name — excludes service-now docs",
    },
    "CVE-2026-65008 (Grav CMS RCE)": {
        "cvss": "9.8 (Critical)",
        "type": "Authenticated RCE via call_user_func_array() in Blueprint::dynamicData()",
        "product": "Grav CMS 2.0.4 (fixed in 2.0.7)",
        "status": "PoC published. Bypass found 2 days later as CVE-2026-65608.",
        "patch": "Update to Grav 2.0.7+",
        "detection": "admin.pages permission → plant Class::method callable in frontmatter",
        "poc": "VulnCheck disclosure. Bypass via FlexDirectory in Grav < 2.0.9.",
        "dorks": "intitle:Grav Admin Login — excludes docs/getgrav",
    },
    "CVE-2026-65608 (Grav FlexDirectory RCE bypass)": {
        "cvss": "9.8 (Critical)",
        "type": "RCE via FlexDirectory — bypasses CVE-2026-65008 patch",
        "product": "Grav CMS 1.7.0 to 2.0.8 (fixed in 2.0.9)",
        "status": "PoC. Hits FlexDirectory instead of Blueprint to bypass 2.0.7 fix.",
        "patch": "Update to Grav 2.0.9+",
        "detection": "FlexDirectory::dynamicDataField() → call_user_func_array() via data-*@: directives",
        "poc": "Published Jul 23. No method allowlist on any Flex directory.",
        "dorks": "intitle:Grav Admin Login (same dorks as 65008)",
    },
    "CVE-2026-47668 (DbGate RCE)": {
        "cvss": "10.0 (CRITICAL — max score)",
        "type": "Unauthenticated RCE via JSON script runner",
        "product": "DbGate <= 7.1.8 (cross-platform DB manager)",
        "status": "CVSS 10.0. No auth required. Public exploit on GitHub.",
        "patch": "Update to DbGate 7.1.9+",
        "detection": "POST /runners/start with JSON assign → functionName → JS concat → Node.js child_process",
        "poc": "GitHub: Nxploited/CVE-2026-47668",
        "dorks": "intitle:DbGate inurl:8080 — excludes docs/github",
    },
    "CVE-2026-42533 + CVE-2026-42945 (NGINX Rift)": {
        "cvss": "9.2 (Critical)",
        "type": "Heap buffer overflow → DoS / RCE in script engine",
        "product": "NGINX 0.9.6 through 1.31.2 (all Plus/Ingress/Gateway/F5)",
        "status": "Patched Jul 2026. PoC expected in ~21 days. Shodan shows millions of exposed instances.",
        "patch": "Update to NGINX 1.30.4 / 1.31.3 / Plus 37.0.3.1",
        "detection": "Crafted HTTP targeting regex-based map with string expression referencing captures",
        "poc": "cyberstan researcher. PoC planned 21 days post-patch.",
        "dorks": 'intitle:"Welcome to nginx" inurl:80 — use Shodan: http.title:"Welcome to nginx"',
    },
    "CVE-2026-49972 (Laravel-Mediable RCE)": {
        "cvss": "9.8 (Critical)",
        "type": "Unauthenticated file upload RCE via double extension bypass",
        "product": "Laravel-Mediable < 7.0.0",
        "status": "CVSS 9.8. Shell.php.jpg bypass — Apache/nginx executes as PHP.",
        "patch": "Update to Laravel-Mediable 7.0.0+",
        "detection": "PATHINFO_FILENAME extracts inner .php from shell.php.jpg. All checks pass on .jpg.",
        "poc": "VulnCheck advisory. PoC available.",
        "dorks": "inurl:/media/upload laravel — excludes docs/github",
    },
    "CVE-2026-48062 (CodeIgniter Upload Bypass)": {
        "cvss": "9.8 (Critical)",
        "type": "File extension validation bypass via MIME mismatch",
        "product": "CodeIgniter 4 < 4.7.3",
        "status": "Fixed in 4.7.3. ext_in rule checks MIME extension not client filename.",
        "patch": "Update to CodeIgniter 4.7.3+",
        "detection": "ext_in[gif] passes shell.php containing GIF bytes. Saved as .php.",
        "poc": "GHSA-2gr4-ppc7-7mhx. Public disclosure.",
        "dorks": 'intitle:"CodeIgniter" "Welcome" — excludes docs/github',
    },
    "CVE-2026-41940 (cPanel Auth Bypass)": {
        "cvss": "9.1 (Critical)",
        "type": "Authentication Bypass → RCE",
        "product": "cPanel & WHM (multiple versions)",
        "status": "Actively exploited — ransomware + webshell deployment chain",
        "patch": "Update to latest cPanel version",
        "detection": "Access /cpanel without auth, try API calls",
        "poc": "Public PoC on Exploit-DB",
        "dorks": "intitle:cPanel inurl:2083 — excludes docs/cpanel.net",
    },
    "CVE-2026-0300 (PAN-OS RCE)": {
        "cvss": "9.3 (Critical)",
        "type": "Out-of-bounds Write / Remote Code Execution",
        "product": "Palo Alto PAN-OS (multiple versions)",
        "status": "CISA KEV — exploited by state-sponsored actors",
        "patch": "Apply PAN-OS security hotfix",
        "detection": "Check for PAN-OS login page, try known exploit paths",
        "poc": "Public PoC available",
        "dorks": 'intitle:"PAN-OS" "login" — excludes docs/paloaltonetworks',
    },
    "CVE-2026-33032 (Nginx UI)": {
        "cvss": "9.8 (Critical)",
        "type": "Missing Authentication → Full Server Control",
        "product": "Nginx UI <= 2.3.3",
        "status": "Actively exploited since Apr 2026",
        "patch": "Update to Nginx UI 2.3.4+",
        "detection": "Access Nginx UI — no login prompt = vulnerable",
        "poc": "GitHub: metarget/nginx-ui-CVE-2026-33032",
        "dorks": 'intitle:"Nginx UI" — excludes docs/github',
    },
    "CVE-2026-6973 (Ivanti EPMM RCE)": {
        "cvss": "9.8 (Critical)",
        "type": "Authentication Bypass → RCE",
        "product": "Ivanti EPMM / MobileIron Core",
        "status": "CISA KEV — actively exploited in enterprise MDM",
        "patch": "Apply Ivanti EPMM security patch",
        "detection": "Access /mifs/user/login, attempt auth bypass",
        "poc": "Public PoC available",
        "dorks": 'intitle:"Ivanti" "MobileIron" "login" — excludes docs/ivanti',
    },
    "CVE-2026-20122/128/133 (Cisco SD-WAN)": {
        "cvss": "9.1-9.8 (Critical)",
        "type": "Multiple Auth Bypass + Info Disclosure",
        "product": "Cisco Catalyst SD-WAN Manager",
        "status": "CISA Emergency Directive ED 26-03 — widespread scanning",
        "patch": "Apply Cisco security updates per advisory",
        "detection": "Check /api/ or /vmanage/ paths for unauthenticated access",
        "poc": "Public PoCs on GitHub",
        "dorks": 'intitle:"Catalyst SD-WAN" "login" — excludes docs/cisco',
    },
}


def get_cve_by_name(name: str) -> dict[str, str]:
    for cve_name, info in CVE_INTEL.items():
        if cve_name.startswith(name) or name in cve_name:
            return info
    return {}


def get_cve_dorks(name: str) -> list[str]:
    for cat_name, dorks in RECON_CATEGORIES.items():
        if name.lower() in cat_name.lower():
            return dorks
    return []
