import frappe
from frappe.model.mapper import get_mapped_doc
from frappe.utils import (get_link_to_form, getdate, fmt_money)
from akf_accounts.akf_accounts.doctype.donation.donation import get_currency_args
from akf_accounts.utils.accounts_defaults import get_company_defaults
from erpnext.accounts.utils import get_company_default

# VALIDATION ################################
def validate_donor_balance(doc, method=None):
	self = doc
	if(self.is_new()): return
	if(not self.fund_class): return
	if(not self.custom_program_details): return
	if(not get_company_default(self.company, "custom_enable_accounting_dimensions_dialog", ignore_validation=True)): 
		self.set("custom_program_details", [])
		return
	accountsBalance = self.estimated_costing or 0.0
	donorBalnce = sum([d.actual_balance for d in self.custom_program_details]) or 0.0

	if(donorBalnce<=0.0):
		frappe.throw("Balance is required to proceed further.", title='Donor Balance')
	if(accountsBalance>donorBalnce):
		frappe.throw(f"Budget amount <b>Rs.{fmt_money(accountsBalance)}</b> exceeding the available balance <b>Rs.{fmt_money(donorBalnce)}</b>.", title='Budget Accounts')

# GL ENTRIES ################################
def make_project_encumbrance_gl_entries(doc, method=None):
	self = doc
	if(self.fund_class in ["", None]): return
	if(not get_company_default(self.company, "custom_enable_accounting_dimensions_dialog", ignore_validation=True)): 
		frappe.throw("Please enable accounting dimensions dialog in company 'AKFP Accounts' tab.", title=f'{self.company}')
	# consumed amount
	consumed_amount = self.estimated_costing or 0.0
	# looping for gl entry
	for row in self.custom_program_details:
		balance_amount = row.actual_balance
		
		if(balance_amount<=consumed_amount):
			# consumed_amount = (7000 - 5000) = 2000
			consumed_amount = (consumed_amount - balance_amount)
			# gl entry
			make_debit_normal_equity_account(self, row, balance_amount)
			make_credit_temporary_encumbrance_project(self, row, balance_amount)

		elif(consumed_amount>0 and balance_amount>consumed_amount):
			# gl entry
			make_debit_normal_equity_account(self,  row, consumed_amount)
			make_credit_temporary_encumbrance_project(self, row, consumed_amount)
			consumed_amount = 0
	
	frappe.msgprint("Funds has been transfered to project successfully.", indicator="green", alert=1)

def get_args(self):
	posting_date = getdate()
	return frappe._dict({
			'doctype': 'GL Entry',
			'posting_date': posting_date,
			'transaction_date': posting_date,
			'against': f"Project: {self.name}",
			'against_voucher_type': "Fund Class",
			'against_voucher': self.fund_class,
			'voucher_type': self.doctype,
			'voucher_no': self.name,
			'voucher_subtype': 'Receive',
			'remarks': f"Project: Encumbrance of project: {self.name} on {self.expected_start_date}",
			'is_opening': 'No',
			'is_advance': 'No',
			'company': self.company,
		})

def make_debit_normal_equity_account(self, row, amount):
	args = get_args(self)
	cargs = get_currency_args()
	args.update(cargs)
	args.update({
		'party_type': 'Donor',
		'party': row.pd_donor,
		'account': row.pd_account,
		'cost_center': row.pd_cost_center,
		'fund_class': self.fund_class,	
		'service_area': row.pd_service_area,
		'subservice_area': row.pd_subservice_area,
		'product': row.pd_product,
		'donor_desk': row.donor_desk,
		'donation_type': row.donation_type,
		'donor': row.pd_donor,
		'debit': amount,
		'debit_in_account_currency': amount,
		'transaction_currency': row.currency,
		'debit_in_transaction_currency': amount,
	})
	doc = frappe.get_doc(args)
	# frappe.throw(frappe.as_json(doc))
	doc.insert(ignore_permissions=True)
	
	doc.submit()

def make_credit_temporary_encumbrance_project(self, row, amount):
	args = get_args(self)
	cargs = get_currency_args()	
	args.update(cargs)
	args.update({
		'party_type': 'Donor',
		'party': row.pd_donor,
		'account': row.encumbrance_project_account,
		'cost_center': row.pd_cost_center,
		'fund_class': self.fund_class,		
		'service_area': row.pd_service_area,
		'subservice_area': row.pd_subservice_area,
		'product': row.pd_product,
		'project': self.name,
		'donor': row.pd_donor,
		'donor_desk': row.donor_desk,
		'donation_type': row.donation_type,
		'credit': amount,
		'credit_in_account_currency': amount,
		'transaction_currency': row.currency,
		'credit_in_transaction_currency': amount,
	})
	doc = frappe.get_doc(args)
	doc.insert(ignore_permissions=True)
	doc.submit()
	
def cancel_project_encumbrance_gl_entries(doc, method=None):
	self = doc
	if(not get_company_default(self.company, "custom_enable_accounting_dimensions_dialog", ignore_validation=True)): return
	if(frappe.db.exists('GL Entry', {'voucher_no': self.name})):
		frappe.db.sql(f""" Delete from `tabGL Entry` where voucher_no = '{self.name}' """)


"""
	*** Function works in case of funds tranfer from 'Fund Class' to 'Project'
"""
# akf_accounts.utils.encumbrance.enc_project.make_transfer_funds_gl_entries
@frappe.whitelist()
def make_transfer_funds_gl_entries(doc, donor_balance, transfer_to=None):
	from erpnext.accounts.doctype.account.account import get_account_currency

	doc = frappe.parse_json(doc)
	donor_balance = frappe.parse_json(donor_balance)

	transfer_to = (transfer_to or "").strip().lower()

	if transfer_to == "fund class":
		source_fund_class = doc.get("fund_class")  # The fund class you are transferring FROM
		target_fund_class = doc.get("target_fund_class")  # The fund class you are transferring TO
		company = doc.get("company")

		source_equity_account = frappe.db.get_value(
			"Accounts Default",
			{"parent": source_fund_class, "company": company},
			"equity_account"
		)
		target_equity_account = frappe.db.get_value(
			"Accounts Default",
			{"parent": target_fund_class, "company": company},
			"equity_account"
		)

		for detail in donor_balance:
			detail = frappe._dict(detail)
			amount = float(detail.get("amount") or 0)
			if amount <= 0:
				continue

			currency = get_account_currency(source_equity_account)
			posting_date = getdate()
			cost_center = detail.get("pd_cost_center")

			# Debit source fund class equity account
			gl_debit = frappe.get_doc({
				"doctype": "GL Entry",
				"posting_date": posting_date,
				"account": source_equity_account,
				
				"debit": amount,
				"debit_in_account_currency": amount,
				"company": company,
				"remarks": f"Transfer from Fund Class {source_fund_class} to {target_fund_class}",
				"voucher_type": "Fund Class",
				"voucher_no": source_fund_class,
				"is_opening": "No",
				"is_advance": "No",
				"transaction_currency": currency,
				"debit_in_transaction_currency": amount,
				"project": "",

				"fund_class": source_fund_class,
				"service_area": detail.get("pd_service_area"),
				"subservice_area": detail.get("pd_subservice_area"),
				"product": detail.get("pd_product"),
				"donor": detail.get("pd_donor"),
				"donor_desk": detail.get("donor_desk"),
				"donation_type": detail.get("donation_type"),
				"cost_center": cost_center,
			})
			gl_debit.insert(ignore_permissions=True)
			gl_debit.submit()

			# Credit target fund class equity account
			currency = get_account_currency(target_equity_account)
			gl_credit = frappe.get_doc({
				"doctype": "GL Entry",
				"posting_date": posting_date,
				"account": target_equity_account,
				
				"credit": amount,
				"credit_in_account_currency": amount,
				"company": company,
				"remarks": f"Transfer from Fund Class {source_fund_class} to {target_fund_class}",
				"voucher_type": "Fund Class",
				"voucher_no": target_fund_class,
				"is_opening": "No",
				"is_advance": "No",
				"transaction_currency": currency,
				"credit_in_transaction_currency": amount,
				"project": "",

				"fund_class": target_fund_class,
				"service_area": detail.get("pd_service_area"),
				"subservice_area": detail.get("pd_subservice_area"),
				"product": detail.get("pd_product"),
				"donor": detail.get("pd_donor"),
				"donor_desk": detail.get("donor_desk"),
				"donation_type": detail.get("donation_type"),
				"cost_center": cost_center,
			})
			gl_credit.insert(ignore_permissions=True)
			gl_credit.submit()

		# # --- NEW: Update Fund Class child table ---
		# fund_class_doc = frappe.get_doc("Fund Class", doc.get("target_fund_class"))
		# enriched_rows = []
		# for detail in donor_balance:
		# 	# If detail is a dict, parse as needed
		# 	if isinstance(detail, str):
		# 		detail = frappe.parse_json(detail)
		# 	# Add currency and pd_fund_class
		# 	detail["currency"] = get_account_currency(detail["pd_account"])
		# 	detail["pd_fund_class"] = doc.get("target_fund_class")
		# 	enriched_rows.append(detail)
		# fund_class_doc.set("custom_program_details", enriched_rows)
		# fund_class_doc.save(ignore_permissions=True)
		# --- END NEW ---

		frappe.msgprint(
			f"Funds have been transferred to Fund Class: {doc.get('target_fund_class')}",
			indicator="green",
			alert=1
		)
		return

	if transfer_to == "project":
		if not doc.get("custom_project"):
			frappe.msgprint("No project selected, skipping Project transfer logic.", indicator="orange", alert=1)
			return

		# Default: Project transfer (existing logic)
		_doc_ = frappe._dict()
		_doc_.update({
			'doctype': "Project",        
			'company': doc.company,
			'name': doc.custom_project,
			'fund_class': doc.fund_class,
			'estimated_costing': doc.estimated_costing
		})

		idx = 0
		project_doc = frappe.get_doc("Project", doc.custom_project)

		for detail in donor_balance:
			detail = frappe.parse_json(detail)
			donor_balance[idx] = detail.update({
				"currency": get_account_currency(detail.pd_account),
				"pd_fund_class": doc.fund_class
			})
			project_doc.append("custom_program_details", detail)
			idx = idx + 1

		_doc_.update({"custom_program_details": donor_balance})

		# process 01
		project_doc.save(ignore_permissions=True)
		# process 02
		make_project_encumbrance_gl_entries(_doc_)
		return

	# If neither, do nothing or show a warning
	frappe.msgprint("No valid transfer type selected.", indicator="orange", alert=1)
	return
