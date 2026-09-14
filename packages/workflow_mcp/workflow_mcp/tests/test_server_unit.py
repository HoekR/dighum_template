import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

# Insert a lightweight fake `fastmcp` module so tests don't require the real dependency.
if 'fastmcp' not in sys.modules:
    fake = types.ModuleType('fastmcp')

    class _FakeFastMCP:
        def __init__(self, *args, **kwargs):
            self._tools = {}

        def tool(self, func=None):
            # decorator used in server to register tools; no-op
            if func is None:
                def _decorator(f):
                    return f

                return _decorator
            return func

        def run(self, *args, **kwargs):
            # placeholder; tests patch this attribute
            raise RuntimeError('fake FastMCP.run should be patched in tests')

    fake.FastMCP = _FakeFastMCP
    sys.modules['fastmcp'] = fake


class ServerCLITests(unittest.TestCase):
    def test_default_runs_stdio(self):
        """Calling main() with no args should invoke mcp.run() in stdio mode."""
        import workflow_mcp.server as server

        called = {}

        def fake_run(*args, **kwargs):
            called['args'] = args
            called['kwargs'] = kwargs

        with patch.object(server.mcp, 'run', new=fake_run):
            server.main(argv=[])

        self.assertIn('kwargs', called)
        self.assertEqual(called['kwargs'], {})

    def test_runs_http_with_args(self):
        """Providing transport/host/port should forward args to mcp.run."""
        import workflow_mcp.server as server

        captured = {}

        def fake_run(*args, **kwargs):
            captured['args'] = args
            captured['kwargs'] = kwargs

        with patch.object(server.mcp, 'run', new=fake_run):
            argv = [
                "--transport",
                "http",
                "--host",
                "127.0.0.1",
                "--port",
                "8765",
            ]
            server.main(argv=argv)

        self.assertIn('kwargs', captured)
        self.assertEqual(captured['kwargs'].get('transport'), 'http')
        self.assertEqual(captured['kwargs'].get('host'), '127.0.0.1')
        self.assertEqual(captured['kwargs'].get('port'), 8765)


class StepFilenameParsingTests(unittest.TestCase):
    def test_underscore_convention(self):
        from workflow_mcp.steps import _step_id_from_filename

        self.assertEqual(_step_id_from_filename("STEP4a_session_date_inputs.md"), "4a")

    def test_hyphen_convention_still_works(self):
        from workflow_mcp.steps import _step_id_from_filename

        self.assertEqual(_step_id_from_filename("STEP3-foo.md"), "3")

    def test_list_step_guides_underscore_files(self):
        from workflow_mcp.steps import list_step_guides

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            steps_dir = root / "docs" / "steps"
            steps_dir.mkdir(parents=True)
            (steps_dir / "STEP4a_session_date_inputs.md").write_text("# 4a")
            (steps_dir / "STEP4b_session_date_ledger.md").write_text("# 4b")

            rows = list_step_guides(root)

        step_ids = {row["filename"]: row["step_id"] for row in rows}
        self.assertEqual(step_ids["STEP4a_session_date_inputs.md"], "4a")
        self.assertEqual(step_ids["STEP4b_session_date_ledger.md"], "4b")


if __name__ == '__main__':
    unittest.main()
