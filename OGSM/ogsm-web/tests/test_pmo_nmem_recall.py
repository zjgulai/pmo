"""PMO nmem 读侧 Recall 测试：真实检索 + 超时/离线降级。

运行：
    OGSM/ogsm-web/.venv/bin/python -m unittest discover -s OGSM/ogsm-web/tests -v
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

WEB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WEB))

from app.memory import recall_durable_memories  # noqa: E402


class RecallDegradationTest(unittest.TestCase):
    def test_empty_query_returns_empty(self):
        self.assertEqual(recall_durable_memories(""), "")
        self.assertEqual(recall_durable_memories("   "), "")

    def test_timeout_returns_empty(self):
        with mock.patch("app.memory.subprocess.run",
                        side_effect=subprocess.TimeoutExpired(cmd="nmem", timeout=3)):
            self.assertEqual(recall_durable_memories("G1 结算指标"), "")

    def test_offline_returns_empty(self):
        with mock.patch.dict(os.environ, {"NMEM_CLI_PATH": "/nonexistent/nmem-bin"}):
            self.assertEqual(recall_durable_memories("G1 结算指标"), "")

    def test_bad_json_returns_empty(self):
        fake = mock.Mock(returncode=0, stdout="not-json")
        with mock.patch("app.memory.subprocess.run", return_value=fake):
            self.assertEqual(recall_durable_memories("G1 结算指标"), "")

    def test_low_score_filtered(self):
        payload = {"memories": [{"title": "低分记忆", "content": "x", "score": 0.1}]}
        fake = mock.Mock(returncode=0, stdout=json.dumps(payload))
        with mock.patch("app.memory.subprocess.run", return_value=fake):
            self.assertEqual(recall_durable_memories("G1 结算指标", min_score=0.5), "")

    def test_high_score_returned(self):
        payload = {"memories": [{"title": "G1", "content": "CAC 口径", "score": 0.88}]}
        fake = mock.Mock(returncode=0, stdout=json.dumps(payload))
        with mock.patch("app.memory.subprocess.run", return_value=fake):
            out = recall_durable_memories("G1 结算指标")
        self.assertIn("G1", out)
        self.assertIn("0.88", out)


@unittest.skipUnless(shutil.which("nmem"), "nmem CLI 不在 PATH，跳过真实检索")
class RealRecallTest(unittest.TestCase):
    def test_real_recall_g1(self):
        out = recall_durable_memories("G1 的结算指标是什么", limit=3, min_score=0.5)
        self.assertTrue(out, "真实检索应返回非空；确认 nmem 服务与 abi-pmo 空间可用")
        self.assertIn("G1", out)

    def test_real_recall_redlines(self):
        out = recall_durable_memories("PMO 的操作红线有哪些", limit=3, min_score=0.5)
        self.assertTrue(out)
        self.assertIn("红线", out)

    def test_cross_space_isolation(self):
        out = recall_durable_memories("G1 的结算指标是什么", limit=3,
                                      min_score=0.5, space="default")
        # Default 空间不应返回 abi-pmo 的 canonical 记忆 id
        self.assertNotIn("pmo-l2-g1g3", out)


if __name__ == "__main__":
    unittest.main()
