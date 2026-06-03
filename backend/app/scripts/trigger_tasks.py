import asyncio
from sqlalchemy import select
from app.core.database import async_session_maker
from app.models.models import Document
from app.tasks.document_tasks import process_document_task

async def run():
    async with async_session_maker() as db:
        res = await db.execute(select(Document).where(Document.status.in_(['uploaded', 'error', 'pending'])))
        docs = res.scalars().all()
        print(f"Found {len(docs)} docs to process")
        for d in docs:
            # reset to indexing so it doesn't stay uploaded
            d.status = "uploaded"
            process_document_task.delay(d.id)
            print(f"Enqueued {d.id}")
        await db.commit()

if __name__ == "__main__":
    asyncio.run(run())
