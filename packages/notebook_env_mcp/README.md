# notebook-env MCP

Cursor MCP tools to find the right `.venv` for a notebook and detect dead Jupyter kernels.

## Problem

Older notebooks often keep a `kernelspec.display_name` like `gensim_env` while the real environment moved to `uv sync` + `.venv`. The kernel picker shows many stale entries whose Python paths no longer exist.

## Setup

```bash
cd ~/develop/dighum_template/packages/notebook_env_mcp && uv sync
```

Add to `.cursor/mcp.json` (project or user level):

```json
{
  "mcpServers": {
    "notebook-env": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/Users/rikhoekstra/develop/dighum_template/packages/notebook_env_mcp",
        "notebook-env-mcp",
        "--scan-root",
        "${workspaceFolder}"
      ]
    }
  }
}
```

Use `--scan-root` `~/develop` if you want cross-repo discovery from any workspace.

Reload MCP in Cursor settings after editing.

## Tools

| Tool | Use when |
|------|----------|
| `list_project_venvs()` | See `.venv` dirs under the scan root |
| `list_jupyter_kernels()` | List kernels; spot dead paths (old conda, moved projects) |
| `recommend_env(path)` | Walk up from a notebook to `pyproject.toml` + `.venv` |
| `inspect_notebook_env(notebook_path)` | Notebook metadata + recommendation + register command |
| `fix_notebook_kernel(notebook_path, execute=false)` | Dry-run or apply kernelspec fix |

## Typical workflow

1. `inspect_notebook_env("notebooks/foo.ipynb")`
2. If `register_kernel_command` is returned, run it once in the project root
3. `fix_notebook_kernel("notebooks/foo.ipynb", execute=true)`
4. Reopen the notebook and pick the `(uv)` kernel

## Notes

- Read-only by default; only `fix_notebook_kernel(execute=true)` edits `.ipynb` metadata.
- Does not install packages — run `uv sync` in the project first.
- Scans skip `.git`, `node_modules`, and other heavy dirs.
