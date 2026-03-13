"""Unit tests for src/ingestion/uploader.py."""

import io
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
from azure.core.exceptions import ServiceRequestError

from src.ingestion.uploader import UploadError, upload_document


@pytest.fixture()
def tmp_file(tmp_path: Path) -> Path:
    """Return a temporary file that exists on disk."""
    f = tmp_path / "document.txt"
    f.write_text("hello world")
    return f


class TestUploadDocumentSuccess:
    def test_returns_blob_url(self, tmp_file: Path) -> None:
        """upload_document returns the blob URL on a successful upload."""
        expected_url = (
            "https://myaccount.blob.core.windows.net/raw-uploads/document.txt"
        )

        mock_blob_client = MagicMock()
        mock_blob_client.url = expected_url

        mock_service_client = MagicMock()
        mock_service_client.get_blob_client.return_value = mock_blob_client

        with (
            patch("src.ingestion.uploader.DefaultAzureCredential"),
            patch(
                "src.ingestion.uploader.BlobServiceClient",
                return_value=mock_service_client,
            ),
            patch.dict("os.environ", {"AZURE_STORAGE_ACCOUNT": "myaccount"}),
        ):
            result = upload_document(str(tmp_file))

        assert result == expected_url

    def test_upload_blob_called_with_overwrite(self, tmp_file: Path) -> None:
        """upload_document calls upload_blob with overwrite=True."""
        mock_blob_client = MagicMock()
        mock_blob_client.url = "https://myaccount.blob.core.windows.net/raw-uploads/document.txt"

        mock_service_client = MagicMock()
        mock_service_client.get_blob_client.return_value = mock_blob_client

        with (
            patch("src.ingestion.uploader.DefaultAzureCredential"),
            patch(
                "src.ingestion.uploader.BlobServiceClient",
                return_value=mock_service_client,
            ),
            patch.dict("os.environ", {"AZURE_STORAGE_ACCOUNT": "myaccount"}),
        ):
            upload_document(str(tmp_file))

        call_kwargs = mock_blob_client.upload_blob.call_args
        assert call_kwargs.kwargs.get("overwrite") is True

    def test_custom_container(self, tmp_file: Path) -> None:
        """upload_document uses the container name passed as argument."""
        mock_blob_client = MagicMock()
        mock_blob_client.url = "https://myaccount.blob.core.windows.net/custom/document.txt"

        mock_service_client = MagicMock()
        mock_service_client.get_blob_client.return_value = mock_blob_client

        with (
            patch("src.ingestion.uploader.DefaultAzureCredential"),
            patch(
                "src.ingestion.uploader.BlobServiceClient",
                return_value=mock_service_client,
            ),
            patch.dict("os.environ", {"AZURE_STORAGE_ACCOUNT": "myaccount"}),
        ):
            upload_document(str(tmp_file), container="custom")

        mock_service_client.get_blob_client.assert_called_once_with(
            container="custom", blob=tmp_file.name
        )


class TestUploadDocumentFileNotFound:
    def test_raises_upload_error_for_missing_file(self) -> None:
        """upload_document raises UploadError when the file does not exist."""
        with (
            patch.dict("os.environ", {"AZURE_STORAGE_ACCOUNT": "myaccount"}),
            pytest.raises(UploadError, match="File not found"),
        ):
            upload_document("/nonexistent/path/missing.txt")

    def test_error_message_contains_path(self) -> None:
        """UploadError message includes the missing file path."""
        missing = "/tmp/does_not_exist_abc123.pdf"
        with (
            patch.dict("os.environ", {"AZURE_STORAGE_ACCOUNT": "myaccount"}),
            pytest.raises(UploadError, match=missing),
        ):
            upload_document(missing)


class TestUploadDocumentUploadError:
    def test_raises_upload_error_on_azure_failure(self, tmp_file: Path) -> None:
        """upload_document wraps AzureError in UploadError."""
        mock_blob_client = MagicMock()
        mock_blob_client.upload_blob.side_effect = ServiceRequestError(
            "network timeout"
        )

        mock_service_client = MagicMock()
        mock_service_client.get_blob_client.return_value = mock_blob_client

        with (
            patch("src.ingestion.uploader.DefaultAzureCredential"),
            patch(
                "src.ingestion.uploader.BlobServiceClient",
                return_value=mock_service_client,
            ),
            patch.dict("os.environ", {"AZURE_STORAGE_ACCOUNT": "myaccount"}),
            pytest.raises(UploadError, match="Upload failed"),
        ):
            upload_document(str(tmp_file))

    def test_upload_error_chains_original_exception(self, tmp_file: Path) -> None:
        """UploadError.__cause__ is set to the original AzureError."""
        original = ServiceRequestError("timeout")

        mock_blob_client = MagicMock()
        mock_blob_client.upload_blob.side_effect = original

        mock_service_client = MagicMock()
        mock_service_client.get_blob_client.return_value = mock_blob_client

        with (
            patch("src.ingestion.uploader.DefaultAzureCredential"),
            patch(
                "src.ingestion.uploader.BlobServiceClient",
                return_value=mock_service_client,
            ),
            patch.dict("os.environ", {"AZURE_STORAGE_ACCOUNT": "myaccount"}),
        ):
            with pytest.raises(UploadError) as exc_info:
                upload_document(str(tmp_file))

        assert exc_info.value.__cause__ is original

    def test_raises_upload_error_when_env_var_missing(self, tmp_file: Path) -> None:
        """upload_document raises UploadError when AZURE_STORAGE_ACCOUNT is unset."""
        with (
            patch.dict("os.environ", {}, clear=True),
            pytest.raises(UploadError, match="AZURE_STORAGE_ACCOUNT"),
        ):
            upload_document(str(tmp_file))
