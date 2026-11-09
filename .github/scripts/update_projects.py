"""Rewrite the project list in README.md from the owner's public GitHub repositories."""

from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path

OWNER = "yousef-megeed"
# Repositories to leave off the profile, in addition to forks, archives and undescribed repos.
HIDDEN: set[str] = {OWNER}
START = "<!-- projects:start -->"
END = "<!-- projects:end -->"


def fetch_repositories() -> list[dict]:
    repositories: list[dict] = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/users/{OWNER}/repos"
            f"?type=owner&sort=created&direction=desc&per_page=100&page={page}"
        )
        request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            request.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(request, timeout=30) as response:
            batch = json.load(response)
        repositories.extend(batch)
        if len(batch) < 100:
            return repositories
        page += 1


def is_listed(repository: dict) -> bool:
    return (
        not repository["private"]
        and not repository["fork"]
        and not repository["archived"]
        and bool((repository.get("description") or "").strip())
        and repository["name"] not in HIDDEN
    )


def render(repositories: list[dict]) -> str:
    """Newest first, with descriptions on one line and Markdown control characters escaped."""
    lines = []
    for repository in repositories:
        description = " ".join(repository["description"].split())
        description = re.sub(r"([\\`*_\[\]<>])", r"\\\1", description)
        lines.append(f"- **[{repository['name']}]({repository['html_url']})**: {description}")
    return "\n".join(lines)


def update(readme: str, listing: str) -> str:
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(readme):
        raise ValueError("README.md is missing the project list markers")
    return pattern.sub(lambda _: f"{START}\n{listing}\n{END}", readme)


def main() -> None:
    path = Path("README.md")
    listed = [repository for repository in fetch_repositories() if is_listed(repository)]
    if not listed:
        raise RuntimeError("No repositories found; leaving README.md unchanged")
    path.write_text(update(path.read_text(encoding="utf-8"), render(listed)), encoding="utf-8")
    print(f"Listed {len(listed)} repositories")


if __name__ == "__main__":
    main()
