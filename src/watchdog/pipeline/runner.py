import argparse
import asyncio
import sys
import time
from pathlib import Path

import structlog

from watchdog.config import settings
from watchdog.logging import setup_logging

log = structlog.get_logger()

STEPS = ["download", "ocr", "chunk", "embed", "triage"]


async def run_step(
    step: str,
    limit: int | None = None,
    archive_path: Path | None = None,
) -> dict:
    """Run a single pipeline step."""
    log.info("step_starting", step=step, limit=limit)
    start = time.time()

    if step == "download":
        from watchdog.pipeline.downloader import run_download
        result = await run_download(
            limit=limit or settings.download_limit,
            archive_dir=archive_path,
        )

    elif step == "ocr":
        from watchdog.pipeline.ocr import run_ocr
        count = await run_ocr(limit=limit)
        result = {"documents_ocrd": count}

    elif step == "chunk":
        from watchdog.pipeline.chunker import run_chunking
        count = await run_chunking(limit=limit)
        result = {"chunks_created": count}

    elif step == "embed":
        from watchdog.services.embedding import run_embeddings
        count = await run_embeddings()
        result = {"embeddings_created": count}

    elif step == "triage":
        from watchdog.pipeline.triage import run_triage
        result = await run_triage(limit=limit)

    else:
        raise ValueError(f"Unknown step: {step}")

    elapsed = round(time.time() - start, 1)
    log.info("step_complete", step=step, elapsed_seconds=elapsed, result=result)
    return {"step": step, "elapsed_seconds": elapsed, **result}


async def run_pipeline(
    steps: list[str] | None = None,
    limit: int | None = None,
    archive_path: Path | None = None,
) -> list[dict]:
    """Run the full pipeline or specific steps."""
    steps = steps or STEPS
    results = []

    for step in steps:
        if step not in STEPS:
            log.error("unknown_step", step=step, valid=STEPS)
            continue
        try:
            result = await run_step(step, limit=limit, archive_path=archive_path)
            results.append(result)
        except Exception as e:
            log.error("step_failed", step=step, error=str(e))
            results.append({"step": step, "error": str(e)})

    return results


def main():
    parser = argparse.ArgumentParser(description="Watchdog Document Analysis Pipeline")
    parser.add_argument(
        "--step",
        choices=STEPS + ["all"],
        default="all",
        help="Pipeline step to run (default: all)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of documents to process",
    )
    parser.add_argument(
        "--archive-path",
        type=Path,
        default=None,
        help="Path to local document archive (overrides ARCHIVE_DIR in .env)",
    )

    args = parser.parse_args()
    setup_logging()

    steps = STEPS if args.step == "all" else [args.step]

    log.info("pipeline_starting", steps=steps, limit=args.limit, archive_path=str(args.archive_path))
    results = asyncio.run(run_pipeline(steps=steps, limit=args.limit, archive_path=args.archive_path))

    print("\n=== Pipeline Results ===")
    for r in results:
        step = r.pop("step", "?")
        error = r.pop("error", None)
        if error:
            print(f"  {step}: FAILED - {error}")
        else:
            elapsed = r.pop("elapsed_seconds", 0)
            print(f"  {step}: OK ({elapsed}s) {r}")

    if any("error" in r for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
