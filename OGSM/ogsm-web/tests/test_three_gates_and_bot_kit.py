"""P0-4 三道 Gate 状态机守卫回执引擎与 P0-2 14 专家飞书 Bot 脚手架单元测试（ADR-0010）。

运行：
    OGSM/ogsm-web/.venv/bin/python -m unittest discover -s OGSM/ogsm-web/tests -v
"""
from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

WEB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WEB))

os.environ["DATABASE_URL"] = "sqlite:////tmp/ogsm_three_gates_test.db"

import os as _os2
_os2.environ["DATABASE_URL"] = "sqlite:////tmp/ogsm_three_gates_test.db"

from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import Session  # noqa: E402

from app.abi_feishu_agent_kit import ABIFeishuAgentBot, list_expert_bot_scaffold_status  # noqa: E402
from app.db import engine  # noqa: E402
from app.feishu_bot import handle_bot_command, process_card_action_event  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import seed  # noqa: E402


class ThreeGatesAndBotKitTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        seed(force_reset=True)
        cls.client = TestClient(app)

    def test_1_claim_gate_pass_and_block(self) -> None:
        """测试 Claim Gate (C)：要件齐全且无红线词 PASS；缺证据或含医疗越界词 BLOCK。"""
        # 1a. PASS case
        r_pass = self.client.post(
            "/api/gate/evaluate",
            json={
                "gate_type": "C",
                "subject_id": "scr-test-m5-001",
                "subject_version": 1,
                "content_text": "Momcozy M5 轻音吸奶器，符合 FDA 食品接触级硅胶测试",
                "claim_refs": ["clm-m5-fda@1"],
                "evidence_refs": ["evd-sgs-001@1"],
                "rule_refs": ["rule-momcozy-baby-fda-84@1"],
                "market_overlay_version": "overlay-us-ftc-fda@1",
            },
        ).json()
        self.assertTrue(r_pass["ok"])
        self.assertEqual(r_pass["verdict"], "PASS")
        self.assertEqual(r_pass["receipt_id"], "scr-test-m5-001@1#C-0001")

        # 1b. BLOCK case (medical redline word + missing evidence)
        r_blk = self.client.post(
            "/api/gate/evaluate",
            json={
                "gate_type": "C",
                "subject_id": "scr-test-m5-001",
                "subject_version": 1,
                "content_text": "医疗级 100%杀菌 治愈乳腺炎",
                "claim_refs": ["clm-m5-med@1"],
                "evidence_refs": [],
                "rule_refs": ["rule-claim-cosmetic-medical-boundary-us-review@3"],
                "market_overlay_version": "overlay-us-ftc-fda@1",
            },
        ).json()
        self.assertEqual(r_blk["verdict"], "BLOCK")
        self.assertEqual(r_blk["receipt_id"], "scr-test-m5-001@1#C-0002")

        # 1c. 旧版本 C-0001 应已被自动置为 superseded
        v_old = self.client.post("/api/gate/verify", json={"receipt_id": "scr-test-m5-001@1#C-0001"}).json()
        self.assertFalse(v_old["valid"])
        self.assertEqual(v_old["status"], "superseded")

    def test_2_rights_gate_reedit_and_whitelist(self) -> None:
        """测试授权 Gate (A)：二次剪辑缺 reedit 或非白名单凭证必须 BLOCK。"""
        r_reedit_blk = self.client.post(
            "/api/gate/evaluate",
            json={
                "gate_type": "A",
                "subject_id": "ast-remix-99",
                "subject_version": 1,
                "creator_id": "crt-us-01@1",
                "credential_type": "ttam_spark_code",
                "scope": ["organic", "paid"],  # 缺 reedit
                "account_ids": ["ttUS-Official"],
                "territory": ["US"],
                "is_reedit": True,
            },
        ).json()
        self.assertEqual(r_reedit_blk["verdict"], "BLOCK")

        r_reedit_pass = self.client.post(
            "/api/gate/evaluate",
            json={
                "gate_type": "A",
                "subject_id": "ast-remix-99",
                "subject_version": 2,
                "creator_id": "crt-us-01@1",
                "credential_type": "ttam_spark_code",
                "scope": ["organic", "paid", "reedit"],
                "account_ids": ["ttUS-Official"],
                "territory": ["US"],
                "is_reedit": True,
            },
        ).json()
        self.assertEqual(r_reedit_pass["verdict"], "PASS")

    def test_3_experiment_gate_hypothesis_and_multi_arm(self) -> None:
        """测试实验 Gate (X)：预注册发号 hyp-yyMMdd-seq3 + >5臂强制多重比较校正。"""
        h = self.client.post(
            "/api/gate/hypothesis",
            json={"statement": "若将吸奶器痛点前置到前2秒则完播率提升15%"},
        ).json()
        self.assertTrue(h["ok"])
        self.assertTrue(h["hypothesis_id"].startswith("hyp-"))

        # 8 臂未声明校正方法 -> BLOCK
        r_exp_blk = self.client.post(
            "/api/gate/evaluate",
            json={
                "gate_type": "X",
                "subject_id": "exp-8arms-01",
                "subject_version": 1,
                "hypothesis_id": h["hypothesis_id"],
                "changed_variables": ["hook_2s"],
                "control_variant_id": "ctrl-01",
                "arm_count": 8,
                "correction_method": "",
            },
        ).json()
        self.assertEqual(r_exp_blk["verdict"], "BLOCK")

    def test_4_feishu_bot_kit_and_commands(self) -> None:
        """测试 P0-2 14 专家 Bot 脚手架、草案审批回写与飞书 @PMO 查回执/发号指令。"""
        kits = list_expert_bot_scaffold_status()
        self.assertEqual(len(kits), 14)

        bot = ABIFeishuAgentBot("shopify")
        card = bot.build_standard_draft_review_card(
            draft_title="Momcozy M5 独立站 PDP 五点优化草稿",
            draft_summary="基于 Echo 高频静音原话与 84 条母婴规则预检生成的 DRAFT",
            receipt_id="scr-bpc-tiktok-00317@2#C-0001",
        )
        self.assertIn("PASS", json.dumps(card, ensure_ascii=False))

        # 模拟品牌市场部点击卡片「批准采纳」按钮 -> 自动记入 measuredActions
        toast_res = process_card_action_event(
            {
                "action": "bot_approve_draft",
                "slug": "shopify",
                "title": "M5 PDP DRAFT #01",
                "receipt_id": "scr-bpc-tiktok-00317@2#C-0001",
            }
        )
        self.assertIn("measuredActions+1", toast_res["toast"]["content"])

        # 测试飞书指令 @PMO 查回执 & @PMO 发号
        t1, md1, _, _ = handle_bot_command("查回执 scr-bpc-tiktok-00317@2#C-0001")
        self.assertIn("PASS", md1)
        self.assertIn("允许迁移", md1)

        t2, md2, _, _ = handle_bot_command("发号 若将独立站KOL落地页第三方脚本削减50%则加购率提升12%")
        self.assertIn("发号成功", t2)
        self.assertIn("hyp-", md2)


if __name__ == "__main__":
    unittest.main()
