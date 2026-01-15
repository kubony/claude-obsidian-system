"""
Base Google API Manager

This module provides the base class for all Google API managers.
"""

from google.oauth2 import service_account

class GoogleAPIManager:
    """
    Base class for Google API services.

    This class handles authentication with service account credentials.
    All specific Google API managers inherit from this base class.

    Attributes:
        credentials: The service account credentials.
    """

    def __init__(self, key_file, scopes):
        """
        Initialize the Google API Manager.

        Args:
            key_file (str): Path to the service account key file.
            scopes (list): List of API scopes to request.

        Raises:
            FileNotFoundError: If the key file is not found.
            ValueError: If scopes are empty or invalid.
        """
        if not key_file:
            raise ValueError("Key file path must be provided")
        if not scopes:
            raise ValueError("At least one scope must be provided")

        try:
            self.credentials = service_account.Credentials.from_service_account_file(
                key_file, scopes=scopes)
        except FileNotFoundError:
            raise FileNotFoundError(f"Service account key file not found: {key_file}")
        except Exception as e:
            raise ValueError(f"Failed to initialize credentials: {str(e)}")

    def build_service(self, service_name, service_version):
        """
        Builds and returns a Google API service object.

        Args:
            service_name (str): The name of the service (e.g., 'drive', 'sheets').
            service_version (str): The version of the service (e.g., 'v3', 'v4').

        Returns:
            A Google API service object.

        Raises:
            Exception: If the service fails to build.
        """
        try:
            # googleapiclient.discovery.build 함수를 직접 사용합니다.
            # 이 함수는 테스트에서 모킹됩니다.
            from googleapiclient.discovery import build
            from googleapiclient.errors import UnknownApiNameOrVersion # 예외 import
            service = build(service_name, service_version, credentials=self.credentials)
            return service
        except UnknownApiNameOrVersion as e:
            # 잘못된 서비스명 또는 버전일 경우 ValueError 발생
            raise ValueError(f"Invalid service name or version: {service_name} {service_version}. Original error: {str(e)}")
        except Exception as e:
            # 그 외 예외 처리
            raise Exception(f"Failed to build service {service_name} {service_version}: {str(e)}")
