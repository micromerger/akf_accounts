import frappe

def execute():
	if not frappe.db.exists("Custom Field", "HR Settings-skip_validations_role"):
		frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "Stock Settings",  # Target DocType
			"module": "Akf Accounts",
			"label": "Disable Material Request Purpose",  # Field label
			"fieldname": "disable_material_request_purpose",  # Fieldname in code
			"fieldtype": "Check",  # Choose your field type (e.g., Data, Int, Check, etc.)
			"options": "",
			"insert_after": "exit_questionnaire_web_form",  # Insert after an existing field
			"description": "This is used to skip normal <Material Request> flow."
		}).insert(ignore_permissions=True)

