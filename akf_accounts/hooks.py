app_name = "akf_accounts"
app_title = "AKF Accounts"
app_publisher = "Nabeel Saleem"
app_description = "Custom changes in accounts module"
app_email = "nabeel.saleem333@gmail.com"
app_license = "mit"
# required_apps = []

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/akf_accounts/css/akf_accounts.css"
# app_include_js = "/assets/akf_accounts/js/akf_accounts.js"
app_include_js = [
    "/assets/akf_accounts/js/jquery.inputmask.min.js",
    "/assets/akf_accounts/js/jquery.mask.js",
    "/assets/akf_accounts/js/highcharts_apis/highcharts.js",
    "/assets/akf_accounts/js/highcharts_apis/data.js",
    "/assets/akf_accounts/js/highcharts_apis/export-data.js",
    "/assets/akf_accounts/js/highcharts_apis/exporting.js",
    "/assets/akf_accounts/js/highcharts_apis/accessibility.js",
    "/assets/akf_accounts/js/highcharts_apis/variable-pie.js",
    "/assets/akf_accounts/js/d3.v7.min.js",
    "/assets/akf_accounts/js/d3-org-chart.js",
    "/assets/akf_accounts/js/d3-flextree.js",
    "/assets/akf_accounts/js/html2canvas.js",
]
# include js, css files in header of web template
# web_include_css = "/assets/akf_accounts/css/akf_accounts.css"
# web_include_js = "/assets/akf_accounts/js/akf_accounts.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "akf_accounts/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}
# /home/frappe/frappe-bench/sites/assets/akf_accounts/js/customizations/purchase_invoice.js
# include js in doctype views
doctype_js = {
	"Payment Entry" : "public/js/customizations/payment_entry.js",
	# "Purchase Receipt" : "public/js/customizations/purchase_receipt.js",
    "Purchase Invoice" : "public/js/customizations/purchase_invoice.js",
    # "Asset" : "public/js/customizations/asset.js",
    "Asset Movement": "public/js/customizations/asset_movement.js",
	# "Purchase Order": "public/js/customizations/enc_purchase_order.js",
    "Material Request": "public/js/customizations/enc_material_request.js",
    "Project": "public/js/customizations/enc_project.js",
    "Stock Entry": "public/js/customizations/material_request_get_items_from.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "akf_accounts/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "akf_accounts.utils.jinja_methods",
# 	"filters": "akf_accounts.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "akf_accounts.install.before_install"
# after_install = "akf_accounts.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "akf_accounts.uninstall.before_uninstall"
# after_uninstall = "akf_accounts.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "akf_accounts.utils.before_app_install"
# after_app_install = "akf_accounts.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "akf_accounts.utils.before_app_uninstall"
# after_app_uninstall = "akf_accounts.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "akf_accounts.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
    "Material Request": "akf_accounts.customizations.overrides.cdoctype.material_request.MaterialRequest",
    "Stock Entry": "akf_accounts.customizations.extends.xstock_entry.XStockEntry",
	"Purchase Receipt" : "akf_accounts.customizations.overrides.cdoctype.purchase_receipt.PurchaseReceipt",
    "Purchase Invoice" : "akf_accounts.customizations.overrides.cdoctype.purchase_invoice.PurchaseInvoice",
    # "Sales Invoice": "akf_accounts.customizations.extends.xsales_invoice.XSalesInvoice",
    "Payment Entry": "akf_accounts.customizations.overrides.payment_entry.XPaymentEntry",
    "Asset": "akf_accounts.customizations.overrides.cdoctype.asset.Asset",
    "Asset Movement": "akf_accounts.customizations.overrides.cdoctype.asset.AssetMovement"
   
}
# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Donation": {
        "validate": "akf_accounts.utils.financial_closure.confirmation",
        "on_submit": "akf_accounts.utils.financial_closure.confirmation",
	},
    "Project": {
        "validate": "akf_accounts.utils.encumbrance.enc_project.validate_donor_balance",
        "after_insert": "akf_accounts.utils.encumbrance.enc_project.make_project_encumbrance_gl_entries",
        "on_trash": "akf_accounts.utils.encumbrance.enc_project.cancel_project_encumbrance_gl_entries"
    },
    "Material Request": {
        "validate": [
            "akf_accounts.utils.financial_closure.confirmation",
            "akf_accounts.utils.encumbrance.enc_material_request.validate_donor_balance"
        ],
        "on_submit": [
            "akf_accounts.utils.financial_closure.confirmation",
            "akf_accounts.utils.encumbrance.enc_material_request.make_encumbrance_material_request_gl_entries"
        ],
        "before_cancel": [
            "akf_accounts.utils.encumbrance.enc_material_request.cancel_encumbrance_material_request_gl_entries"
        ]
	},
    "Stock Entry": {
        "validate": "akf_accounts.utils.mortizations.mor_stock_entry.validate_donor_balance",
        "on_submit": "akf_accounts.utils.mortizations.mor_stock_entry.make_mortizations_gl_entries",
        "on_cancel": "akf_accounts.utils.mortizations.mor_stock_entry.del_stock_gl_entries",
	},
    # "Purchase Order": {
    #     "validate": "akf_accounts.utils.encumbrance.enc_purchase_order.validate_donor_balance",
    #     "on_submit": "akf_accounts.utils.encumbrance.enc_purchase_order.make_encumbrance_purchase_order_gl_entries",
    #     "on_cancel": "akf_accounts.utils.encumbrance.enc_purchase_order.del_encumbrance_gl_entries",
    # },
    "Purchase Receipt": {
        "validate": "akf_accounts.utils.financial_closure.confirmation",
        "on_submit": ["akf_accounts.utils.financial_closure.confirmation",
            "akf_accounts.utils.encumbrance.enc_purchase_receipt.update_grn_accounting_dimensions",
            "akf_accounts.utils.purchase_receipt.stock_ledger_entry.update_stock_dimensions"
        ]
	},
    "Purchase Invoice": {
        "validate": "akf_accounts.utils.financial_closure.confirmation",
        "on_submit": [
            "akf_accounts.utils.financial_closure.confirmation",
            "akf_accounts.utils.encumbrance.enc_purchase_invoice.update_p_i_accounting_dimensions"
        ]
	},
    "Payment Entry": {
        "validate": [
            "akf_accounts.utils.financial_closure.confirmation",
            "akf_accounts.utils.payment_entry_utils.apply_tax_matrix",
        ],
        "on_submit": [
            "akf_accounts.utils.financial_closure.confirmation",
            "akf_accounts.utils.payment_entry_utils.make_journal_entry"
        ]
	},
    # "Tax Withholding Category": {
    #     "validate": "akf_accounts.utils.taxation.tax_withholding_category.set_sales_tax_and_province_rate",
    # }
    # "Asset Movement": {
    #     "on_submit": [
    #         "akf_accounts.utils.asset_gle_entry.asset_movement.make_asset_movement_gl_entries",
    #         "akf_accounts.utils.asset_gle_entry.asset_movement.make_asset_inter_fund_transfer_gl_entries",
    #     ],
    #     "on_cancel": "akf_accounts.utils.asset_gle_entry.asset_movement.delete_all_gl_entries",
    # }
}


# Scheduled Tasks
# ---------------
scheduler_events = {

      "cron": {
        "*/5 * * * *": [
             "akf_accounts.customizations.extends.depreciation.post_depreciation_entries",
        ],      
    },
 	"all": [
 		# "akf_accounts.tasks.all"
 	],
	"daily": [
       
		# "akf_accounts.tasks.daily"
        # "akf_accounts.customizations.extends.XAsset.post_depreciation_entries_extended",
        "akf_accounts.akf_accounts.doctype.donation.donation.cron_for_notify_overdue_tasks"
	],
	# "daily_long":
    # [    	
    #     "akf_accounts.customizations.extends.XAsset.post_depreciation_entries_extended",
	# ],
    
	"hourly": [
		# "akf_accounts.tasks.hourly"
	],
 	"weekly": [
		# "akf_accounts.tasks.weekly"
 	],
 	"monthly": [
		# "akf_accounts.tasks.monthly"
	],
}

# Testing
# -------

# before_tests = "akf_accounts.install.before_tests"

# Overriding Methods
# ------------------------------
#
# /home/frappe/frappe-bench/apps/akf_accounts/akf_accounts/customizations/extends/XAsset.py
override_whitelisted_methods = {
    "erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry": "akf_accounts.customizations.overrides.payment_entry.get_payment_entry" 
# 	# "frappe.desk.doctype.event.event.get_events": "akf_accounts.event.get_events"
#      "erpnext.assets.doctype.asset.depreciation.post_depreciation_entries": "akf_accounts.customizations.extends.XAsset.post_depreciation_entries_extended"
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "akf_accounts.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["akf_accounts.utils.before_request"]
# after_request = ["akf_accounts.utils.after_request"]

# Job Events
# ----------
# before_job = ["akf_accounts.utils.before_job"]
# after_job = ["akf_accounts.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"akf_accounts.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# fixtures = ["Inventory Flag", "Inventory Scenario", "Accounting Dimension"]

accounting_dimension_doctypes = [
	"Payment Detail",
	"Deduction Breakeven",
    "Stock Ledger Entry"
]
# fixtures = ['Inventory Dimension', 'Accounting Dimension', 'Country', 'Donor Type', 'Donation Type']
fixtures = [
    {
        "dt": "Custom Field",
        "filters": [
            ["dt", "in", ["Company", "Cost Center", ""]],
            ["module", "in", ["AKF Accounts"]]
        ]
    }
]

# bench --site al-khidmat.com export-fixtures