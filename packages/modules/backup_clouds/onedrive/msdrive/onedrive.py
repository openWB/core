from .drive import MSDrive
from urllib.parse import quote
from .constants import BASE_GRAPH_URL


class OneDrive(MSDrive):
    """Class for accessing DriveItems stored in OneDrive.

    A DriveItem resource represents a file, folder, or other item stored in a drive.

    All file system objects in OneDrive are returned as DriveItem resources (see https://bit.ly/3HAAxrh).

    """

    def _get_drive_item_url(self, **kwargs) -> str:
        if kwargs.get("item_id"):
            return f"{BASE_GRAPH_URL}/me/drive/items/{kwargs['item_id']}"

        if kwargs.get("item_path"):
            path = quote(kwargs["item_path"].lstrip("/"))
            return f"{BASE_GRAPH_URL}/me/drive/root:/{path}"

        raise ValueError("Missing argument: item_id or item_path")

    def _get_drive_children_url(self, **kwargs) -> str:
        if not kwargs.get("folder_path"):
            return f"{BASE_GRAPH_URL}/me/drive/root/children"
        else:
            path = quote(kwargs["folder_path"].lstrip("/").rstrip("/"))
            return f"{BASE_GRAPH_URL}/me/drive/root:/{path}:/children"
