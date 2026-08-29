# Phase 2 Summary

Phase 2 adds the QMS application layer for database traceability, dashboard monitoring, manual review, image previews, backend APIs, and database-backed reports.

## Scope

Phase 2 includes:

- Local MySQL database setup
- Product and inspection record tables
- Database logging from realtime inspection
- Flask backend API
- QMS dashboard overview page
- Product, date range, result, and status filters
- Recent inspection records
- Saved inspection image previews
- UNCERTAIN case review workflow
- Manual review details
- Original AI decision and final human decision preservation
- Database-backed text and HTML report generation

## Database Setup

Phase 2 uses a local MySQL database named:

```text
vision_inspection_qms
```

Configure credentials with environment variables or `.env`:

```powershell
$env:DB_HOST="127.0.0.1"
$env:DB_PORT="3306"
$env:DB_USER="root"
$env:DB_PASSWORD="your_password"
$env:DB_NAME="vision_inspection_qms"
```

Initialize or update the schema:

```powershell
python init_database.py
```

This creates or updates:

```text
products
inspection_records
```

## Backend API Setup

Start the API server:

```powershell
python api.py
```

Base URL:

```text
http://127.0.0.1:5000
```

Useful endpoints:

```text
GET /api/health
GET /api/inspection-records
GET /api/inspection-records/recent
GET /api/inspection-records/summary
GET /inspection-records/<record_id>/image
```

The records and summary endpoints support filters:

```text
product
product_name
result
status
start_date
end_date
limit
offset
```

## Dashboard Flow

Open the dashboard:

```text
http://127.0.0.1:5000/dashboard
```

The dashboard shows:

- Total inspections
- OK count
- NOT OK count
- UNCERTAIN count
- Rejection percentage
- Uncertain percentage
- Recent inspection records
- Saved image previews when image files are available

Filter examples:

```text
http://127.0.0.1:5000/dashboard?product=parle_biscuit_v2
http://127.0.0.1:5000/dashboard?product=parle_biscuit_v2&result=NOT%20OK
http://127.0.0.1:5000/dashboard?status=FAIL
http://127.0.0.1:5000/dashboard?product=parle_biscuit_v2&start_date=2026-06-07&end_date=2026-06-07
```

## UNCERTAIN Review Workflow

Open the review page:

```text
http://127.0.0.1:5000/review
```

Product-wise review:

```text
http://127.0.0.1:5000/review?product=<product_name>
```

The review workflow:

1. Lists pending records where the original AI result is `UNCERTAIN`.
2. Shows the saved inspection image when available.
3. Shows prediction, confidence, product, and inspected timestamp.
4. Allows the user to enter reviewer name and review notes.
5. Allows the user to mark final decision as `OK` or `NOT OK`.
6. Stores review timestamp.
7. Removes reviewed records from the pending review list.

The original AI decision remains stored in:

```text
result
status
prediction
confidence
```

The manual review decision is stored separately in:

```text
final_decision
reviewed_status
reviewed_by
review_notes
reviewed_at
```

## Realtime Database Logging

Run realtime inspection with database logging:

```powershell
python live_inspection.py --product <product_name>
```

To disable database logging:

```powershell
python live_inspection.py --product <product_name> --disable-db-log
```

Automatic stable decision changes save annotated images for traceability. These image paths are stored in the database and used by the dashboard and review pages.

## Database Report Generation

Generate a report from database records:

```powershell
python generate_report.py --product <product_name> --source db
```

Generate a date-wise report:

```powershell
python generate_report.py --product <product_name> --source db --start-date YYYY-MM-DD --end-date YYYY-MM-DD
```

Report outputs:

```text
products/<product_name>/outputs/inspection_report.txt
products/<product_name>/outputs/inspection_report.html
```

Database reports use final human review decisions when available. If a record has not been reviewed, the report uses the original AI decision.

## Phase 2 Status

Phase 2 currently supports database storage, API access, dashboard monitoring, filtered inspection views, image previews, UNCERTAIN review, manual review audit fields, and database-backed reporting.

The next major improvement area is Phase 3: stronger AI/ML model training and better defect classification robustness.
