import pytest
from pathlib import Path
from fastmcp import Client
from workflow_mcp.server import mcp

@pytest.fixture
def mock_project(tmp_path: Path):
    """Create a temporary project environment with PLAN.md and docs/steps/."""
    plan_file = tmp_path / "PLAN.md"
    plan_file.write_text(
        "# Project Plan\n\n"
        "| Done | Step | Description |\n"
        "| --- | --- | --- |\n"
        "| [x] | 0 | Setup project |\n"
        "| [ ] | 1 | Refactor UI |\n"
    )

    steps_dir = tmp_path / "docs" / "steps"
    steps_dir.mkdir(parents=True)
    (steps_dir / "STEP_01.md").write_text("# Step 1 Guide\nExecute refactoring.")

    return tmp_path

@pytest.mark.asyncio
async def test_workflow_mcp_tools(mock_project: Path, monkeypatch: pytest.MonkeyPatch):
    """Test de FastMCP tools via de InMemory Client."""
    monkeypatch.setattr("workflow_mcp.server._PROJECT_ROOT", mock_project)

    async with Client(mcp) as client:
        # 1. Controleer of tools geregistreerd staan
        tools = await client.list_tools()
        tool_names = [t.name for t in tools]
        assert "get_plan_status" in tool_names
        assert "get_current_step" in tool_names
        assert "mark_step_complete" in tool_names

        # 2. Test 'get_current_step'
        res = await client.call_tool("get_current_step")
        assert res is not None

        # 3. Test 'mark_step_complete'
        update_res = await client.call_tool("mark_step_complete", {"step_id": "1"})
        assert update_res is not None
        
        # Check if the file was actually updated
        plan_text = (mock_project / "PLAN.md").read_text()
        assert "| [x] | 1 |" in plan_text