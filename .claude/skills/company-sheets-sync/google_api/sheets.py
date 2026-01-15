"""
Google Sheets API Manager

This module provides a manager for Google Sheets API operations.
"""

import googleapiclient.discovery
import pandas as pd
from .base import GoogleAPIManager

class GoogleSheetAPIManager(GoogleAPIManager):
    """
    Manager for Google Sheets API operations.

    This class provides methods to read, write, and manage Google Sheets.

    Attributes:
        sheet_service: The Google Sheets API service object.
        spreadsheet_id: The ID of the current spreadsheet.
    """

    def __init__(self, key_file, scopes):
        """
        Initialize the Google Sheet API Manager.

        Args:
            key_file (str): Path to the service account key file.
            scopes (list): List of API scopes to request.
        """
        super().__init__(key_file, scopes)
        self.sheet_service = googleapiclient.discovery.build(
            'sheets', 'v4', credentials=self.credentials)
        self.spreadsheet_id = None

    def set_spreadsheet_id(self, spreadsheet_id):
        """
        Set the current spreadsheet ID.

        Args:
            spreadsheet_id (str): The ID of the spreadsheet to operate on.
        """
        if not spreadsheet_id:
            raise ValueError("Spreadsheet ID must be provided")
        self.spreadsheet_id = spreadsheet_id

    def get_sheet(self, spreadsheet_id=None):
        """
        Get the spreadsheet metadata.

        Args:
            spreadsheet_id (str, optional): The ID of the spreadsheet.
                If not provided, uses the current spreadsheet_id.

        Returns:
            dict: The spreadsheet metadata.
        """
        sheet_id = spreadsheet_id or self.spreadsheet_id
        if not sheet_id:
            raise ValueError("Spreadsheet ID must be provided or set with set_spreadsheet_id()")

        try:
            return self.sheet_service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        except Exception as e:
            raise RuntimeError(f"Failed to get sheet: {str(e)}")

    def get_values(self, range_name, spreadsheet_id=None):
        """
        Get values from a range in the spreadsheet.

        Args:
            range_name (str): The A1 notation of the range to retrieve.
            spreadsheet_id (str, optional): The ID of the spreadsheet.
                If not provided, uses the current spreadsheet_id.

        Returns:
            list: 2D array of values from the specified range.
        """
        sheet_id = spreadsheet_id or self.spreadsheet_id
        if not sheet_id:
            raise ValueError("Spreadsheet ID must be provided or set with set_spreadsheet_id()")

        try:
            result = self.sheet_service.spreadsheets().values().get(
                spreadsheetId=sheet_id, range=range_name).execute()
            return result.get('values', [])
        except Exception as e:
            raise RuntimeError(f"Failed to get values: {str(e)}")

    def update_values(self, range_name, values, major_dimension="ROWS", spreadsheet_id=None):
        """
        Update values in a range of the spreadsheet.

        Args:
            range_name (str): The A1 notation of the range to update.
            values (list): 2D array of values to update.
            major_dimension (str, optional): The major dimension of the values.
            spreadsheet_id (str, optional): The ID of the spreadsheet.
                If not provided, uses the current spreadsheet_id.

        Returns:
            dict: Update response.
        """
        sheet_id = spreadsheet_id or self.spreadsheet_id
        if not sheet_id:
            raise ValueError("Spreadsheet ID must be provided or set with set_spreadsheet_id()")

        try:
            body = {
                'values': values,
                'majorDimension': major_dimension
            }
            return self.sheet_service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
        except Exception as e:
            raise RuntimeError(f"Failed to update values: {str(e)}")

    def batch_update_values(self, data, spreadsheet_id=None):
        """
        Update multiple ranges in a single batch request.

        Args:
            data (list): List of dictionaries with "range" and "values" keys.
            spreadsheet_id (str, optional): The ID of the spreadsheet.
                If not provided, uses the current spreadsheet_id.

        Returns:
            dict: Batch update response.
        """
        sheet_id = spreadsheet_id or self.spreadsheet_id
        if not sheet_id:
            raise ValueError("Spreadsheet ID must be provided or set with set_spreadsheet_id()")

        try:
            batch_data = []
            for item in data:
                batch_data.append({
                    'range': item['range'],
                    'values': item['values'],
                    'majorDimension': item.get('majorDimension', 'ROWS')
                })

            body = {
                'valueInputOption': 'USER_ENTERED',
                'data': batch_data
            }

            return self.sheet_service.spreadsheets().values().batchUpdate(
                spreadsheetId=sheet_id, body=body).execute()
        except Exception as e:
            raise RuntimeError(f"Failed to batch update values: {str(e)}")

    def update_sheet_properties(self, properties, spreadsheet_id=None):
        """
        Update sheet properties.

        Args:
            properties (dict): Sheet properties to update.
            spreadsheet_id (str, optional): The ID of the spreadsheet.
                If not provided, uses the current spreadsheet_id.

        Returns:
            dict: Batch update response.
        """
        sheet_id = spreadsheet_id or self.spreadsheet_id
        if not sheet_id:
            raise ValueError("Spreadsheet ID must be provided or set with set_spreadsheet_id()")

        try:
            body = {
                'requests': [
                    {
                        'updateSheetProperties': {
                            'properties': properties,
                            'fields': ','.join(properties.keys())
                        }
                    }
                ]
            }

            return self.sheet_service.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id, body=body).execute()
        except Exception as e:
            raise RuntimeError(f"Failed to update sheet properties: {str(e)}")

    def load_data_as_dataframe(self, range_name, spreadsheet_id=None, header_row=0):
        """
        Load data from a range as a pandas DataFrame.

        Args:
            range_name (str): The A1 notation of the range to retrieve.
            spreadsheet_id (str, optional): The ID of the spreadsheet.
            header_row (int, optional): Row index to use as DataFrame header.

        Returns:
            pandas.DataFrame: Data from the specified range.
        """
        sheet_id = spreadsheet_id or self.spreadsheet_id
        values = self.get_values(range_name, sheet_id)
        if not values:
            return pd.DataFrame()

        if header_row >= 0 and header_row < len(values):
            headers = values[header_row]
            data = values[header_row + 1:]
            return pd.DataFrame(data, columns=headers)
        else:
            return pd.DataFrame(values)

    def create_sheet(self, title, spreadsheet_id=None):
        """
        Create a new sheet in the spreadsheet.

        Args:
            title (str): Title of the new sheet.
            spreadsheet_id (str, optional): The ID of the spreadsheet.

        Returns:
            dict: The created sheet properties.
        """
        sheet_id = spreadsheet_id or self.spreadsheet_id
        if not sheet_id:
            raise ValueError("Spreadsheet ID must be provided or set with set_spreadsheet_id()")

        try:
            body = {
                'requests': [
                    {
                        'addSheet': {
                            'properties': {
                                'title': title
                            }
                        }
                    }
                ]
            }

            response = self.sheet_service.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id, body=body).execute()
            return response['replies'][0]['addSheet']['properties']
        except Exception as e:
            raise RuntimeError(f"Failed to create sheet: {str(e)}")

    def delete_sheet(self, sheet_id, spreadsheet_id=None):
        """
        Delete a sheet from the spreadsheet.

        Args:
            sheet_id (int): The ID of the sheet to delete.
            spreadsheet_id (str, optional): The ID of the spreadsheet.

        Returns:
            dict: Batch update response.
        """
        spreadsheet_id = spreadsheet_id or self.spreadsheet_id
        if not spreadsheet_id:
            raise ValueError("Spreadsheet ID must be provided or set with set_spreadsheet_id()")

        try:
            body = {
                'requests': [
                    {
                        'deleteSheet': {
                            'sheetId': sheet_id
                        }
                    }
                ]
            }

            return self.sheet_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id, body=body).execute()
        except Exception as e:
            raise RuntimeError(f"Failed to delete sheet: {str(e)}")
