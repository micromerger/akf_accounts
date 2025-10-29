__version__ = "0.0.1"

import erpnext.assets.doctype.asset.depreciation as depreciation
from akf_accounts.scheduler_jobs.depreciation import custom_post_depreciation_entries

def override_depreciation_function():
    depreciation.post_depreciation_entries = custom_post_depreciation_entries

override_depreciation_function()
