import os
from .exceptions import InvalidAccessToken, ItemNotFound, RateLimited, DriveException
from requests import Session
from abc import ABC, abstractmethod
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from requests.exceptions import HTTPError
from .constants import SIMPLE_UPLOAD_MAX_SIZE, CHUNK_UPLOAD_MAX_SIZE


class MSDrive(ABC):
    """Abstract class for accessing files stored in OneDrive and SharePoint using the Microsoft Graph API."""

    def __init__(self, access_token: str) -> None:
        """Class constructor that accepts a Microsoft access token for use with the API

        Args:
            access_token (str): The access token
        """
        self.access_token = access_token

    def get_item_data(self, **kwargs) -> dict:
        """Get metadata for a DriveItem.

        Args:
            drive_id (str): The drive ID (only for SharePoint)
            item_id (str): [EITHER] The item ID
            item_path (str): [EITHER] The item path

        Returns:
            dict: JSON representation of a DriveItem resource
        """
        r = self._session().get(self._get_drive_item_url(**kwargs))

        return r.json()

    def list_items(self, **kwargs) -> dict:
        """List the DriveItems in a specific folder path.

        Args:
            drive_id (str): The drive ID (only for SharePoint)
            folder_path (str): The folder path (or leave out for root)

        Returns:
            dict: JSON representation of a collection of DriveItem resources
        """
        r = self._session().get(self._get_drive_children_url(**kwargs))

        return r.json()

    def download_item(self, **kwargs) -> None:
        """Download a DriveItem file to a specific local path.

        Args:
            drive_id (str): The drive ID (only for SharePoint)
            item_id (str): [EITHER] The item ID
            item_path (str): [EITHER] The item path
            file_path (str): Local path to save the file to (e.g. /tmp/blah.csv)
        """
        if not kwargs.get("file_path"):
            raise ValueError("Missing file_path argument")

        data = self.get_item_data(**kwargs)

        with Session().get(data["@microsoft.graph.downloadUrl"], stream=True) as r:
            r.raise_for_status()

            with open(kwargs["file_path"], "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

    def upload_item(self, **kwargs) -> None:
        """Upload a local file to an existing or new DriveItem.

        Specify the item_path for a new file.
        Specify the item_path or item_id for an existing file.

        Args:
            drive_id (str): The drive ID (only for SharePoint)
            item_id (str): [EITHER] The item ID
            item_path (str): [EITHER] The item path
            file_path (str): Local path to upload the file from (e.g. /tmp/blah.csv)
        """
        if not kwargs.get("file_path"):
            raise ValueError("Missing file_path argument")

        file_size = os.stat(kwargs["file_path"]).st_size

        if file_size <= SIMPLE_UPLOAD_MAX_SIZE:
            self._upload_item_small(**kwargs)
        else:
            self._upload_item_large(**kwargs)

    @abstractmethod
    def _get_drive_item_url(self, **kwargs) -> str:
        raise NotImplementedError("Must be overridden")

    @abstractmethod
    def _get_drive_children_url(self, **kwargs) -> str:
        raise NotImplementedError("Must be overridden")

    def _session(self) -> Session:
        s = Session()
        s.hooks["response"] = [self.raise_error_hook]
        s.headers.update({"Authorization": "Bearer " + self.access_token})

        return s

    def _session_upload(self) -> Session:
        retries = Retry(
            total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504]
        )

        adapter = HTTPAdapter(max_retries=retries)

        s = Session()
        s.mount("http://", adapter)
        s.mount("https://", adapter)
        s.hooks["response"] = [self.raise_error_hook]

        return s

    def _upload_item_small(self, **kwargs) -> None:
        url = self._get_drive_item_url(**kwargs)
        file_data = open(kwargs["file_path"], "rb")

        if kwargs.get("item_id"):
            url += "/content"
        else:
            url += ":/content"

        try:
            self._session().put(url, data=file_data)
        finally:
            file_data.close()

    def _upload_item_large(self, **kwargs) -> None:
        upload_url = self._get_upload_url(**kwargs)
        file_size = os.stat(kwargs["file_path"]).st_size

        with open(kwargs["file_path"], "rb") as f:
            chunk_size = CHUNK_UPLOAD_MAX_SIZE
            chunk_number = file_size // chunk_size
            chunk_leftover = file_size - chunk_size * chunk_number
            chunk_data = f.read(chunk_size)
            i = 0

            while chunk_data:
                start_index = i * chunk_size
                end_index = start_index + chunk_size

                if i == chunk_number:
                    end_index = start_index + chunk_leftover

                s = self._session_upload()

                # Setting the header with the appropriate chunk data location in the file
                headers = {
                    "Content-Length": str(chunk_size),
                    "Content-Range": "bytes {}-{}/{}".format(
                        start_index, end_index - 1, file_size
                    ),
                }

                s.headers.update(headers)
                s.put(upload_url, data=chunk_data)

                i = i + 1
                chunk_data = f.read(chunk_size)

    def _get_upload_url(self, **kwargs) -> str:
        url = self._get_drive_item_url(**kwargs)

        if kwargs.get("item_id"):
            url += "/createUploadSession"
        else:
            url += ":/createUploadSession"

        r = self._session().post(url)

        return r.json()["uploadUrl"]

    def raise_error_hook(self, resp, *args, **kwargs) -> None:
        try:
            resp.raise_for_status()
        except HTTPError as err:
            self._handle_http_error(err)

    def _handle_http_error(self, err: HTTPError) -> None:
        if err.response is None:
            raise err

        try:
            body = err.response.json()
            message = body["error"]["message"]
        except Exception:
            raise err

        if err.response.status_code == 401:
            raise InvalidAccessToken(message)

        if err.response.status_code == 404:
            raise ItemNotFound(message)

        if err.response.status_code == 429:
            raise RateLimited(message)

        raise DriveException(message)
