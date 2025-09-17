import frappe
from frappe.utils import fmt_money
from erpnext.accounts.utils import get_company_default

def validations(self):
	if(self.is_new()): return
	if(self.custom_type_of_transaction=="Normal"): return
	if(not get_company_default(self.company, "custom_enable_accounting_dimensions_dialog", ignore_validation=True)): 
		self.set("custom_program_details", [])
		return

	donor_balance = sum([d.actual_balance for d in self.custom_program_details])
	item_amount = sum([d.amount for d in self.items])

	if(not self.custom_program_details):
		frappe.throw("Balance is required to proceed further.", title='Donor Balance')
	if(item_amount> donor_balance):
		frappe.throw(f"Item amount: <b>Rs.{fmt_money(item_amount)}</b> exceeding the available balance: <b>Rs.{fmt_money(donor_balance)}</b>.", title='Donor Balance')
