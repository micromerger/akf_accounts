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
	
	def update_payment_entry():
		payment_entries = eval(values.payment_entry)
		for pid in payment_entries:
			update_gl_entries(pid, "Payment Entry")
			frappe.db.set_value("Payment Entry", pid, "donor", values.new_donor)

	update_donor_balance_table(values.purchase_invoice)
	update_donor_balance_table(values.purchase_receipt)
	update_donor_balance_table(values.material_request)
	update_donor_balance_table(values.budget)

	update_gl_entries(values.purhcase_receipt, "Purchase Invoice")
	update_gl_entries(values.material_request, "Material Request")
	update_gl_entries(values.budget, "Budget")
	
	update_payment_entry()
	
	frappe.msgprint(f"All records are updated from exisitng-donor to new-donor.", alert=1)