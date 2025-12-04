# CloudHealth FlexReports Backups

Automated backup utility for CloudHealth FlexReports. Downloads all reports across all datasets and packages them into a timestamped zip archive.

## Overview

This script:
- Authenticates to CloudHealth's GraphQL API
- Discovers all available datasets
- Downloads complete report definitions (including SQL, configurations, time ranges)
- Creates a compressed zip archive with all reports
- Cleans up temporary files automatically

## Requirements

- Python 3.6+
- `requests` library

## Installation

```bash
pip install requests
```

## Configuration

The script supports three methods for providing your CloudHealth API key (in priority order):

### 1. Environment Variable (Recommended)

```bash
export CLOUDHEALTH_API_KEY="your-api-key-here"
python backup-flexreports.py
```

### 2. Hardcoded in Script

Edit the script and set the `API_KEY` variable:

```python
API_KEY = "your-api-key-here"
```

### 3. Interactive Prompt

If no API key is found, the script will prompt you to enter it at runtime.

## Usage

Basic usage:

```bash
python backup-flexreports.py
```

The script will:
1. Authenticate with CloudHealth
2. Collect metadata for all FlexReports
3. Download each report with progress indicator
4. Create a zip archive: `FlexReportsBackup_YYYY_MM_DD_HH_MM_SS.zip`
5. Clean up temporary JSON files

### Example Output

```
Using API key from environment variable...
Authenticating...
Authentication successful.
Fetching datasets...
Found 15 dataset(s).

Collecting FlexReports metadata...
Found 46 FlexReport(s). Starting download...

[1/46] Downloaded: Monthly Cost Summary
[2/46] Downloaded: AWS EC2 Usage Report
[3/46] Downloaded: Azure Resource Analysis
...
[46/46] Downloaded: GCP Billing Breakdown

Creating backup archive...
Successfully created 'FlexReportsBackup_2025_12_04_10_30_45.zip' with 46 FlexReport(s).
Cleaning up temporary files...
Temporary JSON files removed.

==================================================
Backup completed successfully!
Total datasets processed: 15
Total reports backed up: 46
Archive file: FlexReportsBackup_2025_12_04_10_30_45.zip
==================================================
```

## Output Format

### Zip Archive Structure

```
FlexReportsBackup_2025_12_04_10_30_45.zip
├── Monthly_Cost_Summary_2025_12_04_10_30_45.json
├── AWS_EC2_Usage_Report_2025_12_04_10_30_45.json
└── ...
```

### Report JSON Contents

Each JSON file contains complete JSON and SQL blob that can be used to restore a FlexReport.  Copy/paste the blob in to the FlexReports editor.

## Exit Codes

- `0`: Success - backup completed without errors
- `1`: Failure - authentication error, network issue, or other problem

Use exit codes in automation scripts:

```bash
python backup-flexreports.py
if [ $? -eq 0 ]; then
    echo "Backup successful"
else
    echo "Backup failed"
fi
```

## Automation

### Scheduled Backups with Cron

Add to your crontab for daily backups at 2 AM:

```bash
0 2 * * * cd /path/to/backups && /usr/bin/python3 backup-flexreports.py >> backup.log 2>&1
```

### Backup Rotation Script

Example script to keep only the last 7 backups:

```bash
#!/bin/bash
cd /path/to/backups
python3 backup-flexreports.py

# Keep only the 7 most recent backups
ls -t FlexReportsBackup_*.zip | tail -n +8 | xargs -r rm
```

## Notes

- The script skips empty datasets automatically
- Report names are sanitized for safe filesystem usage
- Temporary JSON files are created during download and removed after archiving
- The zip archive uses compression to minimize file size
- All HTTP requests include timeouts to prevent hanging

