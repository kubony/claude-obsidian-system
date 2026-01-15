"""
Google Keep API Manager (OAuth 2.0)

This module provides a manager for Google Keep API operations using OAuth 2.0 user authentication.
"""

import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleKeepAPIManager:
    """
    Manager for Google Keep API operations using OAuth 2.0.

    Attributes:
        credentials: The OAuth 2.0 user credentials.
        keep_service: The Google Keep API service object.
    """

    SCOPES = ['https://www.googleapis.com/auth/keep']

    def __init__(self, client_secrets_file: str, token_file: str = None):
        """
        Initialize the Google Keep API Manager with OAuth 2.0.

        Args:
            client_secrets_file (str): Path to the OAuth client secrets JSON file.
            token_file (str): Path to save/load the token file. Defaults to token.json in same dir.
        """
        if not client_secrets_file:
            raise ValueError("Client secrets file path must be provided")

        self.client_secrets_file = client_secrets_file

        # Default token file location
        if token_file is None:
            token_dir = Path(client_secrets_file).parent
            self.token_file = str(token_dir / 'keep_token.json')
        else:
            self.token_file = token_file

        self.credentials = self._get_credentials()
        self.keep_service = build('keep', 'v1', credentials=self.credentials)

    def _get_credentials(self) -> Credentials:
        """
        Get OAuth 2.0 credentials, refreshing or creating as needed.

        Returns:
            Credentials: Valid OAuth 2.0 credentials.
        """
        creds = None

        # Load existing token
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)

        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("🔄 토큰 갱신 중...")
                creds.refresh(Request())
            else:
                print("🌐 브라우저에서 Google 계정 인증을 진행합니다...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file, self.SCOPES)
                creds = flow.run_local_server(port=0)

            # Save credentials for next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
            print(f"✅ 토큰 저장됨: {self.token_file}")

        return creds

    def list_notes(self, page_size: int = 100, page_token: str = None, filter_str: str = None) -> dict:
        """
        List all notes.

        Args:
            page_size (int): Maximum number of notes to return.
            page_token (str): Token for pagination.
            filter_str (str): Filter string (e.g., "trashed=false").

        Returns:
            dict: Response containing notes list.
        """
        try:
            kwargs = {'pageSize': page_size}
            if page_token:
                kwargs['pageToken'] = page_token
            if filter_str:
                kwargs['filter'] = filter_str

            return self.keep_service.notes().list(**kwargs).execute()
        except HttpError as e:
            raise RuntimeError(f"Failed to list notes: {e.reason}")
        except Exception as e:
            raise RuntimeError(f"Failed to list notes: {str(e)}")

    def get_note(self, note_name: str) -> dict:
        """
        Get a specific note.

        Args:
            note_name (str): The resource name of the note (e.g., "notes/xxxxx").

        Returns:
            dict: The note data.
        """
        try:
            return self.keep_service.notes().get(name=note_name).execute()
        except HttpError as e:
            raise RuntimeError(f"Failed to get note {note_name}: {e.reason}")
        except Exception as e:
            raise RuntimeError(f"Failed to get note {note_name}: {str(e)}")

    def create_note(self, title: str, body: str) -> dict:
        """
        Create a new note.

        Args:
            title (str): Note title.
            body (str): Note body text.

        Returns:
            dict: The created note data.
        """
        try:
            note_body = {
                'title': title,
                'body': {
                    'text': {
                        'text': body
                    }
                }
            }
            return self.keep_service.notes().create(body=note_body).execute()
        except HttpError as e:
            raise RuntimeError(f"Failed to create note: {e.reason}")
        except Exception as e:
            raise RuntimeError(f"Failed to create note: {str(e)}")

    def delete_note(self, note_name: str) -> dict:
        """
        Delete a note.

        Args:
            note_name (str): The resource name of the note.

        Returns:
            dict: Empty response on success.
        """
        try:
            return self.keep_service.notes().delete(name=note_name).execute()
        except HttpError as e:
            raise RuntimeError(f"Failed to delete note {note_name}: {e.reason}")
        except Exception as e:
            raise RuntimeError(f"Failed to delete note {note_name}: {str(e)}")

    def get_all_notes(self, include_trashed: bool = False) -> list:
        """
        Get all notes with pagination.

        Args:
            include_trashed (bool): Whether to include trashed notes.

        Returns:
            list: All notes.
        """
        all_notes = []
        page_token = None
        filter_str = None if include_trashed else "trashed=false"

        while True:
            response = self.list_notes(page_size=100, page_token=page_token, filter_str=filter_str)
            notes = response.get('notes', [])
            all_notes.extend(notes)

            page_token = response.get('nextPageToken')
            if not page_token:
                break

        return all_notes
