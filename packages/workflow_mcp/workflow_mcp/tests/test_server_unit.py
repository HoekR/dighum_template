import sys
import types
import unittest
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


if __name__ == '__main__':
    unittest.main()
