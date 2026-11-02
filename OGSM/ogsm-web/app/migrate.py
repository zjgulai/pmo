"""迁移链：按顺序跑，全部幂等。

生产容器启动时执行 `python -m app.migrate`，替代原来只跑 seed 的写法。
每一步都设计成可重复执行——重启容器不会重复写数据，也不会因为某一步已存在而整体失败。
"""
import importlib
import traceback

STEPS = [
    ("seed", "app.seed"),                                   # O/G/S/M 结构（库为空时写入）
    ("0002_geo_object_a", "app.migrate_0002_geo_object_a"),  # GEO 对象级 A
    ("0003_experts", "app.migrate_0003_experts"),            # 专家映射
    ("0004_s06", "app.migrate_0004_s06_and_exclusions"),     # S0.6 知识生产 + 范围排除
    ("0005_order_sku", "app.migrate_0005_order_sku_priority"),  # order_id/sku_id 提级
    ("0006_baselines", "app.migrate_0006_baselines"),        # 基线台账
]


def main() -> None:
    print(f"[migrate] 共 {len(STEPS)} 步")
    ok = 0
    for name, modpath in STEPS:
        try:
            mod = importlib.import_module(modpath)
            fn = getattr(mod, "migrate", None) or getattr(mod, "seed", None)
            if fn is None:
                print(f"[migrate] {name}: 无 migrate()/seed() 入口，跳过")
                continue
            print(f"[migrate] ── {name} ──")
            fn()
            ok += 1
        except Exception:
            # 迁移失败必须整链中断：带着残缺 schema 起服务比不起更危险
            print(f"[migrate] ✗ {name} 失败，整链中断")
            traceback.print_exc()
            raise SystemExit(1)
    print(f"[migrate] 完成 {ok}/{len(STEPS)} 步")


if __name__ == "__main__":
    main()
