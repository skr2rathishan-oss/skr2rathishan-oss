import json
import os
import urllib.request
from datetime import datetime, timezone, timedelta


USERNAME = os.environ.get("GITHUB_USERNAME", "skr2rathishan-oss")
TOKEN = os.environ.get("GITHUB_TOKEN")
OUTPUT_DIR = "assets"

QUERY = """
query($login: String!) {
  user(login: $login) {
    name
    login
    followers { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC) {
      totalCount
      nodes {
        stargazerCount
        primaryLanguage { name }
      }
    }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
    }
  }
}
"""

LANGUAGE_COLORS = {
    "C": "#A8B9CC",
    "C#": "#9B4F96",
    "C++": "#659AD2",
    "CSS": "#663399",
    "Dart": "#00B4AB",
    "Go": "#00ADD8",
    "HTML": "#E34F26",
    "Java": "#ED8B00",
    "JavaScript": "#F7DF1E",
    "Jupyter Notebook": "#F37626",
    "Kotlin": "#A97BFF",
    "PHP": "#777BB4",
    "Python": "#3776AB",
    "Ruby": "#CC342D",
    "Rust": "#DEA584",
    "Shell": "#89E051",
    "Swift": "#F05138",
    "TypeScript": "#3178C6",
    "Vue": "#42B883",
}


def fetch_user():
    if not TOKEN:
        raise RuntimeError("GITHUB_TOKEN is required to fetch live GitHub statistics.")

    body = json.dumps({
        "query": QUERY,
        "variables": {"login": USERNAME},
    }).encode()

    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "skr2rathishan-oss-GitHub-Profile-Stats",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode())

    if result.get("errors"):
        raise RuntimeError(json.dumps(result["errors"], indent=2))

    return result["data"]["user"]


def calculate_streaks(days):
    counts = {day["date"]: day["contributionCount"] for day in days}

    longest = current_run = 0
    for date in sorted(counts):
        if counts[date] > 0:
            current_run += 1
            longest = max(longest, current_run)
        else:
            current_run = 0

    today = datetime.now(timezone.utc).date()
    cursor = today

    if counts.get(str(cursor), 0) == 0:
        cursor -= timedelta(days=1)

    current = 0
    while counts.get(str(cursor), 0) > 0:
        current += 1
        cursor -= timedelta(days=1)

    return current, longest


def streak_details(days):
    ordered = sorted(days, key=lambda day: day["date"])
    active_runs = []
    run_start = None
    run_end = None

    for day in ordered:
        current_date = datetime.fromisoformat(day["date"]).date()
        if day["contributionCount"] > 0:
            if run_start is None:
                run_start = current_date
            run_end = current_date
        elif run_start is not None:
            active_runs.append((run_start, run_end))
            run_start = run_end = None

    if run_start is not None:
        active_runs.append((run_start, run_end))

    longest_start = longest_end = None
    if active_runs:
        longest_start, longest_end = max(
            active_runs,
            key=lambda run: (run[1] - run[0]).days,
        )

    today = datetime.now(timezone.utc).date()
    recent_cutoff = today - timedelta(days=1)
    current_start = current_end = None
    for start, end in reversed(active_runs):
        if end >= recent_cutoff:
            current_start, current_end = start, end
        break

    last_active = active_runs[-1][1] if active_runs else None
    return {
        "period_start": datetime.fromisoformat(ordered[0]["date"]).date() if ordered else None,
        "last_active": last_active,
        "current_start": current_start,
        "current_end": current_end,
        "longest_start": longest_start,
        "longest_end": longest_end,
    }


def short_date(value, include_year=False):
    if value is None:
        return "No activity yet"
    pattern = "%b %d, %Y" if include_year else "%b %d"
    return value.strftime(pattern).replace(" 0", " ")


def date_range(start, end):
    if start is None or end is None:
        return "No active streak yet"
    if start == end:
        return short_date(start, include_year=True)
    if start.year == end.year:
        return f"{short_date(start)} — {short_date(end)}, {end.year}"
    return f"{short_date(start, include_year=True)} — {short_date(end, include_year=True)}"


def language_counts(repositories):
    result = {}

    for repo in repositories:
        language = repo.get("primaryLanguage")
        if language and language.get("name"):
            name = language["name"]
            result[name] = result.get(name, 0) + 1

    return sorted(result.items(), key=lambda item: (-item[1], item[0]))


def esc(value):
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def svg_defs():
    return """
    <defs>
      <linearGradient id="panel" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="#0b1220"/>
        <stop offset="0.52" stop-color="#0d1424"/>
        <stop offset="1" stop-color="#090f1b"/>
      </linearGradient>
      <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0" stop-color="#8b5cf6"/>
        <stop offset="0.5" stop-color="#22d3ee"/>
        <stop offset="1" stop-color="#34d399"/>
      </linearGradient>
      <linearGradient id="card" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#172033" stop-opacity="0.92"/>
        <stop offset="1" stop-color="#111827" stop-opacity="0.78"/>
      </linearGradient>
      <radialGradient id="glow">
        <stop offset="0" stop-color="#22d3ee" stop-opacity="0.18"/>
        <stop offset="1" stop-color="#22d3ee" stop-opacity="0"/>
      </radialGradient>
      <filter id="softGlow" x="-40%" y="-40%" width="180%" height="180%">
        <feGaussianBlur stdDeviation="4" result="blur"/>
        <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
      <pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse">
        <path d="M28 0H0V28" fill="none" stroke="#64748b" stroke-opacity="0.045"/>
      </pattern>
      <style>
        text { font-family: "Segoe UI", Arial, sans-serif; }
        .mono { font-family: "JetBrains Mono", Consolas, monospace; }
        .fade { animation: rise .7s ease-out both; }
        .pulse { animation: pulse 2.4s ease-in-out infinite; transform-origin: center; }
        .flow { animation: flow 5s linear infinite; }
        .ring { animation: drawRing 1.4s cubic-bezier(.22,.9,.32,1) both, ringGlow 2.8s ease-in-out 1.4s infinite; }
        .stat-zone { transition: opacity .2s ease; }
        .stat-zone:hover { opacity: .82; }
        @keyframes rise { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes pulse { 0%, 100% { opacity: .55; } 50% { opacity: 1; } }
        @keyframes flow { to { stroke-dashoffset: -80; } }
        @keyframes drawRing { from { stroke-dashoffset: 402; } to { stroke-dashoffset: 0; } }
        @keyframes ringGlow { 0%, 100% { opacity: .82; } 50% { opacity: 1; } }
        @media (prefers-reduced-motion: reduce) { * { animation: none !important; } }
      </style>
    </defs>
    """


def svg_frame(width, height, title, description):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">'
        f'<title id="title">{esc(title)}</title>'
        f'<desc id="desc">{esc(description)}</desc>'
        + svg_defs()
        + f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="22" fill="url(#panel)" stroke="#334155"/>'
        + f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="22" fill="url(#grid)"/>'
        + f'<ellipse cx="{width - 70}" cy="20" rx="210" ry="170" fill="url(#glow)"/>'
        + f'<path d="M22 1H{width - 22}" stroke="url(#accent)" stroke-width="2" stroke-linecap="round"/>'
    )


def stats_svg(user):
    collection = user["contributionsCollection"]
    calendar = collection["contributionCalendar"]
    days = [day for week in calendar["weeks"] for day in week["contributionDays"]]
    current, longest = calculate_streaks(days)
    details = streak_details(days)

    repositories = user["repositories"]["nodes"]
    stars = sum(repo["stargazerCount"] for repo in repositories)
    contributions = calendar["totalContributions"]
    commits = collection["totalCommitContributions"]
    prs = collection["totalPullRequestContributions"]
    issues = collection["totalIssueContributions"]
    updated = datetime.now(timezone.utc).strftime("%d %b %Y · %H:%M UTC").upper()
    contribution_period = (
        f'{short_date(details["period_start"], include_year=True)} — PRESENT'
        if details["period_start"]
        else "PAST 365 DAYS"
    )
    current_period = (
        date_range(details["current_start"], details["current_end"])
        if current > 0
        else f'Last active {short_date(details["last_active"], include_year=True)}'
    )
    longest_period = date_range(details["longest_start"], details["longest_end"])

    output = [
        svg_frame(900, 410, "GitHub streak analytics", "A neon three-column GitHub dashboard showing total contributions, current streak, longest streak, and supporting profile metrics."),
        '<g class="fade">',
        '<circle cx="40" cy="37" r="5" fill="#76ff03" filter="url(#softGlow)" class="pulse"/>',
        '<text x="55" y="42" fill="#f8fafc" font-size="19" font-weight="700" letter-spacing="1.6">GITHUB ANALYTICS</text>',
        f'<text x="858" y="40" fill="#64748b" font-size="10" text-anchor="end" class="mono">UPDATED {esc(updated)}</text>',
        '</g>',
        '<rect x="34" y="67" width="832" height="274" rx="17" fill="#030507" stroke="#1f2937"/>',
        '<rect x="35" y="68" width="830" height="272" rx="16" fill="none" stroke="url(#accent)" stroke-opacity="0.22"/>',
        '<path d="M311 99V309M589 99V309" stroke="#64748b" stroke-opacity="0.75"/>',

        '<g class="stat-zone fade" style="animation-delay:100ms">',
        f'<text x="172" y="158" fill="#76ff03" font-size="42" font-weight="800" text-anchor="middle" class="mono">{contributions}</text>',
        '<text x="172" y="201" fill="#76ff03" font-size="16" font-weight="600" text-anchor="middle">Total Contributions</text>',
        f'<text x="172" y="238" fill="#f1f5f9" font-size="12" text-anchor="middle" class="mono">{esc(contribution_period)}</text>',
        f'<text x="172" y="285" fill="#64748b" font-size="10" text-anchor="middle" class="mono">{commits} COMMITS · {prs} PRS · {issues} ISSUES</text>',
        '</g>',

        '<g class="stat-zone fade" style="animation-delay:220ms">',
        '<circle cx="450" cy="164" r="65" fill="#061006" stroke="#172033" stroke-width="8"/>',
        '<circle cx="450" cy="164" r="65" fill="none" stroke="#76ff03" stroke-width="7" stroke-linecap="round" stroke-dasharray="402" class="ring" filter="url(#softGlow)" transform="rotate(-90 450 164)"/>',
        '<circle cx="450" cy="164" r="54" fill="url(#glow)" opacity="0.55"/>',
        '<path d="M450 76c8 9 8 18 1 24 11-2 17-11 13-22 11 7 16 18 12 28-4 12-14 18-26 18s-22-6-26-18c-4-11 2-23 14-30-2 10 1 17 7 20-2-8-1-14 5-20Z" fill="#76ff03" filter="url(#softGlow)" class="pulse"/>',
        f'<text x="450" y="179" fill="#00c8ff" font-size="38" font-weight="800" text-anchor="middle" class="mono">{current}</text>',
        '<text x="450" y="262" fill="#00c8ff" font-size="17" font-weight="700" text-anchor="middle">Current Streak</text>',
        f'<text x="450" y="294" fill="#f1f5f9" font-size="11" text-anchor="middle" class="mono">{esc(current_period)}</text>',
        '</g>',

        '<g class="stat-zone fade" style="animation-delay:340ms">',
        f'<text x="728" y="158" fill="#76ff03" font-size="42" font-weight="800" text-anchor="middle" class="mono">{longest}</text>',
        '<text x="728" y="201" fill="#76ff03" font-size="16" font-weight="600" text-anchor="middle">Longest Streak</text>',
        f'<text x="728" y="238" fill="#f1f5f9" font-size="12" text-anchor="middle" class="mono">{esc(longest_period)}</text>',
        '<text x="728" y="285" fill="#64748b" font-size="10" text-anchor="middle" class="mono">PERSONAL CONSISTENCY RECORD</text>',
        '</g>',

        '<g class="fade" style="animation-delay:500ms">',
        '<text x="40" y="379" fill="#64748b" font-size="10" letter-spacing="1">PROFILE SIGNAL</text>',
        f'<text x="155" y="379" fill="#cbd5e1" font-size="11" class="mono">{user["repositories"]["totalCount"]} REPOSITORIES</text>',
        '<circle cx="278" cy="375" r="2" fill="#334155"/>',
        f'<text x="299" y="379" fill="#cbd5e1" font-size="11" class="mono">{stars} STARS</text>',
        '<circle cx="375" cy="375" r="2" fill="#334155"/>',
        f'<text x="396" y="379" fill="#cbd5e1" font-size="11" class="mono">{user["followers"]["totalCount"]} FOLLOWERS</text>',
        '<circle cx="511" cy="375" r="2" fill="#334155"/>',
        '<text x="532" y="379" fill="#22d3ee" font-size="10" class="mono">LIVE GITHUB GRAPHQL</text>',
        '<text x="858" y="379" fill="#475569" font-size="9" text-anchor="end" class="mono">REFRESHED DAILY</text>',
        '</g></svg>',
    ]

    return "".join(output)


def languages_svg(user):
    languages = language_counts(user["repositories"]["nodes"])[:8]
    total = sum(count for _, count in languages) or 1
    bar_width = 822

    output = [
        svg_frame(900, 330, "Repository language map", "Primary language distribution across public repositories."),
        '<text x="38" y="46" fill="#f8fafc" font-size="20" font-weight="700" letter-spacing="1.2">LANGUAGE FOOTPRINT</text>',
        f'<text x="38" y="70" fill="#64748b" font-size="12">Primary language across {total} classified public repositories</text>',
        '<text x="862" y="48" fill="#22d3ee" font-size="10" text-anchor="end" letter-spacing="1.3">REPOSITORY DISTRIBUTION</text>',
        '<rect x="38" y="91" width="824" height="18" rx="9" fill="#1e293b"/>',
    ]

    cursor = 39.0
    for index, (name, count) in enumerate(languages):
        width = bar_width * count / total
        color = LANGUAGE_COLORS.get(name, "#94a3b8")
        radius = 8 if index in (0, len(languages) - 1) else 0
        output.append(
            f'<rect x="{cursor:.1f}" y="92" width="{width:.1f}" height="16" rx="{radius}" '
            f'fill="{color}" class="fade" style="animation-delay:{index * 80}ms"/>'
        )
        cursor += width

    for index, (name, count) in enumerate(languages):
        col = index % 4
        row = index // 4
        x = 38 + col * 207
        y = 137 + row * 75
        percent = count / total * 100
        color = LANGUAGE_COLORS.get(name, "#94a3b8")
        output.extend([
            f'<g class="fade" style="animation-delay:{160 + index * 60}ms">',
            f'<rect x="{x}" y="{y}" width="190" height="60" rx="12" fill="#111827" fill-opacity="0.78" stroke="#263449"/>',
            f'<circle cx="{x + 18}" cy="{y + 20}" r="5" fill="{color}" filter="url(#softGlow)"/>',
            f'<text x="{x + 31}" y="{y + 24}" fill="#e2e8f0" font-size="13" font-weight="600">{esc(name)}</text>',
            f'<text x="{x + 18}" y="{y + 47}" fill="#64748b" font-size="10">{count} {"repo" if count == 1 else "repos"}</text>',
            f'<text x="{x + 172}" y="{y + 47}" fill="{color}" font-size="12" font-weight="700" text-anchor="end" class="mono">{percent:.1f}%</text>',
            '</g>',
        ])

    output.extend([
        '<text x="38" y="308" fill="#475569" font-size="10">Based on each repository\'s primary language · Forks excluded</text>',
        '<text x="862" y="308" fill="#475569" font-size="10" text-anchor="end" class="mono">TOP 8 LANGUAGES</text>',
        '</svg>',
    ])
    return "".join(output)


def contribution_graph_svg(user):
    calendar = user["contributionsCollection"]["contributionCalendar"]
    weeks = calendar["weeks"][-53:]
    days = [day for week in weeks for day in week["contributionDays"]]
    current, longest = calculate_streaks(days)

    output = [
        svg_frame(900, 255, "GitHub contribution activity", "A one-year contribution calendar with current and longest streak statistics."),
        '<text x="34" y="43" fill="#f8fafc" font-size="20" font-weight="700" letter-spacing="1.2">CONTRIBUTION SIGNAL</text>',
        '<text x="34" y="65" fill="#64748b" font-size="11">365 days of building, learning, and shipping</text>',
        '<rect x="713" y="27" width="153" height="43" rx="12" fill="#111827" stroke="#263449"/>',
        f'<text x="730" y="45" fill="#64748b" font-size="9" letter-spacing="1">TOTAL ACTIVITY</text>',
        f'<text x="730" y="62" fill="#22d3ee" font-size="15" font-weight="700" class="mono">{calendar["totalContributions"]}</text>',
        '<circle cx="844" cy="49" r="5" fill="#34d399" class="pulse" filter="url(#softGlow)"/>',
        '<text x="32" y="111" fill="#64748b" font-size="9">MON</text>',
        '<text x="32" y="139" fill="#64748b" font-size="9">WED</text>',
        '<text x="32" y="167" fill="#64748b" font-size="9">FRI</text>',
    ]

    last_month = None
    last_label_x = -100
    for col, week in enumerate(weeks):
        x = 73 + col * 14
        if not week["contributionDays"]:
            continue
        first_date = datetime.fromisoformat(week["contributionDays"][0]["date"])
        month = first_date.strftime("%b").upper()
        if month != last_month and x - last_label_x >= 36:
            output.append(f'<text x="{x}" y="88" fill="#64748b" font-size="9" class="mono">{month}</text>')
            last_label_x = x
        last_month = month

        for day in week["contributionDays"]:
            date = datetime.fromisoformat(day["date"])
            row = (date.weekday() + 1) % 7
            y = 96 + row * 14
            count = day["contributionCount"]
            if count == 0:
                fill = "#172033"
            elif count <= 2:
                fill = "#164e63"
            elif count <= 5:
                fill = "#0891b2"
            elif count <= 9:
                fill = "#22d3ee"
            else:
                fill = "#67e8f9"
            output.append(
                f'<rect x="{x}" y="{y}" width="10" height="10" rx="2" fill="{fill}" class="fade" '
                f'style="animation-delay:{col * 12}ms"><title>{esc(day["date"])}: {count} contributions</title></rect>'
            )

    output.extend([
        '<rect x="34" y="210" width="168" height="27" rx="8" fill="#111827" stroke="#263449"/>',
        '<text x="47" y="228" fill="#64748b" font-size="10">CURRENT STREAK</text>',
        f'<text x="187" y="228" fill="#34d399" font-size="11" font-weight="700" text-anchor="end" class="mono">{current} DAYS</text>',
        '<rect x="216" y="210" width="168" height="27" rx="8" fill="#111827" stroke="#263449"/>',
        '<text x="229" y="228" fill="#64748b" font-size="10">LONGEST STREAK</text>',
        f'<text x="369" y="228" fill="#a78bfa" font-size="11" font-weight="700" text-anchor="end" class="mono">{longest} DAYS</text>',
        '<text x="697" y="228" fill="#64748b" font-size="9">LESS</text>',
        '<rect x="730" y="219" width="10" height="10" rx="2" fill="#172033"/>',
        '<rect x="746" y="219" width="10" height="10" rx="2" fill="#164e63"/>',
        '<rect x="762" y="219" width="10" height="10" rx="2" fill="#0891b2"/>',
        '<rect x="778" y="219" width="10" height="10" rx="2" fill="#22d3ee"/>',
        '<rect x="794" y="219" width="10" height="10" rx="2" fill="#67e8f9"/>',
        '<text x="812" y="228" fill="#64748b" font-size="9">MORE</text>',
        '</svg>',
    ])
    return "".join(output)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    user = fetch_user()

    with open(f"{OUTPUT_DIR}/github-stats.svg", "w", encoding="utf-8") as file:
        file.write(stats_svg(user))

    with open(f"{OUTPUT_DIR}/languages.svg", "w", encoding="utf-8") as file:
        file.write(languages_svg(user))

    with open(f"{OUTPUT_DIR}/contribution-graph.svg", "w", encoding="utf-8") as file:
        file.write(contribution_graph_svg(user))

    print("Generated premium GitHub profile analytics successfully.")


if __name__ == "__main__":
    main()
