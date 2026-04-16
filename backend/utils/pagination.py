from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession


async def paginate(db: AsyncSession, query, schema_class, page: int = 1, per_page: int = 50):
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    result = await db.execute(query.offset((page - 1) * per_page).limit(per_page))
    items = result.scalars().all()

    return {
        "items": [schema_class.model_validate(item) for item in items],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": max(1, (total + per_page - 1) // per_page),
    }
