import frappe, ast
from akf_accounts.utils.accounts_defaults import get_company_defaults

""" 
Nabeel Saleem
Date: 21-03-2025
"""
# 
@frappe.whitelist()
def update_link_records_of_donor(values=None):
	if(isinstance(values, str)):
		values = frappe.json.loads(values)
		values = frappe._dict(values)
	doctypes = ["Program Details", "Payment Entry", "Purchase Invoice", "Purchase Receipt", "Material Request", "Budget", "GL Entry"]
	
	def update_donor_balance_table(parent): 
		frappe.db.sql(f"""
					Update `tabProgram Details`
					Set pd_donor = '{values.new_donor}'
					Where docstatus=1 and parent = '{parent}' and pd_donor='{values.existing_donor}'
					""")
	
	def update_gl_entries(voucher_no, doctype):
		query = f"""
				Update `tabGL Entry`
				Set donor = '{values.new_donor}'
				Where docstatus=1 and voucher_no = '{voucher_no}' and donor='{values.existing_donor}'
			"""
		if(doctype != "Purchase Invoice"):
			query = f"""
				Update `tabGL Entry`
				Set party = '{values.new_donor}', donor = '{values.new_donor}'
				Where docstatus=1 and voucher_no = '{voucher_no}' and donor='{values.existing_donor}'
			"""
		frappe.db.sql(query)
	
		
	update_donor_balance_table(values.purchase_invoice)
	update_donor_balance_table(values.purchase_receipt)
	update_donor_balance_table(values.material_request)
	update_donor_balance_table(values.budget)

	update_gl_entries(values.purchase_invoice, "Payment Entry")
	update_gl_entries(values.purhcase_receipt, "Purchase Invoice")
	update_gl_entries(values.material_request, "Material Request")
	update_gl_entries(values.budget, "Budget")

	frappe.msgprint(f"All records are updated from exisitng-donor to new-donor,", alert=1)