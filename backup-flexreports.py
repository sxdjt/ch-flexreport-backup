"""
CloudHealth FlexReports Backup Script

Author: Dean Tabor - CloudHealth Professional Services (dean.tabor@arrow.com)

This script authenticates to the CloudHealth API, retrieves all FlexReports across
all available datasets, downloads each report as JSON, and packages them into a
timestamped zip file for backup purposes.

Requirements:
    - requests library (pip install requests)
    - Valid CloudHealth API key

Configuration (in order of priority):
    1. Environment variable: Set CLOUDHEALTH_API_KEY (recommended for security)
    2. Hardcoded: Set API_KEY variable below (less secure)
    3. Interactive: Script will prompt for API key at runtime

Output:
    - FlexReportsBackup_YYYY_MM_DD_HH_MM_SS.zip containing all FlexReports

Exit Codes:
    - 0: Success
    - 1: Failure (authentication error, network error, etc.)
"""

import os
import sys
import json
import requests
import zipfile
from datetime import datetime

# API Configuration Constants
CLOUDHEALTH_API_URL = 'https://apps.cloudhealthtech.com/graphql'

# Configuration: Set your API key here to avoid prompting
# Example: API_KEY = "YOUR-API-KEY-HERE"
# Better practice: Set CLOUDHEALTH_API_KEY environment variable instead

API_KEY = ""


def get_api_key():
    """
    Get the API key from environment variable, hardcoded variable, or user prompt.
    Priority: 1) Environment variable, 2) Hardcoded, 3) User input

    Returns:
        str: CloudHealth API key
    """
    # First check environment variable
    env_key = os.environ.get('CLOUDHEALTH_API_KEY')
    if env_key and env_key.strip():
        print("Using API key from environment variable...")
        return env_key

    # Fall back to hardcoded key
    if API_KEY and API_KEY.strip():
        print("Using hardcoded API key...")
        return API_KEY

    # Finally, prompt the user
    return input("Enter your CloudHealth API key: ")


def authenticate_api(api_key):
    """
    Authenticate to the CloudHealth GraphQL API and retrieve an access token.

    Args:
        api_key (str): CloudHealth API key

    Returns:
        str: Bearer access token for subsequent API requests

    Raises:
        requests.exceptions.RequestException: If authentication fails
        KeyError: If response structure is unexpected
    """
    login_query = {
        "query": """
            mutation Login($apiKey: String!) {
                loginAPI(apiKey: $apiKey) {
                    accessToken
                }
            }
        """,
        "variables": {"apiKey": api_key}
    }

    try:
        response = requests.post(CLOUDHEALTH_API_URL, json=login_query, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Validate response structure
        if 'data' not in data or 'loginAPI' not in data['data']:
            raise ValueError("Unexpected API response structure during authentication")

        return data['data']['loginAPI']['accessToken']

    except requests.exceptions.RequestException as e:
        raise Exception(f"Authentication request failed: {str(e)}")
    except (KeyError, ValueError) as e:
        raise Exception(f"Failed to parse authentication response: {str(e)}")


def get_datasets(access_token):
    """
    Retrieve all available datasets from CloudHealth.

    Args:
        access_token (str): Bearer token from authentication

    Returns:
        list: List of dataset dictionaries containing datasetName

    Raises:
        requests.exceptions.RequestException: If the request fails
        ValueError: If response structure is unexpected
    """
    datasets_query = {
        "query": "query queryReq { dataSources { datasetName } }",
        "variables": {}
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "application/json",
        "Connection": "keep-alive"
    }

    try:
        response = requests.post(CLOUDHEALTH_API_URL, json=datasets_query,
                               headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Validate response structure
        if 'data' not in data or 'dataSources' not in data['data']:
            raise ValueError("Unexpected API response structure when fetching datasets")

        return data['data']['dataSources']

    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch datasets: {str(e)}")
    except (KeyError, ValueError) as e:
        raise Exception(f"Failed to parse datasets response: {str(e)}")


def get_flexreports_for_dataset(dataset_name, access_token, headers):
    """
    Retrieve all FlexReports for a specific dataset.

    Args:
        dataset_name (str): Name of the dataset to query
        access_token (str): Bearer token from authentication (unused, kept for API consistency)
        headers (dict): HTTP headers for the request

    Returns:
        list: List of FlexReport dictionaries with id, name, description, etc.

    Raises:
        requests.exceptions.RequestException: If the request fails
        ValueError: If response structure is unexpected
    """
    reports_query = {
        "query": f'query queryReports{dataset_name} {{ flexReports(dataset: "{dataset_name}") {{ id name description createdBy lastUpdatedOn }} }}',
        "variables": {}
    }

    try:
        response = requests.post(CLOUDHEALTH_API_URL, json=reports_query,
                               headers=headers, timeout=30)
        response.raise_for_status()
        report_data = response.json()

        # Validate response structure
        if 'data' not in report_data or 'flexReports' not in report_data['data']:
            raise ValueError(f"Unexpected API response structure for dataset: {dataset_name}")

        return report_data['data']['flexReports']

    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch FlexReports for dataset '{dataset_name}': {str(e)}")
    except (KeyError, ValueError) as e:
        raise Exception(f"Failed to parse FlexReports response for dataset '{dataset_name}': {str(e)}")


def download_flexreport(report_id, report_name, access_token, headers, timestamp):
    """
    Download the full details of a FlexReport and save to a JSON file.

    Args:
        report_id (str): Unique identifier for the report
        report_name (str): Human-readable name of the report
        access_token (str): Bearer token from authentication (unused, kept for API consistency)
        headers (dict): HTTP headers for the request
        timestamp (str): Timestamp string to append to filename

    Returns:
        str: Filename of the downloaded report

    Raises:
        requests.exceptions.RequestException: If the request fails
        IOError: If file write fails
    """
    # Sanitize report name for safe filesystem usage
    # Replace spaces with underscores and remove potentially problematic characters
    report_name_clean = report_name.replace(' ', '_')
    # Remove or replace characters that are invalid in filenames
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        report_name_clean = report_name_clean.replace(char, '_')

    # GraphQL query to fetch complete report details including SQL, configuration, etc.
    download_query = {
        "query": f'query queryReport {{ node(id: "{report_id}") {{ id ... on FlexReport {{ name createdBy result {{ reportUpdatedOn }} query {{ sqlStatement dataset dataGranularity needBackLinkingForTags limit timeRange {{ last from to excludeCurrent }} }} }} }} }}',
        "variables": {}
    }

    try:
        # Execute the download request
        response = requests.post(CLOUDHEALTH_API_URL, json=download_query,
                               headers=headers, timeout=60)
        response.raise_for_status()

        # Write the response to a JSON file with timestamp
        output_filename = f'{report_name_clean}_{timestamp}.json'
        with open(output_filename, 'w', encoding='utf-8') as report_file:
            report_file.write(response.text)

        return output_filename

    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to download FlexReport '{report_name}': {str(e)}")
    except IOError as e:
        raise Exception(f"Failed to write file for FlexReport '{report_name}': {str(e)}")


def create_backup_archive(downloaded_files, timestamp):
    """
    Create a zip archive containing all downloaded FlexReport JSON files.

    Args:
        downloaded_files (list): List of filenames to include in the archive
        timestamp (str): Timestamp string to use in archive filename

    Returns:
        str: Filename of the created zip archive

    Raises:
        IOError: If zip file creation fails
    """
    zip_filename = f'FlexReportsBackup_{timestamp}.zip'

    try:
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in downloaded_files:
                # Add file to zip using just the basename (no directory path)
                # ZIP_DEFLATED provides compression to reduce backup size
                zipf.write(file, os.path.basename(file))

        return zip_filename

    except (IOError, zipfile.BadZipFile) as e:
        raise Exception(f"Failed to create backup archive: {str(e)}")


def cleanup_temp_files(file_list):
    """
    Remove temporary JSON files after they've been added to the archive.
    Errors during cleanup are logged but do not stop execution.

    Args:
        file_list (list): List of filenames to delete
    """
    for file in file_list:
        try:
            # Attempt to remove each temporary file
            if os.path.exists(file):
                os.remove(file)
        except OSError as e:
            # Log error but continue cleanup of remaining files
            print(f"Warning: Could not delete temporary file '{file}': {str(e)}")


def main():
    """
    Main execution function that orchestrates the backup process.

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        # Step 1: Get API credentials (environment variable, hardcoded, or user input)
        api_key = get_api_key()

        # Step 2: Authenticate and get access token
        print("Authenticating...")
        access_token = authenticate_api(api_key)
        print("Authentication successful.")

        # Step 3: Prepare HTTP headers for authenticated requests
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "application/json",
            "Connection": "keep-alive"
        }

        # Step 4: Get all available datasets
        print("Fetching datasets...")
        datasets = get_datasets(access_token)
        print(f"Found {len(datasets)} dataset(s).")

        # Step 5: Generate timestamp for this backup run
        current_timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

        # Step 6: First, collect all reports from all datasets to get total count
        print("\nCollecting FlexReports metadata...")
        all_reports = []
        for dataset in datasets:
            dataset_name = dataset['datasetName']
            report_list = get_flexreports_for_dataset(dataset_name, access_token, headers)
            all_reports.extend(report_list)

        total_reports = len(all_reports)
        downloaded_files = []

        # Step 7: Download all FlexReports with progress indicator
        if total_reports == 0:
            print("No FlexReports found to backup.")
            return 0

        print(f"Found {total_reports} FlexReport(s). Starting download...\n")

        for report_idx, report in enumerate(all_reports, 1):
            report_name = report['name']
            report_id = report['id']

            # Download the report and track the filename
            filename = download_flexreport(report_id, report_name, access_token,
                                         headers, current_timestamp)
            downloaded_files.append(filename)

            # Show progress with counter
            print(f"[{report_idx}/{total_reports}] Downloaded: {report_name}")

        # Step 8: Create zip archive with all downloaded reports
        print(f"\nCreating backup archive...")
        zip_filename = create_backup_archive(downloaded_files, current_timestamp)
        print(f"Successfully created '{zip_filename}' with {len(downloaded_files)} FlexReport(s).")

        # Step 9: Clean up temporary JSON files
        print("Cleaning up temporary files...")
        cleanup_temp_files(downloaded_files)
        print("Temporary JSON files removed.")

        # Success summary
        print("\n" + "="*50)
        print(f"Backup completed successfully!")
        print(f"Total datasets processed: {len(datasets)}")
        print(f"Total reports backed up: {total_reports}")
        print(f"Archive file: {zip_filename}")
        print("="*50)

        return 0

    except KeyboardInterrupt:
        print("\n\nBackup interrupted by user.")
        return 1

    except Exception as e:
        # Catch all exceptions and provide user-friendly error message
        print(f"\n\nERROR: Backup failed!")
        print(f"Reason: {str(e)}")
        print("\nPlease check your API key and network connection, then try again.")
        return 1


# Entry point
if __name__ == "__main__":
    # Exit with the return code from main() for proper shell integration
    exit_code = main()
    sys.exit(exit_code)