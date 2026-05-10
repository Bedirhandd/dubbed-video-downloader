# Contributing

Contributions are welcome, and issues are welcome too. Thanks for helping improve this project.

This project follows the Conventional Commits style. See the specification here:
https://www.conventionalcommits.org/en/v1.0.0/

## For Humans

- Use commit messages in this format: `<type>(<scope>): <description>`
- Use branch names in this format: `<type>/<short-description>`
- Use pull request titles in the same format as commit messages: `<type>(<scope>): <description>`
- Keep pull requests focused on one change when possible.
- Include a short description of what changed and how it was tested.
- Open an issue for bugs, questions, suggestions, or improvements.

### Fork Workflow

If you do not have write access to this repository:

1. Fork the repository to your GitHub account.
2. Clone your fork locally.
3. Create a branch using the project branch naming format: `<type>/<short-description>`
4. Make your changes and commit them using the project commit message format: `<type>(<scope>): <description>`
5. Push your branch to your fork.
6. Open a pull request from your fork branch to this repository.

Before opening a pull request, make sure your branch is up to date with the target branch and include a short note about what changed and how you checked it.

Examples:

```text
docs(readme): add setup notes
fix(download): handle missing dub language
chore(deps): update yt-dlp
```

```text
docs/update-readme
fix/missing-dub-language
chore/update-yt-dlp
```

## For Agents

- Follow the same commit, branch, and pull request naming conventions used by humans.
- Keep edits scoped to the requested task.
- Prefer small, reviewable documentation or code changes.
- Do not rewrite unrelated files or revert user changes.
- Mention the checks, tests, or manual verification performed.
- If something cannot be verified, state that clearly in the pull request or response.
