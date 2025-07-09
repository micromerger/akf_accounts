import frappe
from frappe.utils import (cint, comma_or, flt, getdate, nowdate, get_link_to_form, fmt_money)
from akf_accounts.customizations.overrides.tax_withholding_category import get_party_tax_withholding_details #mubarrim
import erpnext
import time

# calls on validate 
def apply_tax_matrix(doc, method=None):
	self = doc
	_empty_advance_taxes_and_charges(self)
	set_tax_withholding_income_tax(self)
	set_sales_tax_and_province_tax_withholding(self)
	set_rent_slab(self)

# Nabeel Saleem, 20-06-2025
def _empty_advance_taxes_and_charges(self):
	self.set("taxes", [])	

# Nabeel Saleem, 20-06-2025
def set_tax_withholding_income_tax(self):
	
	if not self.party_type == "Supplier":
		return

	if not self.apply_tax_withholding_amount:
		return

	order_amount = self.get_order_net_total()

	net_total = flt(order_amount) + flt(self.unallocated_amount)

	# Adding args as purchase invoice to get TDS amount
	args = frappe._dict(
		{
			"company": self.company,
			"doctype": "Payment Entry",
			"supplier": self.party,
			"posting_date": self.posting_date,
			"net_total": net_total,
		}
	)

	tax_withholding_details = get_party_tax_withholding_details(args, self.tax_withholding_category)
	
	if not tax_withholding_details:
		return

	tax_withholding_details.update(
		{"cost_center": self.cost_center or erpnext.get_default_cost_center(self.company)}
	)
	
	accounts = []
	for d in self.taxes:
		if d.account_head == tax_withholding_details.get("account_head"):

			# Preserve user updated included in paid amount
			if d.included_in_paid_amount:
				tax_withholding_details.update({"included_in_paid_amount": d.included_in_paid_amount})

			d.update(tax_withholding_details)
		accounts.append(d.account_head)
	
	# Check for an existing Rent Slab row with the same account_head and charge_type
	rent_slab_row_exists = False
	for d in self.taxes:
		if (
			d.account_head == tax_withholding_details.get("account_head")
			and d.charge_type == tax_withholding_details.get("charge_type")
		):
			# Update the row if needed
			if d.included_in_paid_amount:
				tax_withholding_details.update({"included_in_paid_amount": d.included_in_paid_amount})
			d.update(tax_withholding_details)
			rent_slab_row_exists = True

	# Only append if not already present
	if not rent_slab_row_exists:
		self.append("taxes", tax_withholding_details)
	
	to_remove = [
		d
		for d in self.taxes
		if not d.tax_amount and d.account_head == tax_withholding_details.get("account_head")
	]
	
	for d in to_remove:
		self.remove(d)

# S.T and Province
# Nabeel Saleem, 20-06-2025
def set_sales_tax_and_province_tax_withholding(self):
	if not self.party_type == "Supplier":
		return

	if not self.custom_sales_tax_and_province:
		return

	order_amount = self.get_order_net_total()

	net_total = flt(order_amount) + flt(self.unallocated_amount)

	# Adding args as purchase invoice to get TDS amount
	args = frappe._dict(
		{
			"company": self.company,
			"doctype": "Payment Entry",
			"supplier": self.party,
			"posting_date": self.posting_date,
			"net_total": net_total,
		}
	)

	tax_withholding_details = get_party_tax_withholding_details(args, self.custom_tax_withholding_category_st)
	
	if not tax_withholding_details:
		return

	tax_withholding_details.update(
		{"cost_center": self.cost_center or erpnext.get_default_cost_center(self.company)}
	)
	
	accounts = []
	for d in self.taxes:
		if d.account_head == tax_withholding_details.get("account_head"):

			# Preserve user updated included in paid amount
			if d.included_in_paid_amount:
				tax_withholding_details.update({"included_in_paid_amount": d.included_in_paid_amount})

			d.update(tax_withholding_details)
		accounts.append(d.account_head)
	
	# Check for an existing Rent Slab row with the same account_head and charge_type
	rent_slab_row_exists = False
	for d in self.taxes:
		if (
			d.account_head == tax_withholding_details.get("account_head")
			and d.charge_type == tax_withholding_details.get("charge_type")
		):
			# Update the row if needed
			if d.included_in_paid_amount:
				tax_withholding_details.update({"included_in_paid_amount": d.included_in_paid_amount})
			d.update(tax_withholding_details)
			rent_slab_row_exists = True

	# Only append if not already present
	if not rent_slab_row_exists:
		self.append("taxes", tax_withholding_details)
	
	to_remove = [
		d
		for d in self.taxes
		if not d.tax_amount and d.account_head == tax_withholding_details.get("account_head")
	]
	
	for d in to_remove:
		self.remove(d)

def set_rent_slab(self):
	
	if not self.party_type == "Supplier":
		return

	if not self.custom_apply_rent_slab:
		return

	order_amount = self.get_order_net_total()

	net_total = flt(order_amount) + flt(self.unallocated_amount)

	# Adding args as purchase invoice to get TDS amount
	args = frappe._dict(
		{
			"company": self.company,
			"doctype": "Payment Entry",
			"supplier": self.party,
			"posting_date": self.posting_date,
			"net_total": net_total,
		}
	)

	def get_rent_slab_details():
		result = frappe.db.sql(f'''
			Select 
				ts.idx,
				rs.add_deduct_tax, 
				rs.account_head,
				rs.category, 
				rs.charge_type, 
				ts.percent_deduction as rate, 
				"Rent Slab" as description,
				ts.formula

			From `tabRent Slab` rs inner join `tabTaxable Rent Slab` ts on (rs.name=ts.parent)

			Where 
				rs.docstatus=1
				and rs.company = "{self.company}"
				and ts.tax_payer_status_id='{self.custom_tax_payer_status}'
				and ts.supplier_type_tax_payer_category ='{self.custom_tax_payer_category_id}'
				and {self.paid_amount} between ts.from_amount and ts.to_amount	
		''', as_dict=1)
		return result[0] if(result) else {}
  
	tax_withholding_details = get_rent_slab_details()
	
	if not tax_withholding_details:
		return

	tax_withholding_details.update(
		{"cost_center": self.cost_center or erpnext.get_default_cost_center(self.company)}
	)
	
	accounts = []
	for d in self.taxes:
		if d.account_head == tax_withholding_details.get("account_head"):

			# Preserve user updated included in paid amount
			if d.included_in_paid_amount:
				tax_withholding_details.update({"included_in_paid_amount": d.included_in_paid_amount})

			d.update(tax_withholding_details)
		accounts.append(d.account_head)

	
	# Check for an existing Rent Slab row with the same account_head and charge_type
	rent_slab_row_exists = False
	for d in self.taxes:
		if (
			d.account_head == tax_withholding_details.get("account_head")
			and d.charge_type == tax_withholding_details.get("charge_type")
		):
			# Update the row if needed
			if d.included_in_paid_amount:
				tax_withholding_details.update({"included_in_paid_amount": d.included_in_paid_amount})
			d.update(tax_withholding_details)
			rent_slab_row_exists = True

	amount = eval_condition_and_formula(self, tax_withholding_details)
	tax_withholding_details.update({"tax_amount": amount})
	
	# Only append if not already present
	if not rent_slab_row_exists:
		self.append("taxes", tax_withholding_details)
	
	to_remove = [
		d
		for d in self.taxes
		if not d.tax_amount and d.account_head == tax_withholding_details.get("account_head")
	]
	
	for d in to_remove:
		self.remove(d)

def eval_condition_and_formula(self, struct_row):
	from frappe import _, msgprint
	from hrms.payroll.utils import sanitize_expression
	from akf_hrms.overrides.salary_slip  import _safe_eval, throw_error_message
	data = frappe._dict({
		"paid_amount": self.paid_amount
	})

	self.whitelisted_globals = {
			"int": int,
			"float": float,
			"long": int,
			"round": round,
			# "date": date,
			# "getdate": getdate,
			# "ceil": ceil,
			# "floor": floor,
		}

	try:
		
		'''condition = sanitize_expression(struct_row.condition)
		if condition:
			if not _safe_eval(condition, self.whitelisted_globals, data):
				return None
		amount = struct_row.amount
		if struct_row.amount_based_on_formula:
			formula = sanitize_expression(struct_row.formula)
			if formula:
				amount = flt(
					_safe_eval(formula, self.whitelisted_globals, data), struct_row.precision("amount")
				)
		if amount:
			data[struct_row.abbr] = amount

		return amount '''
		
		# formula = sanitize_expression('(600000-300000)*0.05 + (paid_amount-600000)* .1')
		formula = sanitize_expression(struct_row.formula)
		if formula:
			amount = flt(
				_safe_eval(formula, self.whitelisted_globals, data)
				# _safe_eval(formula, self.whitelisted_globals, data), struct_row.precision("amount")
			)
			return amount
		
		return 0

	except NameError as ne:
		throw_error_message(
			struct_row,
			ne,
			title=_("Name error"),
			description=_("This error can be due to missing or deleted field."),
		)
	except SyntaxError as se:
		throw_error_message(
			struct_row,
			se,
			title=_("Syntax error"),
			description=_("This error can be due to invalid syntax."),
		)
	except Exception as exc:
		throw_error_message(
			struct_row,
			exc,
			title=_("Error in formula or condition"),
			description=_("This error can be due to invalid formula or condition."),
		)

def submit_sales_tax_provision_gl_entry(doc, method=None):
	self = doc

	if not self.party_type == "Supplier":
		return

	if not self.custom_sales_tax_and_province:
		return

	
	def get_gl_entry_dict():
		return frappe._dict({
			'doctype': 'GL Entry',
			'posting_date': self.posting_date,
			'transaction_date': self.posting_date,
			'against': f"{self.doctype}: {self.name}",
			'against_voucher_type': self.doctype,
			'against_voucher' : self.name,
			'voucher_type': self.doctype,
			'voucher_subtype': 'Pay',
			'voucher_no': self.name,
			"company": self.company,
		})

	def get_supplier_account():
		supplier_account = frappe.db.sql(f'''
							Select account 
							From `tabParty Account` 
							Where docstatus=0 
							and parent="{self.custom_supplier}" ''')
		if(not supplier_account):
			sp_link = get_link_to_form('Supplier', self.custom_supplier)
			frappe.throw(f"Please select default account of supplier ` <br>{sp_link}.", 
				title="Missing Info")
		return supplier_account[0][0]


	def get_tax_wh_payable_account():
		comp = frappe.get_doc('Company', self.company)
		
		if(not comp.custom_tax_withholding_payable_account):
			wh_link = get_link_to_form('Company', comp.name)
			frappe.throw(f"Please select tax withholding payable account in company. <br>{wh_link}.", 
				title="Missing Info")
		
		return comp.custom_tax_withholding_payable_account
	
	from akf_accounts.akf_accounts.doctype.donation.donation import get_currency_args
	
	args =  get_gl_entry_dict()
	cargs = get_currency_args()
	args.update(cargs)
	tax_amount = [d.tax_amount for d in self.taxes if(d.description == self.custom_tax_withholding_category_st)][0] or 0.0

	supplier_account = get_supplier_account()
	temp_tax_wh_payable_account = get_tax_wh_payable_account()
	
	args.update({
		"party_type": "Supplier",
		"party": self.custom_supplier,
		"cost_center": self.cost_center,
		"service_area": self.service_area,
		"subservice_area": self.subservice_area,
		"product": self.product,
		"project": self.project,
		"fund_class": self.fund_class,
		"donor": self.donor,
  
		'account': temp_tax_wh_payable_account,
		'credit': tax_amount,
		'credit_in_account_currency': tax_amount,
		"credit_in_transaction_currency": tax_amount,
		# "transaction_currency": row.currency,
	})
	doc = frappe.get_doc(args)
	doc.insert(ignore_permissions=True)
	doc.submit()

	# create j.e to settle payable entry for tax to pay to government taxation department.
	make_sales_tax_provision_journal_entry(self, supplier_account, temp_tax_wh_payable_account, tax_amount)

def make_sales_tax_provision_journal_entry(self, supplier_account, temp_tax_wh_payable_account, tax_amount):
	
	def _create_():
		reference_doctype = "Payment Entry"
		reference_name = self.name
		args = {
			"doctype": "Journal Entry",
			"entry_type": "Journal Entry",
			"posting_date": self.posting_date,
			"company": self.company,
			"remark": "The sales tax and province of {0} has been recorded against {1} {2}".format(fmt_money(tax_amount, currency=self.paid_to_account_currency), "Purchase Invoice", reference_name),
			"accounts": [
				# debit
				{
					"account": supplier_account,
					"party_type": self.party_type,
					"party": self.custom_supplier,
					"cost_center": self.cost_center,
					"credit_in_account_currency": tax_amount,
					"credit": tax_amount,
					# "debit_in_account_currency": tax_amount,
					# "debit": tax_amount,
					# "reference_type": reference_doctype,
					# "reference_name": reference_name
				},
				# credit
				{
					"account": temp_tax_wh_payable_account,
					"party_type": self.party_type,
					"party": self.custom_supplier,
					"cost_center": self.cost_center,
					"debit_in_account_currency": tax_amount,
					"debit": tax_amount,
					# "credit_in_account_currency": tax_amount,
					# "credit": tax_amount,
					"reference_type": reference_doctype,
					"reference_name": reference_name
				}
			]
		}
		doc = frappe.get_doc(args)
		doc.insert(ignore_permissions=True)
		doc.submit()
		frappe.db.set_value("Payment Entry", self.name, "custom_journal_entry_st", doc.name)
		
	_create_()
	self.reload()
