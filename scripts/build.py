import html
import json
import os
import pathlib
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request


API_URL = "https://api.github.com"
API_VERSION = "2026-03-10"

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE_FILE = ROOT_DIR / "templates" / "index.html"
SITE_DIR = ROOT_DIR / "_site"
REPOS_DIR = SITE_DIR / "repos"

TOKEN = os.environ.get("GITHUB_TOKEN")

if not TOKEN:
    print("GITHUB_TOKEN is not set", file=sys.stderr)
    sys.exit(1)


def github_request(path, accept="application/vnd.github+json"):
    request = urllib.request.Request(
        API_URL + path,
        headers={
            "Accept": accept,
            "Authorization": f"Bearer {TOKEN}",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "github-starred-repos-page",
        },
    )

    try:
        with urllib.request.urlopen(request) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None

        body = exc.read().decode("utf-8", errors="replace")
        print(f"GitHub API request failed: {path}", file=sys.stderr)
        print(f"HTTP {exc.code}: {body}", file=sys.stderr)
        raise


def github_json(path):
    data = github_request(path)
    if data is None:
        return None
    return json.loads(data)


def fetch_starred_repos():
    repos = []
    page = 1

    while True:
        print(f"Fetching starred repositories page {page}")

        result = github_json(f"/user/starred?per_page=100&page={page}")

        if not result:
            break

        repos.extend(result)

        if len(result) < 100:
            break

        page += 1

    return repos


def fetch_readme(owner, repo):
    owner = urllib.parse.quote(owner, safe="")
    repo = urllib.parse.quote(repo, safe="")

    return github_request(
        f"/repos/{owner}/{repo}/readme",
        accept="application/vnd.github.raw+json",
    )


def prepare_output():
    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)

    REPOS_DIR.mkdir(parents=True)


def readme_filename(owner, repo):
    return f"{owner}_{repo}.md"


def make_repo_row(repo, readme_exists):
    owner = repo["owner"]["login"]
    name = repo["name"]
    full_name = repo["full_name"]
    url = repo["html_url"]
    description = repo.get("description") or ""
    topics = repo.get("topics") or []

    search_text = " ".join(
        [
            owner,
            name,
            full_name,
            description,
            *topics,
        ]
    ).lower()

    topics_html = "".join(
        f'<span class="topic">{html.escape(topic)}</span>'
        for topic in topics
    )

    if readme_exists:
        filename = readme_filename(owner, name)
        readme_url = "repos/" + urllib.parse.quote(filename, safe="")
        readme_html = f'<a href="{readme_url}">README</a>'
    else:
        readme_html = '<span class="muted">No README</span>'

    return f"""
<tr data-search="{html.escape(search_text, quote=True)}">
    <td>
        <a
            class="repo-name"
            href="{html.escape(url, quote=True)}"
            target="_blank"
            rel="noopener noreferrer"
        >
            {html.escape(full_name)}
        </a>

        <div class="topics">
            {topics_html}
        </div>
    </td>

    <td>
        {html.escape(description)}
    </td>

    <td class="readme">
        {readme_html}
    </td>
</tr>
"""


def build():
    prepare_output()

    repos = fetch_starred_repos()
    print(f"Found {len(repos)} starred repositories")

    # GitHub Pages is public. Never publish content from private repos.
    public_repos = [repo for repo in repos if not repo.get("private", False)]
    skipped_private = len(repos) - len(public_repos)

    if skipped_private:
        print(f"Skipping {skipped_private} private repositories")

    print(f"Publishing {len(public_repos)} public repositories")

    rows = []

    for index, repo in enumerate(public_repos, start=1):
        owner = repo["owner"]["login"]
        name = repo["name"]
        full_name = repo["full_name"]

        print(f"[{index}/{len(public_repos)}] {full_name}")

        readme = None

        try:
            readme = fetch_readme(owner, name)
        except Exception as exc:
            print(
                f"Warning: failed to fetch README for {full_name}: {exc}",
                file=sys.stderr,
            )

        if readme is not None:
            path = REPOS_DIR / readme_filename(owner, name)
            path.write_bytes(readme)

        rows.append(make_repo_row(repo, readme_exists=readme is not None))

    template = TEMPLATE_FILE.read_text(encoding="utf-8")

    document = (
        template.replace("{{REPO_COUNT}}", str(len(public_repos)))
        .replace("{{REPO_ROWS}}", "\n".join(rows))
    )

    (SITE_DIR / "index.html").write_text(document, encoding="utf-8")

    print()
    print("Build complete")
    print(f"Site: {SITE_DIR}")
    print(f"READMEs: {REPOS_DIR}")


if __name__ == "__main__":
    build()
