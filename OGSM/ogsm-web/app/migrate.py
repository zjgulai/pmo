"""V2 数据初始化与迁移入口。

生产容器启动时执行 `python -m app.migrate`：
- 若 `product_project` 表为空或不足 14 个产品项目，自动写入完整 V2 数据
- 已存在 14 个产品项目时保持后台已修改的状态，不覆盖手工改动
"""
from sqlmodel import Session, SQLModel, select

from .db import engine
from .models import ProductProject
from .seed import seed


def main() -> None:
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        count = len(s.exec(select(ProductProject)).all())
    if count < 14:
        print(f"[migrate] 当前产品项目数 {count} < 14，执行 V2 全量初始化")
        seed(force_reset=True)
    else:
        print(f"[migrate] 已存在 {count} 个产品项目，保留现有数据")


if __name__ == "__main__":
    main()
