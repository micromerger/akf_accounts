# Copyright (c) 2025, Nabeel Saleem and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class FundClass(Document):
	pass
	
@frappe.whitelist()
def initiate_project(*args, **kwargs):
	frappe.msgprint(f'project...')

@frappe.whitelist()
def initiate_budget(*args, **kwargs):
	frappe.msgprint(f'redirecting to budget...')

