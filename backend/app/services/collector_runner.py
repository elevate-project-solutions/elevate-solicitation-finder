import logging

from app.collectors.base import BaseCollector, CollectionResult

logger = logging.getLogger(__name__)

def run_collector(
        collector: BaseCollector,
) -> CollectionResult:
    """
    Runs a collector with consistent logging
    
    Raises collection errors so callers can decide
    whether to retry an entire import
    """

    source_name = collector.source_name

    logger.info(
        "Starting collector source=%s",
        source_name,
    )

    try:
        result = collector.run()

    except Exception:
        logger.exception(
            "Collector failed source=%s",
            source_name,
        )
        raise

    logger.info(
        "Collector completed source=%s collected=%s",
        source_name,
        result.total_collected,
    )

    return result