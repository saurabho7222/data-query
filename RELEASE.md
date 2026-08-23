# Release Process

Releases are intentionally tied to real Git tags; the workflow never fabricates a tag or release history.

## Checklist

1. Land a meaningful, tested change through the normal CI/Security/CodeQL gates.
2. Update `CHANGELOG.md` and the package version in `pyproject.toml`; keep `uv.lock` consistent.
3. Confirm `make quality`, `make package-check`, `make compose-demo`, and `make security` are green.
4. Create and push a real version tag from the commit being released, for example `v0.2.1`.
5. `.github/workflows/release.yml` builds the wheel from that exact tagged source, installs it in a clean virtual environment, smoke-tests the console command, and only then creates the GitHub Release with generated notes.

The release workflow uses `gh release create --verify-tag`, so it cannot create a release for a non-existent tag.
