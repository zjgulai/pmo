"""一次性整理脚本：删除 seed() 里内联的专家块，改调 seed_experts()。

背景：2026-11-02 新增专家映射时，数据被写进了两处（seed_experts() 与 seed() 内联），
两份会漂移。本脚本保留 seed_experts() 作为唯一真源。

幂等：已经整理过则跳过。
"""
import pathlib

MARK = "# 专家 × OGSM 映射（来源：reports/ 九份成果总结，2026-10-31 ~ 11-02）"
REPLACEMENT = [
    "        # 专家 × OGSM 映射统一由 seed_experts() 提供，避免两份数据漂移",
    "        seed_experts(s)",
]


def main() -> None:
    p = pathlib.Path("app/seed.py")
    lines = p.read_text().splitlines()

    if MARK not in "\n".join(lines):
        print("[tidy] 已整理过，跳过")
        return

    start = next(i for i, l in enumerate(lines) if MARK in l)
    # 从 start 往后找 "s.add_all(" 之后的 "]" + ")" 结束
    add_all = next(i for i in range(start, len(lines)) if lines[i].strip() == "s.add_all(")
    end = next(i for i in range(add_all, len(lines))
               if lines[i].strip() == "]" and lines[i + 1].strip() == ")")

    removed = end + 2 - start
    lines[start:end + 2] = REPLACEMENT
    p.write_text("\n".join(lines) + "\n")
    print(f"[tidy] 删除内联专家块 {removed} 行，改为调用 seed_experts(s)")


if __name__ == "__main__":
    main()
