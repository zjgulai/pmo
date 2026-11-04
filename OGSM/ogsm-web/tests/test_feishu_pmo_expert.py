"""PMO 飞书专家灵魂大脑、三棒一键交棒与自进化漏斗测试套件（ADR-0009）。

运行：
    OGSM/ogsm-web/.venv/bin/python -m unittest discover -s OGSM/ogsm-web/tests -v
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

WEB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WEB))

os.environ["DATABASE_URL"] = "sqlite:////tmp/ogsm_expert_bot_test.db"

from sqlmodel import Session, select  # noqa: E402
from app import models  # noqa: E402
from app.db import engine  # noqa: E402
from app.feishu_bot import handle_bot_command, process_card_action_event  # noqa: E402
from app.seed import seed  # noqa: E402


class PmoFeishuExpertTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        seed(force_reset=True)

    @classmethod
    def tearDownClass(cls) -> None:
        db_file = Path("/tmp/ogsm_expert_bot_test.db")
        if db_file.exists():
            db_file.unlink()

    def test_1_wuyuning_contract_and_key_question(self) -> None:
        """场景 1：吴雨宁询问跨 Agent 交接主键与二创授权 Gate。"""
        title, md, btns, act_btns = handle_bot_command(
            "Radar 和 Clone 交接达人二创视频时，卡片和表结构必须包含哪几个主键字段？Gate怎么过？"
        )
        self.assertIn("专家诊断", title)
        self.assertIn("creator_id", md)
        self.assertIn("Clone", md)
        self.assertTrue(len(act_btns) >= 1)

    def test_2_zhoujian_reuse_and_dependency_question(self) -> None:
        """场景 2：周健询问 Vicky 研发的现成资产复用与三棒在手状态。"""
        title, md, _, _ = handle_bot_command(
            "我今天开发 Vicky 的飞书Bot和品线回填，目前接棒状态如何？有哪些历史资产可复用？"
        )
        self.assertIn("专家诊断", title)
        self.assertIn("Vicky", md)
        self.assertIn("当前接棒", md)

    def test_3_liuhuali_self_evolution_funnel_query(self) -> None:
        """场景 3：刘华丽查询 Stage 3 高频问题自进化漏斗与业务回写账本。"""
        title, md, _, _ = handle_bot_command("自进化漏斗")
        self.assertIn("自进化漏斗", title)
        self.assertIn("Stage 3", md)
        self.assertIn("measuredActions", md)

    def test_4_brand_dept_triage_and_redline_guard(self) -> None:
        """场景 4：品牌市场部询问单条视频 ROAS 9.0 能否直接加预算（触发 M01 指标误用守门）。"""
        title, md, _, _ = handle_bot_command(
            "这周 TikTok 单条视频 ROAS 跑到了 9.0，能不能直接申请加 5 万美金预算？"
        )
        self.assertIn("专家诊断", title)
        self.assertTrue("M01" in md or "ROAS" in md or "MER" in md)

    def test_5_baton_pass_command_and_card_action(self) -> None:
        """场景 5：三棒一键交棒指令（P1 吴雨宁 25% -> P2 周健 35% -> P3 刘华丽 75%）。"""
        with Session(engine) as s:
            cap = s.exec(
                select(models.CapabilityItem).where(models.CapabilityItem.name == "IP 合作计划制定")
            ).first()
            assert cap is not None
            cap_id = cap.id
            self.assertEqual(cap.progress_pct, 25)

        # 第一次交棒：吴雨宁 (25%) -> 周健 (35%)
        title, md, _, _ = handle_bot_command("交棒 IP 合作计划制定 Schema与飞书卡片原型已定稿")
        self.assertIn("交棒完成", title)
        self.assertIn("@吴雨宁", md)
        self.assertIn("@周健", md)
        self.assertIn("35%", md)

        # 第二次通过卡片按钮免打字交棒：周健 (35%) -> 刘华丽 (75%)
        res = process_card_action_event({"action": "pass_baton", "cap_id": cap_id})
        self.assertIn("@刘华丽", res["toast"]["content"])
        self.assertIn("75%", res["toast"]["content"])


if __name__ == "__main__":
    unittest.main()
