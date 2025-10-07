# Developer Aqsa Abbasi
import frappe
from frappe.model.document import Document
import json
import datetime
from erpnext.accounts.utils import get_fiscal_year
from frappe.utils import (
    getdate, today, fmt_money, get_link_to_form
)
# from akf_accounts.customizations.overrides.cdoctype.project.financial_stats import (
#     get_transactions
# )
from akf_accounts.utils.dimensional_donor_balance import (
	get_donor_balance
)
# from frappe import today

from akf_accounts.akf_accounts.doctype.funds_transfer.gl_entries.inter_fund_project import (
	make_inter_fund_project_gl_entries
)
from akf_accounts.akf_accounts.doctype.funds_transfer.gl_entries.inter_fund_class import (
	make_inter_fund_class_gl_entries
)
from akf_accounts.akf_accounts.doctype.funds_transfer.gl_entries.inter_branch import (
	first_workflow_gl_entry_inter_branch,
	second_workflow_gl_entry_inter_branch,
	without_workflow_inter_branch
)

from akf_accounts.akf_accounts.doctype.funds_transfer.gl_entries.inter_bank import (
    make_inter_bank_gl_entries
)

class FundsTransfer(Document):
	def validate(self):
		self.posting_date = today()
		self.validate_cost_center()
		self.validate_inter_branch_accounts()
		self.validate_inter_bank()
		self.validate_receiving_date()
		self.donor_list_data_funds_transfer(is_valid=True)
		self.update_funds_tranfer_from()
		self.set_deduction_breakeven()
		self.calculate_totals()

	def validate_cost_center(self):
		if self.transaction_purpose == 'Inter Branch':
			if self.from_cost_center == self.to_cost_center:
				frappe.throw("Cost Centers cannot be same in Inter Branch Transfer")

	def validate_inter_branch_accounts(self):
		if self.transaction_purpose == 'Inter Branch':
			self.transfer_type = ""
			if self.from_bank_account == self.to_bank_account:
				frappe.throw("Banks cannot be same in Inter Branch Transfer")
			if (not self.desposit_in_transit_account or not self.ibft_equity_account):
				clink = get_link_to_form("Company", self.company)
				frappe.throw(f"[Desposit In Transit Account, IBFT (Equity) Account] are need to be set in company {clink}", title="Inter Branch (Accounts Settings)")

	def validate_inter_bank(self):
		if self.transaction_purpose == 'Inter Bank':
			self.transfer_type = ""
			if self.account_balance_from <= 0.0:
				frappe.throw(f"ZERO balance in {self.from_bank}", title="No Balance")
			if self.account_balance_from < self.transfer_amount :
				frappe.throw(f"Transfer to <b>{self.transfer_amount}</b> is greater than available balance <b>{self.account_balance_from}</b>", title="Exceeding balance")
	
	def validate_receiving_date(self):
		posting_date = getdate(self.posting_date)		
		receiving_date = getdate(self.receiving_date)
		if(receiving_date < posting_date):
			frappe.throw(f"Receiving date cannot be less than posting date.", title="Invalid Dates")

	@frappe.whitelist()
	def update_funds_tranfer_from(self):
		if(self.transaction_purpose == "Inter Fund" and self.transaction_purpose == "Fund Project"):
			total_transfer_amount = 0
			for row in self.funds_transfer_to:
				amount = row.ft_amount
				if(amount<=0.0):
					frappe.throw(f"""In <b>Row#{row.idx}</b>, the amount cannot be negative or zero to transfer.""", 
						title="Funds Transfer To")
				total_transfer_amount += amount
			
			total_available_balance = 0

			temp_total_transfer_amount = total_transfer_amount
			# update the transfer-amount and also calcuate total balance.
			for row in self.funds_transfer_from:
				balance_amount = row.ff_balance_amount
				total_available_balance += balance_amount # calcuate total balance

				row.ff_transfer_amount =  0
				row.transfer = False

				if(temp_total_transfer_amount > 0 and temp_total_transfer_amount <= balance_amount):
					row.ff_transfer_amount =  temp_total_transfer_amount
					row.transfer = 1
					temp_total_transfer_amount = 0

				if(temp_total_transfer_amount > balance_amount):
					row.ff_transfer_amount = balance_amount
					row.transfer = 1
					temp_total_transfer_amount = (temp_total_transfer_amount - balance_amount)
				

			# Show message to user you're exceeding balance limit.
			if(total_transfer_amount > total_available_balance):
				frappe.throw(f"""
						Transfer amount: <b>{fmt_money(total_transfer_amount, currency="PKR")}</b> 
						<br> 
						Available amount: <b>{fmt_money(total_available_balance, currency="PKR")}</b>
						<br>
						Differecne: <b>{fmt_money((total_transfer_amount - total_available_balance), currency="PKR")}</b>""", 
						title="Exceeding available balance")


	@frappe.whitelist()
	def set_deduction_breakeven(self):
		if(self.transaction_purpose=='Inter Branch'): 
			from akf_accounts.akf_accounts.doctype.funds_transfer.deduction_breakeven import apply_deduction_breakeven
			apply_deduction_breakeven(self)
		else: self.set("deduction_breakeven", [])

	def calculate_totals(self):
		self.total_amount = sum(d.ft_amount for d in self.funds_transfer_to)
		self.total_deduction = sum(d.amount for d in self.deduction_breakeven)
		self.outstanding_amount = (self.total_amount - self.total_deduction)

	@frappe.whitelist()
	def donor_list_data_funds_transfer(self, is_valid=False):
		
		def validate_balance(row, financial_stats):
			if(is_valid and (not financial_stats)):
				frappe.throw(f"""<b>Row#{row.idx}</b>; no balance exists for <b>{row.ff_donor}</b> with provided details""", 
							title="Funds Transfer From")
		
		def execute_funds_transfer_from():
			filters = set()
			for row in self.funds_transfer_from:
				filters = {
					'company': row.ff_company,
					'cost_center': row.ff_cost_center,
					'project': row.project,				
					'fund_class': row.fund_class,
					'service_area': row.ff_service_area,
					'subservice_area': row.ff_subservice_area,
					'product': row.ff_product,
					'donor': row.ff_donor,
					'donor_type': row.donor_type,
					'donor_desk': row.donor_desk,
					'intention': row.donation_type,
					'transaction_type': row.transaction_type,
					'account': row.ff_account,
					'amount': row.ff_transfer_amount
				}
				# financial_stats = get_transactions(filters) # get complete stats
				financial_stats = get_donor_balance(filters)
				# print('|--------------------------|')
				# print(financial_stats)
				validate_balance(row, financial_stats) # validate balance against filters
				
				# donor_entries = get_donor_entries(condition)
	
		if(self.docstatus==0): execute_funds_transfer_from()

	def on_update(self): 
		first_workflow_gl_entry_inter_branch(self)

	def on_submit(self):
		make_inter_fund_project_gl_entries(self) # Project only
		make_inter_fund_class_gl_entries(self) # Fund Class only
		without_workflow = second_workflow_gl_entry_inter_branch(self) # Inter Branch
		if(without_workflow): without_workflow_inter_branch(self)
		make_inter_bank_gl_entries(self) # Inter Bank
		
	def on_trash(self):
		self.delete_all_gl_entries()

	def on_cancel(self):
		self.delete_all_gl_entries()

	def delete_all_gl_entries(self):
		frappe.db.sql("DELETE FROM `tabGL Entry` WHERE voucher_no = %s", self.name)
		if(hasattr(self, 'workflow_state')): 
			frappe.db.set_value(self.doctype, self.name, 'workflow_state', 'Cancelled') 
			self.reload
