import csv


def export_to_csv(file_path, headers, data):
    """Export data to CSV file

    Args:
        file_path: Path to save the CSV file
        headers: List of column headers
        data: List of rows (each row is a list of values)

    Returns:
        bool: Success status
    """
    try:
        # Add .csv extension if not present
        if not file_path.endswith('.csv'):
            file_path += '.csv'

        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Write headers
            writer.writerow(headers)

            # Write data
            for row in data:
                writer.writerow(row)

        return True
    except Exception as e:
        print(f"Export error: {e}")
        return False