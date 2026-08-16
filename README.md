# Starred Repo Search

A simple static site for browsing and searching the GitHub starred repositories.

The site is generated from the GitHub stars using GitHub Actions. For each public starred repository, it collects:

- Owner name
- Repository name
- Repository URL
- GitHub description
- Topics
- README content

The generated site contains a searchable `index.html` plus one Markdown file per repository.

## Live Site

https://makercyf.github.io/starred-repo-search/

## Why

After starring hundreds of repositories, it becomes difficult to remember the name of a useful project you saw before.

This project turns GitHub stars into a small searchable knowledge base.

The index page is useful for normal browsing, and the generated README files make it easy for an LLM or other tool to inspect promising repositories when you only remember what a project does.

## How It Works

The workflow is triggered manually with `workflow_dispatch`.

It:

1. Fetches all starred repositories from the authenticated GitHub account.
2. Keeps public repositories only.
3. Extracts repository metadata.
4. Downloads each repository README.
5. Generates the static site.
6. Deploys the result to GitHub Pages.

The generated site looks like:

```text
_site/
├── index.html
└── repos/
    ├── owner_repo-a.md
    ├── owner_repo-b.md
    └── owner_repo-c.md
```

README files use the flat naming format:

```text
repos/<owner>_<repo>.md
```

## License

Use, modify, and adapt this project however you like.
