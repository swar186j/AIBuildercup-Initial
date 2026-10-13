"""Single-run job suitable for Cloud Run Jobs + Cloud Scheduler (once daily)."""
import json
import os
from .passport_source_monitor import check


def main():
    if os.getenv('MAADHYAM_PASSPORT_SOURCE_STATE', '').startswith('gs://'):
        # Cloud Run Job must use persistent GCS state, never ephemeral local files.
        if not os.getenv('MAADHYAM_PASSPORT_SOURCE_VERSIONS', '').startswith('gs://'):
            raise RuntimeError('GCS version-history path required for cloud sync')
        if not os.getenv('MAADHYAM_PASSPORT_SOURCE_SNAPSHOTS', '').startswith('gs://'):
            raise RuntimeError('GCS full-text snapshots path required for cloud sync')
        if not os.getenv('MAADHYAM_PASSPORT_APPROVED_BASELINES', '').startswith('gs://'):
            raise RuntimeError('GCS approved-baselines path required for cloud sync')
    result = check()
    print(json.dumps({'job': 'passport-daily-sync', 'overall': result['overall'],
                      'source_count': len(result['sources'])}))
    # A review-required state is a valid sync run; job must not retry indefinitely.
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
