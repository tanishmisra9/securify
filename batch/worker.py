"""
Securify batch worker.

Start Redis: redis-server
Start worker: celery -A batch.worker worker --loglevel=info

Submit a batch job via POST /api/batch/submit with a .zip file.
Poll status via GET /api/batch/{job_id}
"""
from __future__ import annotations

from pathlib import Path

from celery import Celery

app = Celery('securify', broker='redis://localhost:6379/0',
             backend='redis://localhost:6379/0')

app.conf.update(task_serializer='json', result_serializer='json',
                accept_content=['json'])


@app.task(bind=True)
def process_batch(self, job_id: str, file_paths: list[str]) -> dict:
    from pipeline.chunker import chunk_text
    from pipeline.ingestor import extract_text
    from pipeline.redactor import redact

    results = []
    total = len(file_paths)

    for i, fpath in enumerate(file_paths):
        try:
            text = extract_text(fpath)
            result = redact(text)
            chunks = chunk_text(result.redacted_text)
            results.append({
                "filename": Path(fpath).name,
                "status": "ok",
                "total_entities": sum(result.entity_counts.values()),
                "entity_counts": result.entity_counts,
                "chunks_count": len(chunks),
            })
        except Exception as e:
            results.append({
                "filename": Path(fpath).name,
                "status": "error",
                "error": str(e),
            })

        self.update_state(
            state='PROGRESS',
            meta={'current': i + 1, 'total': total, 'results': results}
        )

    return {
        'current': total, 'total': total,
        'results': results,
        'summary': {
            'processed': sum(1 for r in results if r['status'] == 'ok'),
            'errors': sum(1 for r in results if r['status'] == 'error'),
            'total_entities_redacted': sum(
                r.get('total_entities', 0) for r in results
            ),
        }
    }
