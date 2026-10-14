#!/usr/bin/env python3
"""Opt-in live Gemini OCR QA for clearly fictional PDFs. Provider quota may be used."""
import argparse
import json
import random
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path

SAMPLES = [
    ('fictional_aadhaar.pdf', 'Rahul Kumar Sharma', '2000-05-12'),
    ('fictional_pan.pdf', 'Rahul K Sharma', '2000-05-12'),
    ('fictional_birth_certificate.pdf', 'Rahul Kumar Sharma', '2000-05-12'),
]
RETRYABLE_HTTP = {408, 429, 500, 502, 503, 504}

def multipart_pdf(path):
    boundary = 'maadhyam-fictional-ocr-qa-boundary'
    body = (
        f'--{boundary}\r\n'
        'Content-Disposition: form-data; name="fictional_document_confirmed"\r\n\r\n'
        'true\r\n'
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
        'Content-Type: application/pdf\r\n\r\n'
    ).encode() + path.read_bytes() + f'\r\n--{boundary}--\r\n'.encode()
    return body, f'multipart/form-data; boundary={boundary}'

def load_previous(report_path):
    if not report_path.exists():
        return {}
    try:
        report = json.loads(report_path.read_text(encoding='utf-8'))
        return {r['file']: r for r in report.get('results', []) if r.get('status') == 'PASS'}
    except (OSError, ValueError, KeyError, TypeError):
        return {}

def extract_once(api, path, timeout):
    body, ctype = multipart_pdf(path)
    request = urllib.request.Request(
        api.rstrip('/') + '/api/ai/extract-document', body,
        {'Content-Type': ctype}, method='POST',
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, json.loads(response.read())

def run_sample(api, path, expected_name, expected_dob, timeout, retries, backoff):
    started = time.monotonic()
    for attempt in range(1, retries + 2):
        retryable = False
        try:
            status, result = extract_once(api, path, timeout)
            name = (result.get('printedName') or '').strip()
            dob = result.get('dateOfBirth')
            ok = status == 200 and name == expected_name and dob == expected_dob
            return {
                'file': path.name, 'status': 'PASS' if ok else 'FAIL', 'http': status,
                'extractedName': name, 'extractedDOB': dob,
                'expectedName': expected_name, 'expectedDOB': expected_dob,
                'warnings': result.get('warnings', []), 'attempts': attempt,
                'elapsedSeconds': round(time.monotonic() - started, 2),
                'errorType': None if ok else 'extraction_mismatch',
            }
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode('utf-8', 'replace')[:500]
            retryable = exc.code in RETRYABLE_HTTP or ('temporarily busy' in detail.lower())
            record = {'file': path.name, 'status': 'FAIL', 'http': exc.code,
                      'errorType': 'http_error', 'error': detail}
        except (TimeoutError, socket.timeout) as exc:
            retryable = True
            record = {'file': path.name, 'status': 'FAIL', 'errorType': 'timeout',
                      'error': str(exc) or 'Timed out'}
        except urllib.error.URLError as exc:
            reason = exc.reason
            retryable = isinstance(reason, (TimeoutError, socket.timeout))
            record = {'file': path.name, 'status': 'FAIL', 'errorType': 'network_error',
                      'error': str(exc)[:500]}
        except (ValueError, OSError) as exc:
            record = {'file': path.name, 'status': 'FAIL', 'errorType': 'response_or_io_error',
                      'error': str(exc)[:500]}
        if not retryable or attempt > retries:
            record.update(attempts=attempt, elapsedSeconds=round(time.monotonic()-started, 2))
            return record
        delay = backoff * (2 ** (attempt-1)) + random.uniform(0, 0.3)
        print(f'RETRY {path.name}: attempt {attempt}/{retries+1} failed ({record["errorType"]}); waiting {delay:.1f}s', flush=True)
        time.sleep(delay)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--allow-live-gemini', action='store_true', help='Authorize sending fictional PDFs to Gemini')
    parser.add_argument('--api', default='http://127.0.0.1:8000')
    parser.add_argument('--report', default='live-gemini-ocr-results.json')
    parser.add_argument('--files', nargs='+', choices=[sample[0] for sample in SAMPLES],
                        help='Run only selected fictional PDFs')
    parser.add_argument('--resume', action='store_true', help='Skip files previously marked PASS in report')
    parser.add_argument('--timeout', type=float, default=120, help='HTTP timeout per attempt (seconds)')
    parser.add_argument('--retries', type=int, default=2, help='Additional attempts for temporary failures')
    parser.add_argument('--backoff', type=float, default=3, help='Initial retry delay (seconds)')
    args = parser.parse_args()
    if not args.allow_live_gemini:
        print('SKIP: add --allow-live-gemini to explicitly authorize fictional document uploads.')
        return 0
    if args.timeout <= 0 or args.retries < 0 or args.backoff < 0:
        parser.error('--timeout must be positive; --retries and --backoff must be nonnegative')
    report_path = Path(args.report)
    previous = load_previous(report_path) if args.resume else {}
    chosen = [s for s in SAMPLES if args.files is None or s[0] in args.files]
    results = []
    for filename, expected_name, expected_dob in chosen:
        if filename in previous:
            record = {**previous[filename], 'skippedPreviouslyPassed': True}
            print('SKIP previously passed', filename, flush=True)
        else:
            path = Path(__file__).resolve().parent / 'fictional_docs' / filename
            if not path.is_file():
                record = {'file': filename, 'status': 'FAIL', 'errorType': 'missing_file', 'error': str(path)}
            else:
                record = run_sample(args.api, path, expected_name, expected_dob,
                                    args.timeout, args.retries, args.backoff)
            print(record['status'], filename, record.get('error', ''), flush=True)
        results.append(record)
        # Save after each document so interrupted runs can resume.
        report = {'suite': 'LIVE GEMINI OCR — fictional PDFs', 'results': results,
                  'passed': sum(r['status']=='PASS' for r in results),
                  'failed': sum(r['status']=='FAIL' for r in results)}
        report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f'{report["passed"]} passed, {report["failed"]} failed; {report_path.resolve()}')
    return 1 if report['failed'] else 0

if __name__ == '__main__':
    raise SystemExit(main())
