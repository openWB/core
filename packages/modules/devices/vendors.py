from enum import Enum


class VendorGroup(Enum):
    GENERIC = "generic"
    OPENWB = "openwb"
    VENDORS = "vendors"


READABLE_GROUP_NAME = {
    VendorGroup.GENERIC: "herstellerunabhängig",
    VendorGroup.OPENWB: "openWB",
    VendorGroup.VENDORS: "andere Hersteller",
}
