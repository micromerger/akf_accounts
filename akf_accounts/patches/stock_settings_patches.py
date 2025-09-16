import frappe

def execute():
	if not frappe.db.exists("Custom Field", "Stock Settings-disable_material_request_purpose"):
		frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "Stock Settings",  # Target DocType
			"module": "AKF Accounts",
			"label": "Disable Material Request Purpose",  # Field label
			"fieldname": "disable_material_request_purpose",  # Fieldname in code
			"fieldtype": "Check",  # Choose your field type (e.g., Data, Int, Check, etc.)
			"options": "",
			"insert_after": "allow_uom_with_conversion_rate_defined_in_item",  # Insert after an existing field
			"description": "Disable material request purpose-wise functionality by enabling this checkbox."
		}).insert()

