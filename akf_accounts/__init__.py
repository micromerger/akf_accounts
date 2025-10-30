__version__ = "0.0.1"

import erpnext.assets.doctype.asset.depreciation as depreciation
from akf_accounts.monkey_patching.depreciation import (
    custom_post_depreciation_entries,
    custom_get_gl_entries_on_asset_disposal,
    custom_scrap_asset
    )

def override_depreciation_function():
    depreciation.post_depreciation_entries = custom_post_depreciation_entries
    depreciation.get_gl_entries_on_asset_disposal = custom_get_gl_entries_on_asset_disposal
    depreciation.scrap_asset = custom_scrap_asset

override_depreciation_function()


