"""数据库连接与会话。"""
import os

from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://ogsm:ogsm@localhost:5432/ogsm"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def init_db() -> None:
    # 导入模型以注册 metadata
    from . import models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
