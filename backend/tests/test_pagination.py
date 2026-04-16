"""Tests for the pagination utility — runs against real async SQLAlchemy with SQLite."""

import pytest
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from utils.pagination import paginate


class Base(DeclarativeBase):
    pass


class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)


class DummySchema:
    """Minimal schema-like class with model_validate for testing."""
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.name = kwargs.get("name")

    @classmethod
    def model_validate(cls, obj):
        return cls(id=obj.id, name=obj.name)


async def _make_session():
    """Create an in-memory SQLite DB with 25 items and return a session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        for i in range(25):
            session.add(Item(id=i + 1, name=f"item-{i + 1:03d}"))
        await session.commit()
    return factory


@pytest.mark.asyncio
class TestPagination:
    async def test_first_page(self):
        factory = await _make_session()
        async with factory() as db:
            result = await paginate(db, select(Item), DummySchema, page=1, per_page=10)
        assert result["total"] == 25
        assert result["page"] == 1
        assert result["per_page"] == 10
        assert len(result["items"]) == 10
        assert result["pages"] == 3

    async def test_middle_page(self):
        factory = await _make_session()
        async with factory() as db:
            result = await paginate(db, select(Item), DummySchema, page=2, per_page=10)
        assert len(result["items"]) == 10
        assert result["page"] == 2

    async def test_last_page_partial(self):
        factory = await _make_session()
        async with factory() as db:
            result = await paginate(db, select(Item), DummySchema, page=3, per_page=10)
        assert len(result["items"]) == 5
        assert result["pages"] == 3

    async def test_beyond_last_page(self):
        factory = await _make_session()
        async with factory() as db:
            result = await paginate(db, select(Item), DummySchema, page=10, per_page=10)
        assert len(result["items"]) == 0
        assert result["total"] == 25

    async def test_single_page_all(self):
        factory = await _make_session()
        async with factory() as db:
            result = await paginate(db, select(Item), DummySchema, page=1, per_page=50)
        assert len(result["items"]) == 25
        assert result["pages"] == 1

    async def test_per_page_one(self):
        factory = await _make_session()
        async with factory() as db:
            result = await paginate(db, select(Item), DummySchema, page=1, per_page=1)
        assert len(result["items"]) == 1
        assert result["pages"] == 25

    async def test_filtered_query(self):
        factory = await _make_session()
        async with factory() as db:
            query = select(Item).where(Item.id <= 5)
            result = await paginate(db, query, DummySchema, page=1, per_page=10)
        assert result["total"] == 5
        assert len(result["items"]) == 5
        assert result["pages"] == 1

    async def test_default_params(self):
        factory = await _make_session()
        async with factory() as db:
            result = await paginate(db, select(Item), DummySchema)
        assert result["page"] == 1
        assert result["per_page"] == 50
        assert len(result["items"]) == 25

    async def test_items_are_validated(self):
        factory = await _make_session()
        async with factory() as db:
            result = await paginate(db, select(Item), DummySchema, page=1, per_page=5)
        for item in result["items"]:
            assert isinstance(item, DummySchema)
            assert item.id is not None
            assert item.name is not None
