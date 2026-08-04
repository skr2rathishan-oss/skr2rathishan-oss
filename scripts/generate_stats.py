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
        @keyframes rise { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes pulse { 0%, 100% { opacity: .55; } 50% { opacity: 1; } }
        @keyframes flow { to { stroke-dashoffset: -80; } }
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

    repositories = user["repositories"]["nodes"]
    stars = sum(repo["stargazerCount"] for repo in repositories)
    contributions = calendar["totalContributions"]
    commits = collection["totalCommitContributions"]
    prs = collection["totalPullRequestContributions"]
    issues = collection["totalIssueContributions"]
    updated = datetime.now(timezone.utc).strftime("%d %b %Y · %H:%M UTC").upper()

    hero_cards = [
        ("CONTRIBUTIONS", contributions, "activity in the last year", "#22d3ee"),
        ("CURRENT STREAK", current, "consecutive active days", "#34d399"),
        ("LONGEST STREAK", longest, "personal consistency record", "#a78bfa"),
    ]
    small_cards = [
        ("PUBLIC REPOSITORIES", user["repositories"]["totalCount"], "01"),
        ("STARS EARNED", stars, "02"),
        ("FOLLOWERS", user["followers"]["totalCount"], "03"),
    ]

    output = [
        svg_frame(900, 475, "GitHub analytics dashboard", "Live GitHub contribution, streak, repository, star, follower, commit, pull request, and issue statistics."),
        '<g class="fade">',
        '<circle cx="42" cy="41" r="6" fill="#34d399" filter="url(#softGlow)" class="pulse"/>',
        '<text x="58" y="46" fill="#e2e8f0" font-size="20" font-weight="700" letter-spacing="1.8">GITHUB ANALYTICS</text>',
        f'<text x="58" y="69" fill="#64748b" font-size="12" class="mono">@{esc(user["login"])}</text>',
        f'<text x="858" y="46" fill="#94a3b8" font-size="11" text-anchor="end" class="mono">UPDATED {esc(updated)}</text>',
        '<text x="858" y="68" fill="#22d3ee" font-size="10" text-anchor="end" letter-spacing="1.4">LIVE · GITHUB GRAPHQL</text>',
        '</g>',
    ]

    for index, (label, value, note, color) in enumerate(hero_cards):
        x = 34 + index * 284
        output.extend([
            f'<g class="fade" style="animation-delay:{index * 90}ms">',
            f'<rect x="{x}" y="94" width="264" height="137" rx="16" fill="url(#card)" stroke="#263449"/>',
            f'<rect x="{x}" y="94" width="4" height="137" rx="2" fill="{color}"/>',
            f'<circle cx="{x + 231}" cy="126" r="17" fill="{color}" fill-opacity="0.10"/>',
            f'<circle cx="{x + 231}" cy="126" r="4" fill="{color}" class="pulse"/>',
            f'<text x="{x + 22}" y="124" fill="#94a3b8" font-size="11" font-weight="600" letter-spacing="1.25">{label}</text>',
            f'<text x="{x + 22}" y="174" fill="#f8fafc" font-size="42" font-weight="750" class="mono">{esc(value)}</text>',
            f'<text x="{x + 22}" y="207" fill="#64748b" font-size="12">{note}</text>',
            '</g>',
        ])

    for index, (label, value, number) in enumerate(small_cards):
        x = 34 + index * 284
        output.extend([
            f'<g class="fade" style="animation-delay:{270 + index * 70}ms">',
            f'<rect x="{x}" y="248" width="264" height="86" rx="14" fill="#111827" fill-opacity="0.84" stroke="#263449"/>',
            f'<text x="{x + 20}" y="278" fill="#64748b" font-size="10" font-weight="700" letter-spacing="1.1">{label}</text>',
            f'<text x="{x + 20}" y="316" fill="#e2e8f0" font-size="28" font-weight="700" class="mono">{esc(value)}</text>',
            f'<text x="{x + 237}" y="316" fill="#334155" font-size="30" font-weight="700" text-anchor="end" class="mono">{number}</text>',
            '</g>',
        ])

    activity_total = max(commits + prs + issues, 1)
    commit_width = 832 * commits / activity_total
    pr_width = 832 * prs / activity_total
    issue_width = 832 - commit_width - pr_width

    output.extend([
        '<g class="fade" style="animation-delay:480ms">',
        '<text x="34" y="375" fill="#cbd5e1" font-size="12" font-weight="700" letter-spacing="1.2">ACTIVITY MIX</text>',
        f'<text x="866" y="375" fill="#64748b" font-size="11" text-anchor="end">{activity_total} recorded actions</text>',
        '<rect x="34" y="391" width="832" height="12" rx="6" fill="#1e293b"/>',
        f'<rect x="34" y="391" width="{commit_width:.1f}" height="12" rx="6" fill="#22d3ee"/>',
        f'<rect x="{34 + commit_width:.1f}" y="391" width="{pr_width:.1f}" height="12" fill="#8b5cf6"/>',
        f'<rect x="{34 + commit_width + pr_width:.1f}" y="391" width="{issue_width:.1f}" height="12" rx="6" fill="#34d399"/>',
        '<circle cx="39" cy="438" r="4" fill="#22d3ee"/><text x="51" y="442" fill="#94a3b8" font-size="12">COMMITS</text>',
        f'<text x="132" y="442" fill="#e2e8f0" font-size="12" font-weight="700" class="mono">{commits}</text>',
        '<circle cx="218" cy="438" r="4" fill="#8b5cf6"/><text x="230" y="442" fill="#94a3b8" font-size="12">PULL REQUESTS</text>',
        f'<text x="344" y="442" fill="#e2e8f0" font-size="12" font-weight="700" class="mono">{prs}</text>',
        '<circle cx="430" cy="438" r="4" fill="#34d399"/><text x="442" y="442" fill="#94a3b8" font-size="12">ISSUES</text>',
        f'<text x="495" y="442" fill="#e2e8f0" font-size="12" font-weight="700" class="mono">{issues}</text>',
        '<text x="866" y="442" fill="#475569" font-size="10" text-anchor="end" class="mono">AUTOMATICALLY REFRESHED DAILY</text>',
        '</g></svg>',
    ])

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
