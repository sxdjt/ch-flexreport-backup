# List All FlexReports

Lists all CloudHealth FlexReports across all datasets and saves to CSV.

## Requirements

- Python 3.6+
- `requests` library

```bash
pip install requests
```

## Usage

```bash
python list-all-flexreports.py
```

The script will:
1. Prompt for your CloudHealth API key
2. Fetch all datasets
3. Retrieve all FlexReports from each dataset
4. Save to `backup-list.csv` (sorted alphabetically by name)

## Output

CSV file with columns:
- name
- id
- createdBy
- dataset_name

## Example

```
$ python list-all-flexreports.py
Enter your CloudHealth API key: ****
Getting all saved FlexReports for all datasets, saving them to backup-list.csv
```

## Notes

- CSV header row is not included in output
- Reports are sorted case-insensitive by name
