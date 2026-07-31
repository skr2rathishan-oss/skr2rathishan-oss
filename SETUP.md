# 🚀 Rathishan GitHub Profile — Complete Stats Setup

This package is designed for the profile repository:

`Rathishan/Rathishan`

It replaces the unreliable third-party stats cards with SVG files generated from **real GitHub GraphQL API data**.

## 📁 Files

```text
Rathishan/
│
├── README.md
│
├── .github/
│   └── workflows/
│       └── github-stats.yml
│
├── scripts/
│   └── generate_stats.py
│
└── assets/
    ├── github-stats.svg
    ├── languages.svg
    └── contribution-graph.svg
```

## 1. Replace your README

The included `README.md` is already based on your existing profile README.

Upload it to:

```text
Rathishan/Rathishan
```

## 2. Upload the workflow

Upload:

```text
.github/workflows/github-stats.yml
```

## 3. Upload the Python script

Upload:

```text
scripts/generate_stats.py
```

## 4. Assets

You can initially leave `assets/` empty.

The GitHub Action generates:

```text
assets/github-stats.svg
assets/languages.svg
assets/contribution-graph.svg
```

## 5. Run the workflow

Go to:

**GitHub → Rathishan/Rathishan → Actions**

Select:

**Update GitHub Profile Stats**

Then click:

**Run workflow**

After it succeeds, GitHub Actions commits the generated SVG files to your repository.

## 6. Automatic updates

The workflow runs once every day:

```yaml
schedule:
  - cron: "17 0 * * *"
```

It also runs when you manually trigger it.

## 🔐 No personal GitHub token required

The workflow uses GitHub's built-in:

```text
GITHUB_TOKEN
```

You do **not** need to create a personal access token.

The workflow has:

```yaml
permissions:
  contents: write
```

which allows it to commit the generated SVG files.

## 📊 Real GitHub data

The generated cards use GitHub GraphQL data for:

- Total contributions
- Current contribution streak
- Longest contribution streak
- Public repositories
- Stars received
- Followers
- Commit contributions
- Pull requests
- Issues
- Primary languages

The contribution graph is generated from GitHub's actual contribution calendar.

## ⚠️ Language statistic

The language card counts the **primary language of your public repositories**.

It is not a byte-level calculation of every line of code.

## 🛠️ If the Action fails

Open:

**Repository → Actions → Update GitHub Profile Stats**

Open the failed run and check the failed step.

Most importantly, verify the repository is:

```text
Rathishan/Rathishan
```

and that the workflow is located exactly at:

```text
.github/workflows/github-stats.yml
```

## 🔄 After adding a new project

You don't need to manually update the README.

The next scheduled workflow run will regenerate the statistics.

You can also manually run the workflow whenever you want the stats refreshed immediately.
