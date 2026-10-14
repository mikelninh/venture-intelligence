"""Privacy-conscious optional Langfuse integration, opt-in only.

Remote telemetry is intentionally disabled by default, including in tests. We only
send counts, stage names and timing, never pitch text, prompts, names, or filenames.
"""
from __future__ import annotations
import os
from .models import Deal


def publish_metadata_only(deal: Deal) -> bool:
    if os.getenv('VI_LANGFUSE_ENABLED') != '1':
        return False
    if not (os.getenv('LANGFUSE_PUBLIC_KEY') and os.getenv('LANGFUSE_SECRET_KEY')):
        return False
    from langfuse import get_client  # optional installation, not required for local app
    client = get_client()
    with client.start_as_current_observation(
        name='venture-intelligence-evidence-pipeline', as_type='span',
        input={'source_pages': deal.page_count, 'synthetic_demo': deal.demo,
               'workflow_engine': deal.workflow_engine}) as root:
        for stage in deal.trace:
            with client.start_as_current_observation(
                as_type='span', name=stage.name, input={'status': stage.status}) as span:
                span.update(output={**stage.details, 'duration_ms': stage.duration_ms})
        root.update(output={'citations_verified': deal.supported_facts,
                            'conflicts': sum(f.status=='conflict' for f in deal.facts.values()),
                            'human_review_required': True})
    return True
