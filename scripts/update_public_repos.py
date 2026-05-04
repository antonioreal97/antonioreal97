#!/usr/bin/env python3
"""Atualiza o bloco entre PUBLIC_REPOS_START/END no README.md via API do GitHub."""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request

USERNAME = "antonioreal97"
START = "<!-- PUBLIC_REPOS_START -->"
END = "<!-- PUBLIC_REPOS_END -->"
README = "README.md"


def fetch_all_repos() -> list[dict]:
    repos: list[dict] = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/users/{USERNAME}/repos"
            f"?per_page=100&page={page}&sort=full_name&type=owner"
        )
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                batch = json.load(resp)
        except urllib.error.HTTPError as e:
            print(e.read().decode("utf-8", errors="replace"), file=sys.stderr)
            raise
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    public = [r for r in repos if not r.get("private")]
    public.sort(key=lambda r: str(r["name"]).lower())
    return public


def md_row(r: dict) -> str:
    name = r["name"]
    url = r["html_url"]
    desc = (r.get("description") or "—").replace("|", "\\|").replace("\n", " ").strip()
    if r.get("fork"):
        desc = f"{desc} _(fork)_" if desc != "—" else "_(fork)_"
    lang = r.get("language") or "—"
    stars = r.get("stargazers_count", 0)
    link = f"[{name}]({url})"
    return f"| {link} | {desc} | {lang} | {stars} |"


def build_table(repos: list[dict]) -> str:
    lines = [
        "| Repositório | Descrição | Linguagem | ⭐ |",
        "|-------------|-----------|-----------|-----|",
    ]
    lines.extend(md_row(r) for r in repos)
    return "\n".join(lines)


def main() -> None:
    try:
        with open(README, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Arquivo não encontrado: {README}", file=sys.stderr)
        sys.exit(1)

    repos = fetch_all_repos()
    table = build_table(repos)
    block = f"{START}\n{table}\n{END}"

    if START not in content or END not in content:
        print("Marcadores PUBLIC_REPOS não encontrados no README.", file=sys.stderr)
        sys.exit(1)

    pattern = re.escape(START) + r".*?" + re.escape(END)
    new_content = re.sub(pattern, block, content, count=1, flags=re.DOTALL)

    if new_content == content:
        print(f"Sem mudanças ({len(repos)} repositórios públicos).")
        return

    with open(README, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"README atualizado: {len(repos)} repositórios públicos.")


if __name__ == "__main__":
    main()
