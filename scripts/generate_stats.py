import json
import os
import urllib.request
from datetime import datetime, timezone, timedelta

USERNAME = os.environ.get("GITHUB_USERNAME", "Rathishan")
TOKEN = os.environ["GITHUB_TOKEN"]
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

def fetch_user():
    body = json.dumps({
        "query": QUERY,
        "variables": {"login": USERNAME}
    }).encode()

    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "Rathishan-GitHub-Profile-Stats",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode())

    if result.get("errors"):
        raise RuntimeError(json.dumps(result["errors"], indent=2))

    return result["data"]["user"]

def calculate_streaks(days):
    counts = {d["date"]: d["contributionCount"] for d in days}

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

    return sorted(result.items(), key=lambda item: item[1], reverse=True)

def esc(value):
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )

def stats_svg(user):
    calendar = user["contributionsCollection"]["contributionCalendar"]

    days = [
        day
        for week in calendar["weeks"]
        for day in week["contributionDays"]
    ]

    current, longest = calculate_streaks(days)

    repos = user["repositories"]["nodes"]
    stars = sum(repo["stargazerCount"] for repo in repos)

    contributions = calendar["totalContributions"]
    commits = user["contributionsCollection"]["totalCommitContributions"]
    prs = user["contributionsCollection"]["totalPullRequestContributions"]
    issues = user["contributionsCollection"]["totalIssueContributions"]

    cards = [
        ("Total Contributions", contributions),
        ("Current Streak", f"{current} days"),
        ("Longest Streak", f"{longest} days"),
        ("Public Repositories", user["repositories"]["totalCount"]),
        ("Stars Received", stars),
        ("Followers", user["followers"]["totalCount"]),
    ]

    output = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="390" viewBox="0 0 900 390">',
        '<rect width="900" height="390" rx="18" fill="#0d1117"/>',
        '<text x="45" y="55" fill="#58a6ff" font-family="Arial,sans-serif" font-size="26" font-weight="700">GitHub Statistics</text>',
        '<text x="45" y="82" fill="#8b949e" font-family="Arial,sans-serif" font-size="15">Real data from GitHub GraphQL API</text>'
    ]

    positions = [
        (45, 115),
        (325, 115),
        (605, 115),
        (45, 230),
        (325, 230),
        (605, 230),
    ]

    for (label, value), (x, y) in zip(cards, positions):
        output.append(
            f'<rect x="{x}" y="{y}" width="250" height="95" rx="12" fill="#161b22" stroke="#30363d"/>'
            f'<text x="{x+23}" y="{y+33}" fill="#8b949e" font-family="Arial,sans-serif" font-size="14">{esc(label)}</text>'
            f'<text x="{x+23}" y="{y+69}" fill="#f0f6fc" font-family="Arial,sans-serif" font-size="30" font-weight="700">{esc(value)}</text>'
        )

    output.append(
        f'<text x="45" y="360" fill="#8b949e" font-family="Arial,sans-serif" font-size="13">'
        f'Commits: {commits} | Pull Requests: {prs} | Issues: {issues}</text>'
    )
    output.append("</svg>")

    return "".join(output)

def languages_svg(user):
    languages = language_counts(user["repositories"]["nodes"])[:8]
    total = sum(count for _, count in languages) or 1
    height = 90 + len(languages) * 48

    rows = []
    y = 78

    for name, count in languages:
        percent = count / total * 100

        rows.append(
            f'<text x="40" y="{y}" fill="#f0f6fc" font-family="Arial,sans-serif" font-size="15">{esc(name)}</text>'
            f'<text x="530" y="{y}" fill="#8b949e" font-family="Arial,sans-serif" font-size="14" text-anchor="end">{percent:.1f}%</text>'
            f'<rect x="40" y="{y+12}" width="500" height="7" rx="3" fill="#21262d"/>'
            f'<rect x="40" y="{y+12}" width="{500*percent/100:.1f}" height="7" rx="3" fill="#58a6ff"/>'
        )

        y += 48

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="580" height="{height}" viewBox="0 0 580 {height}">'
        f'<rect width="580" height="{height}" rx="18" fill="#0d1117" stroke="#30363d"/>'
        f'<text x="40" y="38" fill="#58a6ff" font-family="Arial,sans-serif" font-size="21" font-weight="700">Languages by Public Repositories</text>'
        + "".join(rows)
        + "</svg>"
    )

def contribution_graph_svg(user):
    days = [
        day
        for week in user["contributionsCollection"]["contributionCalendar"]["weeks"]
        for day in week["contributionDays"]
    ]

    # Last 365 days; GitHub contribution calendar is the source of truth.
    days = days[-365:]
    width = 900
    height = 190
    cell = 11
    gap = 3

    output = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" rx="18" fill="#0d1117" stroke="#30363d"/>',
        '<text x="35" y="32" fill="#58a6ff" font-family="Arial,sans-serif" font-size="20" font-weight="700">Contribution Activity</text>'
    ]

    # Arrange 7 rows by weekday, approximately 52 columns.
    for index, day in enumerate(days):
        col = index // 7
        row = index % 7

        x = 35 + col * (cell + gap)
        y = 52 + row * (cell + gap)

        count = day["contributionCount"]

        if count == 0:
            fill = "#161b22"
        elif count <= 2:
            fill = "#0e4429"
        elif count <= 5:
            fill = "#006d32"
        elif count <= 9:
            fill = "#26a641"
        else:
            fill = "#39d353"

        output.append(
            f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{fill}"/>'
        )

    output.append(
        '<text x="35" y="165" fill="#8b949e" font-family="Arial,sans-serif" font-size="12">'
        f'Total contributions: {user["contributionsCollection"]["contributionCalendar"]["totalContributions"]}'
        '</text>'
    )

    output.append("</svg>")
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

    print("Generated GitHub profile statistics successfully.")

if __name__ == "__main__":
    main()
