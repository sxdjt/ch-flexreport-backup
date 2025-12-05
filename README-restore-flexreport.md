# Restore FlexReport

Restores a single CloudHealth FlexReport from a JSON backup file.

## Requirements

- Python 3.6+
- `requests` library

```bash
pip install requests
```

## Usage

### With filename argument

```bash
python restore-flexreport.py report_name_2025_12_04_10_30_45.json
```

### Interactive prompt

```bash
python restore-flexreport.py
Enter the JSON filename: report_name_2025_12_04_10_30_45.json
```

## Behavior

The script will:
1. Prompt for your CloudHealth API key
2. Read the JSON backup file
3. Create a new FlexReport with " RESTORED FROM BACKUP" appended to the name
4. Display the created report ID

## Example

```
$ python restore-flexreport.py Monthly_Cost_Summary_2025_12_04.json
Enter your CloudHealth API key: ****
Full GraphQL Request:
{
  "query": "mutation CreateFlexReport...",
  ...
}
FlexReport created successfully!
FlexReport ID: abc123
```

## Limitations

- Only restores basic FlexReport fields (name, description, SQL, data granularity, limit, timeRange.last)
- Does not restore: from/to timeRange values, excludeCurrent flag, or notification settings
- Original report name is used as description
- " RESTORED FROM BACKUP" is always appended to prevent name conflicts

## Exit Codes

- 0: Success
- 1: Failure (file not found, API error, etc.)
