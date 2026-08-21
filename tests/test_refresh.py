#!/usr/bin/env python3
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_hub.refresh import collector_path


class RefreshAdapterTest(unittest.TestCase):
    def test_discovers_user_local_collector_without_shell_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            collector = home / ".local/bin/agent-hub-collect"
            collector.parent.mkdir(parents=True)
            collector.write_text("#!/bin/sh\nexit 0\n")
            collector.chmod(0o755)
            with patch.dict(os.environ, {"HOME": str(home), "PATH": "/usr/bin"}, clear=True):
                self.assertEqual(collector_path(), str(collector))


if __name__ == "__main__":
    unittest.main()
