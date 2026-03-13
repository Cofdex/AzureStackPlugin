"""Uploads documents to Azure Blob Storage using DefaultAzureCredential."""

import os
from pathlib import Path

from azure.core.exceptions import AzureError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient


class UploadError(Exception):
    """Raised when a document upload to Azure Blob Storage fails."""


def upload_document(file_path: str, container: str = "raw-uploads") -> str:
    """Upload a local file to Azure Blob Storage.

    Args:
        file_path: Absolute or relative path to the local file to upload.
        container: Target blob container name. Defaults to "raw-uploads".

    Returns:
        The full HTTPS URL of the uploaded blob.

    Raises:
        UploadError: If the file does not exist or the upload fails.
    """
    path = Path(file_path)
    if not path.exists():
        raise UploadError(f"File not found: {file_path}")

    storage_account = os.environ.get("AZURE_STORAGE_ACCOUNT")
    if not storage_account:
        raise UploadError("Environment variable AZURE_STORAGE_ACCOUNT is not set.")

    account_url = f"https://{storage_account}.blob.core.windows.net"
    blob_name = path.name

    try:
        credential = DefaultAzureCredential()
        service_client = BlobServiceClient(account_url=account_url, credential=credential)
        blob_client = service_client.get_blob_client(container=container, blob=blob_name)

        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        return blob_client.url
    except AzureError as exc:
        raise UploadError(f"Upload failed for '{blob_name}': {exc}") from exc
