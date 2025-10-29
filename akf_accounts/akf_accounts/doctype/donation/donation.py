import frappe, ast, json
from frappe.model.document import Document
from frappe.utils import get_link_to_form
from erpnext.accounts.utils import get_balance_on
from erpnext.setup.utils import get_exchange_rate
from frappe.core.doctype.communication.email import make

from akf_accounts.akf_accounts.doctype.donation.in_kind_donation import (
    calculate_in_kind_totals,
	make_stock_entry_for_in_kind_donation
)


class Donation(Document):
	def validate(self):
		self.validate_payment_details()
		self.validate_deduction_percentages()
		self.validate_pledge_contribution_type()
		# self.validate_is_return()
		self.set_deduction_breakeven()
		self.update_status()
		calculate_in_kind_totals(self)

	def before_submit(self):
		self.validate_is_return()


	def set_exchange_rate(self):
		exchange_rate = get_exchange_rate(self.currency, self.to_currency, self.posting_date)
		if(exchange_rate): self.exchange_rate = exchange_rate
	
	def validate_payment_details(self):
		if(len(self.payment_detail)<1 and self.donation_type=="Cash"):
			frappe.throw("Please provide, payment details to proceed further.")

	def validate_deduction_percentages(self):
		for row in self.get('deduction_breakeven'):
			if row.account:
				# min_percentage, max_percentage = get_min_max_percentage(row.service_area, row.account)
				min_percentage, max_percentage = get_min_max_percentage(row.fund_class, row.account)
				if min_percentage is not None and max_percentage is not None:
					if row.percentage < min_percentage or row.percentage > max_percentage:
						frappe.throw(f"Row#{row.idx}; Percentage for account '{row.account}' must be between {min_percentage}% and {max_percentage}%.")

	def validate_pledge_contribution_type(self):
		if(self.contribution_type!="Pledge"):
			msg = []
			for d in self.payment_detail:
				if(not d.mode_of_payment):
					msg+=[" Mode of Payment"]
				if(not d.transaction_no_cheque_no and not d.reference_date and d.mode_of_payment!="Cash"):
					msg+=["Transaction No/Cheque No"]
				if(not d.account_paid_to):
					msg+=["Account Paid To"]
				if(msg): 
					msg = f"<b>Row#{d.idx}:</b> {msg}"
					frappe.throw(msg=f"{msg}", title="Payment Detail")

	@frappe.whitelist()
	def set_deduction_breakeven(self):

		def reset_mode_of_payment(row):
			if(self.contribution_type == "Pledge"):
				return
			elif(self.donor_identity in ["Merchant - Known", "Merchant - Unknown"]):
				row.mode_of_payment = self.mode_of_payment
				row.account_paid_to = self.account_paid_to
			
		def get_deduction_details(row, deduction_breakeven):
			# Added by Aqsa
			# Mobeen said no deduction only on Zakat
			# if (row.intention in [None, "Zakat", "Fitrana", "Sadqa Jaria", "Sadqaat" , "Cash"]):
			'''Deduction in case of Pledge again applied on request of Zubair Khan, Usama. 15-09-2025'''
			# if (row.intention in [None, "Zakat"]) or (self.contribution_type=='Pledge'):
			if (row.intention in [None, "Zakat"]): 
				return []

			_breakeven = [d for d in deduction_breakeven if(d.random_id == row.random_id)]
			
			if (_breakeven):
				return _breakeven

			'''
				and parent = '{row.pay_service_area}'		
				and project = '{row.project}'	
			'''
			result = frappe.db.sql(f"""
					SELECT 
						company, income_type,
						project, 
						account, 
						percentage, 
						min_percent, 
						max_percent
						
					FROM 
						`tabDeduction Details` dd
					WHERE 
						ifnull(account, "")!=""
						and company = '{self.company}'
						and parenttype="Fund Class"
						and parent = '{row.fund_class}'
					""", as_dict=True)
			
			return result

		def set_deduction_details(row, args):
			args.update({
					"random_id": row.random_id,
					"company": self.company,

					# "project": args.project, # for income-type		
					"cost_center": self.donation_cost_center,				
					"fund_class": row.fund_class,
					"service_area": row.pay_service_area,
					"subservice_area": row.pay_subservice_area,
					"product": row.pay_product,
					"donor": row.donor,
					"donor_type": row.donor_type,				
					"donor_desk": row.donor_desk,
					"intention": row.intention,
					"transaction_type": row.transaction_type,

					"donation_amount": row.donation_amount,
					"amount": percentage_amount,
					"base_amount": base_amount
					
					})
			self.append("deduction_breakeven", args)

		'''def get_default_accounts(service_area, fieldname):
			return frappe.db.get_value('Accounts Default', {'parent': service_area, 'company': self.company}, fieldname)
		'''
		def get_default_accounts(fund_class, fieldname):
			return frappe.db.get_value('Accounts Default', {'parent': fund_class, 'company': self.company}, fieldname)
		
		def get_default_donor_account(donor, fieldname):
			return frappe.db.get_value('Donor', {'name': donor}, fieldname)

		def set_total_donors():
			self.total_donors = len(self.payment_detail)

		def verify_unique_receipt_no(row):
			if(not row.receipt_number): return
			receipt_list = [d.idx for d in self.payment_detail if(row.receipt_number == d.receipt_number and row.idx!=d.idx)]
			if(receipt_list):
				frappe.throw(f"Receipt#<b>{row.receipt_number}</b> in row#<b>{row.idx}</b> is already used in another row.", title='Receipt No.')
		
		# 31-12-2024 nabeel saleem
		def validate_active_donor(row):
			if(frappe.db.exists("Donor", {"name": row.donor, "status": "Blocked"})):
				frappe.throw(f"<b>Row#{row.idx}</b> donor: {row.donor} is blocked.", title='Blocked Donor.')
				
		# 31-12-2024 nabeel saleem
		def validate_donor_currency(row):
			if(row.donor):
				if(not frappe.db.exists("Donor", {"name": row.donor, "default_currency": self.currency})):
					donor = get_link_to_form("Donor", row.donor)
					frappe.throw(f"<b>Row#{row.idx}</b> donor: {donor} currency is not {self.currency}.", title='Currency conflict')

		if(self.donation_type=="Cash"):
			deduction_breakeven = self.deduction_breakeven
			self.set("deduction_breakeven", [])
			deduction_amount=0
			total_donation=0
			
			for row in self.payment_detail:
				# print("payment_detail: ", row.random_id)
				validate_active_donor(row)
				validate_donor_currency(row)
				verify_unique_receipt_no(row)
				reset_mode_of_payment(row)
				total_donation+= row.donation_amount
				# Setup Deduction Breakeven
				temp_deduction_amount=0
				# Looping
				""" _breakeven = [d for d in deduction_breakeven if(d.random_id == row.random_id)]
				_deduction_breakeven = _breakeven if(_breakeven) else get_deduction_details(row) """
				for args in get_deduction_details(row, deduction_breakeven):
					# print("_deduction_breakeven: ", args.random_id)
					percentage_amount = 0
					base_amount = 0
					
					if(row.donation_amount>0 or self.is_return):
						percentage_amount = row.donation_amount*(args.percentage/100)
						base_amount = self.apply_currecny_exchange(percentage_amount)
						temp_deduction_amount += percentage_amount
					
					set_deduction_details(row, args)			
				
				'''row.equity_account = get_default_accounts(row.pay_service_area, 'equity_account')'''
				row.equity_account = get_default_accounts(row.fund_class, 'equity_account')
				default_receivable_account = get_default_donor_account(row.donor, "default_account")
				row.receivable_account = default_receivable_account if(default_receivable_account) else get_default_accounts(row.pay_service_area, 'receivable_account')
				
				row.cost_center = self.donation_cost_center
				# Total Deduction Amount
				deduction_amount += temp_deduction_amount
				# account_currency
				row.deduction_amount = temp_deduction_amount  
				row.net_amount = (row.donation_amount-row.deduction_amount)
				row.outstanding_amount = row.donation_amount if(self.contribution_type=="Pledge") else row.net_amount
				# company_currency
				row.base_donation_amount = self.apply_currecny_exchange(row.donation_amount)
				row.base_deduction_amount = self.apply_currecny_exchange(temp_deduction_amount)
				row.base_net_amount = self.apply_currecny_exchange(row.net_amount)
				row.base_outstanding_amount = self.apply_currecny_exchange(row.outstanding_amount)
		
			# calculate total
			set_total_donors()
			self.calculate_total(total_donation, deduction_amount)

	@frappe.whitelist()
	def update_deduction_breakeven(self):
		""" in case of return """
		deduction_amount=0
		total_donation=0
		
		deduction_breakeven = self.deduction_breakeven
		breakeven_list = []
		for row1 in self.payment_detail:
			total_donation+= row1.donation_amount
			row1.base_donation_amount = self.apply_currecny_exchange(row1.donation_amount)
			# Setup Deduction Breakeven
			temp_deduction_amount=0
			
			for row2 in deduction_breakeven:
				if(row1.random_id == row2.random_id):
					percentage_amount = 0
					base_amount = 0
					
					if(row1.donation_amount>0 or self.is_return):
						percentage_amount = row1.donation_amount*(row2.percentage/100)
						base_amount = self.apply_currecny_exchange(percentage_amount)
						temp_deduction_amount += percentage_amount

					args = {
					"random_id": row1.random_id,
									
					"income_type": row2.income_type,
    				"project": row2.project,
					"account": row2.account, 

					"percentage": row2.percentage, 
					"min_percent": row2.min_percent, 
					"max_percent": row2.max_percent,

					"company": row2.company, 
					"cost_center": row1.cost_center,
					"fund_class": row1.fund_class,
					"service_area": row1.pay_service_area,
					"subservice_area": row1.pay_subservice_area,
					"product": row1.pay_product,
					"donor": row1.donor,
					"donor_type": row1.donor_type,
					"donor_desk": row1.donor_desk,
					"intention": row1.intention,
					"transaction_type": row1.transaction_type,
     
					"donation_amount": row1.donation_amount,
					"amount": percentage_amount,
					"base_amount": base_amount,

					"payment_detail_id": row1.idx,
					}
					breakeven_list.append(args)
		
			row1.deduction_amount = temp_deduction_amount    
			row1.net_amount = (row1.donation_amount-row1.deduction_amount)
			row1.outstanding_amount = row1.donation_amount if(self.contribution_type=="Pledge") else row1.net_amount
			row1.base_outstanding_amount = self.apply_currecny_exchange(row1.outstanding_amount)
			deduction_amount += temp_deduction_amount
		
		self.set("deduction_breakeven", breakeven_list)
		self.calculate_total(total_donation, deduction_amount)

	def apply_currecny_exchange(self, amount):
		if(self.currency):
			if(self.currency != self.to_currency):
				if(self.exchange_rate and self.exchange_rate>0):
					return (amount * self.exchange_rate)
				return (amount * 1)
			else:
				return amount
		return amount
			
	@frappe.whitelist()
	def calculate_percentage(self):
		deduction_amount = 0
		for row in self.deduction_breakeven:
			amount = row.donation_amount*(row.percentage/100)
			row.amount = amount
			deduction_amount += amount
		# calculate totals...
		self.calculate_total(deduction_amount)

	def calculate_total(self, total_donation, deduction_amount):
		# currency exchange calculation...
		self.total_donation = total_donation
		self.total_deduction = deduction_amount
		# self.outstanding_amount = (self.total_donation - deduction_amount)
		self.outstanding_amount = self.total_donation
		self.net_amount = (self.total_donation - deduction_amount)
		# base amount calculation...
		self.base_total_donation  = self.apply_currecny_exchange(self.total_donation)
		self.base_total_deduction = self.apply_currecny_exchange(self.total_deduction)
		self.base_outstanding_amount = self.apply_currecny_exchange(self.total_donation)
		self.base_net_amount = self.apply_currecny_exchange(self.net_amount)
		# ...!

	def on_submit(self):
		# Credit Debit, GL Entry
		if(self.donation_type == "Cash"):
			self.make_payment_detail_gl_entry()
			self.make_deduction_gl_entries()
			self.make_payment_ledger_entry()
			self.make_payment_entry()
			self.update_status()
			self.send_donation_emails()		# Mubashir Bashir
			
		elif(self.donation_type in ["In Kind Donation", "In-Kind Donation", "In-Kind-Donation",]):
			make_stock_entry_for_in_kind_donation(self) # nabeel saleem, 22-08-2025
		
		
	def get_gl_entry_dict(self):
		return frappe._dict({
			'doctype': 'GL Entry',
			'posting_date': self.posting_date,
			'transaction_date': self.posting_date,
			'against': f"Donation: {self.name}",
			'against_voucher_type': self.doctype,
			'against_voucher': self.name,
			'voucher_type': self.doctype,
			'voucher_no': self.name,
			'voucher_subtype': 'Receive',
			# 'remarks': self.instructions_internal,
			# 'is_opening': 'No',
			# 'is_advance': 'No',
			'company': self.company,
			'transaction_currency': self.currency,
			'transaction_exchange_rate': self.exchange_rate,
		})

	def make_payment_detail_gl_entry(self):
		
		def get_account_currency(row):
			return frappe.db.get_value("Account", {"name": row.equity_account, "account_currency": self.currency}, "account_currency")
		
		def equity_entry(row, args):
			args.update({
				"party_type": "",
				"party": "",
				"voucher_detail_no": row.name,
				"donor": row.donor,
				"donor_type": row.donor_type,
				"donor_desk": row.donor_desk,
				"donation_type": row.intention,
				"transaction_type": row.transaction_type,
				"fund_class": row.fund_class,
				"service_area": row.pay_service_area,
				"subservice_area": row.pay_subservice_area,
				"product": row.pay_product if(row.pay_product) else row.product,
				# "project": row.project,
				"cost_center": row.cost_center,
				"account": row.equity_account,
			})
			c_args = get_currency_args()
			args.update(c_args)
			if(self.is_return): # debit
				args.update({
					"debit": row.base_net_amount,
					"debit_in_account_currency": row.net_amount if(get_account_currency(row)) else row.base_net_amount,
					"debit_in_transaction_currency": row.net_amount,
		   		})
			elif(self.unknown_to_known): # credit
				args.update({
					"credit": row.base_net_amount,
					"credit_in_account_currency": row.net_amount if(get_account_currency(row)) else row.base_net_amount,
					"credit_in_transaction_currency": row.net_amount,
		   		})
			else: # credit
				args.update({
					"credit": row.base_net_amount,
					"credit_in_account_currency": row.net_amount if(get_account_currency(row)) else row.base_net_amount,
					"credit_in_transaction_currency": row.net_amount,
		   		})

			doc = frappe.get_doc(args)
			doc.save(ignore_permissions=True)
			doc.submit()

		def debtors_unknown_to_known(row):
			if(self.unknown_to_known): 
				for rowp in frappe.db.sql("""select * from `tabPayment Detail`
						where docstatus=%(docstatus)s and parent = %(parent)s and random_id=%(random_id)s""", 
						{"docstatus": 1,"parent": self.return_against, "random_id": row.random_id}, as_dict=1):
					frappe.db.set_value("Payment Detail", rowp.name, "unknown_to_known", 1)
					args.update({
						"account": rowp.equity_account,
						'against': f"Donation: {self.return_against}",
						'against_voucher': self.name,
						'voucher_no': self.return_against,
						"party_type": "",
						"party": "",
						"voucher_detail_no": row.name,
						"donor": rowp.donor,
						"donor_type": rowp.donor_type,
						"donor_desk": rowp.donor_desk,
						"donation_type": rowp.intention,
						"transaction_type": rowp.transaction_type,
						"fund_class": rowp.fund_class,
						"service_area": rowp.pay_service_area,
						"subservice_area": rowp.pay_subservice_area,
						"product": rowp.pay_product if(rowp.pay_product) else rowp.product,
						# "project": row.project,
						"cost_center": rowp.cost_center,
    
						"account": rowp.equity_account,
						"debit": row.base_net_amount,
						"credit": 0,
						"debit_in_account_currency": row.net_amount,
						"credit_in_account_currency": 0,
						"debit_in_transaction_currency": row.net_amount,
						"credit_in_transaction_currency": 0,
					})
					doc = frappe.get_doc(args)
					doc.save(ignore_permissions=True)
					doc.submit()

		def receivable_entries(args):
			# Entry against Receivable Account
			c_args = get_currency_args()
			args.update(c_args)
			args.update({
				"party_type": "Donor",
				"party": row.donor,
				"account": row.receivable_account,
			})
			if(self.is_return): # credit
				args.update({
					"credit": row.base_donation_amount,
					"credit_in_account_currency": row.donation_amount,
					"credit_in_transaction_currency": row.donation_amount
				})
			else: # debit
				args.update({
					"debit": row.base_donation_amount,
					"debit_in_account_currency": row.donation_amount,
					"debit_in_transaction_currency": row.donation_amount
				})
			
			if(self.donor_identity == "Merchant - Known"): pass
			else:
				doc = frappe.get_doc(args)
				doc.insert(ignore_permissions=True)
				doc.submit()

		def receivable_entry(args):
			if (not self.unknown_to_known) and (self.donor_identity == "Merchant - Known"): 
				c_args = get_currency_args()
				args.update(c_args)
				args.update({
					"account": row.receivable_account,
				})
				if(self.is_return): # credit
					args.update({
						"credit": self.base_total_donation,
						"credit_in_account_currency": self.total_donation,
						"credit_in_transaction_currency": self.total_donation
					})
				else: # debit
					args.update({
							"debit": self.base_total_donation,
							"debit_in_account_currency": self.total_donation,
							"debit_in_transaction_currency": self.total_donation
						})
				doc = frappe.get_doc(args)
				doc.insert(ignore_permissions=True)
				doc.submit()
	
		args = self.get_gl_entry_dict()
		for row in self.payment_detail:
			""" is return reverse account functionality... """
			equity_entry(row, args)
			debtors_unknown_to_known(row)
			receivable_entries(args)
		receivable_entry(args)
			
	def make_deduction_gl_entries(self):
		args = self.get_gl_entry_dict()
		# Loop through each row in the child table `deduction_breakeven`
		for row in self.deduction_breakeven:
			""" In normal case, accounts are going to be credit
			But, in return case accounts are debit.
				"""
			c_args = get_currency_args()
			args.update(c_args)
			if(self.is_return): # debit
				args.update({
					"debit": row.base_amount,
					"debit_in_account_currency": row.amount,
					"debit_in_transaction_currency": row.amount
				})
			elif(self.unknown_to_known): # credit
				args.update({
					"credit": row.base_amount,
					"credit_in_account_currency": row.amount,
					"credit_in_transaction_currency": row.amount
				})
			else: # credit
				args.update({
					"credit": row.base_amount,
					"credit_in_account_currency": row.amount,
					"credit_in_transaction_currency": row.amount
				})

			args.update({
				"account": row.account,
				"voucher_detail_no": row.name,
				
				"donor": row.donor,
				"donor_type": row.donor_type,
				"donor_desk": row.donor_desk,
				"donation_type": row.intention,
				"transaction_type": row.transaction_type,
				"fund_class": row.fund_class,
				"service_area": row.service_area,
				"subservice_area": row.subservice_area,
				"product": row.product,
				"project": row.project,
				"cost_center": row.cost_center,
			})
			doc = frappe.get_doc(args)
			doc.save(ignore_permissions=True)
			doc.submit()

	def make_payment_ledger_entry(self):
		if((self.reference_doctype=='Payment Entry') and (self.reference_docname)): return
		if(self.is_return or self.unknown_to_known): return
		args = {}
		for row in self.payment_detail:
			args = frappe._dict({
				"doctype": "Payment Ledger Entry",
				"posting_date": self.posting_date,
				"company": self.company,
				"account_type": "Receivable",
				"account": row.receivable_account,
				"party_type": "Donor",
				"party": row.donor,
				"due_date": self.due_date,
				"voucher_type": self.doctype,
				"voucher_no": self.name,
				"against_voucher_type": self.doctype,
				"against_voucher_no": self.name,
				"amount": row.base_donation_amount,
				"account_currency": self.currency,
				"amount_in_account_currency": row.donation_amount,
				"voucher_detail_no": row.name,
			})
			if(self.donor_identity == "Merchant - Known"):
				pass
			else:
				doc = frappe.get_doc(args)
				doc.save(ignore_permissions=True)
				doc.submit()
		if(self.donor_identity == "Merchant - Known"):
			args.update({
				"amount": self.base_total_donation,
				"amount_in_account_currency": self.total_donation
			})
			doc = frappe.get_doc(args)
			doc.save(ignore_permissions=True)
			doc.submit()

	def make_payment_entry(self):
		if(self.contribution_type!="Donation"): return
		if((self.reference_doctype=='Payment Entry') and (self.reference_docname)): return
		if(self.is_return or self.unknown_to_known): return
		args = {}
		MERCHANT_LIST = ["Merchant - Known", "Merchant - Unknown"]
		for row in self.payment_detail:
			args = frappe._dict({
				"doctype": "Payment Entry",
				"payment_type" : "Receive",
				"party_type" : "Donor",
				"party" : row.donor,
				"party_name" : row.donor_name,
				"posting_date" : self.posting_date,
				"company" : self.company,
				"mode_of_payment" : row.mode_of_payment,
				"reference_no" : row.transaction_no_cheque_no,
				"reference_date" : row.reference_date,
				"source_exchange_rate" : self.exchange_rate,
				"target_exchange_rate": 1,
				"paid_from" : row.receivable_account,
				"paid_to" :  row.account_paid_to,
				"reference_date" : self.due_date,
				"cost_center" : row.cost_center,
				"paid_amount" : row.donation_amount,
				"received_amount" : row.base_donation_amount,
				# Dimensions
				"donor": row.donor,
				"donor_type": row.donor_type,
				"donor_desk": row.donor_desk,
				"donation_type": row.intention,
				"transaction_type": row.transaction_type,
				"fund_class": row.fund_class,
				"service_area": row.pay_service_area,
				"subservice_area": row.pay_subservice_area,
				"product": row.pay_product if(row.pay_product) else row.product,
				# "project": row.project,
				"cost_center": row.cost_center,
    
				"references": [{
						"reference_doctype": self.doctype,
						"reference_name" : self.name,
						"due_date" : self.posting_date,
						"total_amount" : self.total_donation,
						"outstanding_amount" : row.donation_amount,
						"allocated_amount" : row.donation_amount,
						"custom_donation_payment_detail": row.name
				}]
			})
			# frappe.throw(frappe.as_json(args))
			if(self.donor_identity in MERCHANT_LIST):
				pass
			else:
				doc = frappe.get_doc(args)
				doc.save(ignore_permissions=True)
				# doc.submit()

				if(self.donor_identity == "Unknown"):
					# set Payment Entry id in payment_detail child table.
					frappe.db.set_value("Payment Detail", row.name, "payment_entry", doc.name)

		if(self.donor_identity in MERCHANT_LIST):
			args.update({
				"paid_amount" : self.total_donation,
				"received_amount" : self.total_donation,
			})
			doc = frappe.get_doc(args)
			doc.save(ignore_permissions=True)
			doc.submit()

	def validate_is_return(self):
		def stop_exceeding_donation_amount(row):
			# For Unknown->Known (reverse donor) we cannot match by donor because the donor changes.
			# Use parent and random_id (and keep other dimensional matches) to fetch the original amount.
			if self.unknown_to_known:
				result = frappe.db.sql(f"""
					select donation_amount 
					from `tabPayment Detail` 
					where 
						docstatus=1
						and pay_service_area='{row.pay_service_area}'
						and pay_subservice_area='{row.pay_subservice_area}'
						and pay_product='{row.pay_product}'
						and fund_class='{row.fund_class}'
						and random_id = '{row.random_id}'
						and parent= '{self.return_against}'
				""")
			else:
				result = frappe.db.sql(f"""
					select donation_amount 
					from `tabPayment Detail` 
					where 
						docstatus=1
						and donor='{row.donor}'
						and pay_service_area='{row.pay_service_area}'
						and pay_subservice_area='{row.pay_subservice_area}'
						and pay_product='{row.pay_product}'
						and fund_class='{row.fund_class}'
						and random_id = '{row.random_id}'
						and parent= '{self.return_against}'
				""")
			# and project='{row.project}'
			if(result):
				donation_amount = result[0][0]
				if(row.donation_amount>donation_amount):
					frappe.throw(f" <b>Row #{row.idx}: </b> [{row.donor_name}]<br> Donation return amount is exceeding the actual donation.", title='Return Donation')
		
		if(self.is_return): 
			# if(len(self.payment_detail)>1):
				# frappe.throw('Only [1] donor is allowed.', title='Is Return (Credit Note)')
			error_msg = ""
			for row in self.payment_detail:
				if (frappe.db.sql(f""" 
					select d.name 
					from `tabDonation` d inner join `tabPayment Detail` pd on (d.name=pd.parent) 
					where 
						d.docstatus=1
						and d.return_against='{self.return_against}' 
						and pd.donor='{row.donor}'
						and pd.pay_service_area='{row.pay_service_area}'
						and pd.pay_subservice_area='{row.pay_subservice_area}'
						and pd.pay_product='{row.pay_product}'
						and pd.fund_class='{row.fund_class}'
						and pd.random_id = '{row.random_id}'
						and pd.parent!= '{self.name}' """)):
					error_msg += f" <b>Row #{row.idx}: </b> [{row.donor_name}]<br>"
				stop_exceeding_donation_amount(row)
				# and pd.project='{row.project}'
			if(error_msg!=""):	
				frappe.throw(error_msg, title='Return entries already exist.')

	def update_status(self):
		if(self.docstatus!=2 and (self.unknown_to_known)):
			self.db_set("status", "Unknown To Known")
		elif(self.docstatus==1):
			if(self.donation_type == "Cash"):
				status = "Paid" if(self.contribution_type == "Donation") else "Unpaid"
			elif(self.donation_type == "In Kind Donation"):
				status = "In Kind"
			if(self.is_return): 
				status = "Return"
				self.reset_return_to_paid()
			self.db_set("status", status)
		elif(self.docstatus==0):
			self.db_set("status", "Draft")
		elif(self.docstatus==2):
			self.db_set("status", "Cancelled")

	#Mubashir Bashir Start 3-12-24
	def send_donation_emails(self):
		"""
		Sends email notifications to all users linked to the project when a new donation is added.
		"""
		for payment in self.payment_detail:
			project = payment.project
			if project:
				project_name = frappe.db.get_value('Project', project, 'project_name')
				project_users = frappe.db.sql(
					"""
					SELECT email, full_name
					FROM `tabProject User`
					WHERE parent = %s
					""",
					(project,),
					as_dict=True,
				)
				
				email_addresses = [
					{"email": user["email"], "full_name": user["full_name"]}
					for user in project_users if user["email"]
				]

				company_currency = frappe.db.get_value('Company', self.company, 'default_currency')
				currency = self.currency or company_currency

				for user in email_addresses:
					formatted_amount = frappe.utils.fmt_money(payment.donation_amount, currency=currency)
					email = user["email"]
					full_name = user["full_name"] or "Valued Team Member"
					subject = f"New Donation Received for Project {project_name}"
					message = f"""
					Dear {full_name},<br><br>
					We are excited to inform you that a new {self.contribution_type} has been received for the project: <b>{project_name}</b>.<br><br>
					<b>{self.contribution_type} Details:</b><br>
					- <b>Project Name:</b> {project_name}<br>
					- <b>Project ID:</b> {project}<br>
					- <b>{self.contribution_type} Amount:</b> {formatted_amount}<br>
					Your contribution and effort towards this project are greatly appreciated. Please feel free to reach out if you have any questions.<br><br>
					Best regards,<br>
					<b>{self.company}</b>
					"""
					frappe.sendmail(
						recipients=email,
						subject=subject,
						message=message,
					)
			#Mubashir Bashir End 3-12-24

	def before_cancel(self):
		self.del_gl_entries()
		self.del_payment_ledger_entry()
		self.del_payment_entry()
		# self.del_child_table()
		
	def on_cancel(self):
		self.del_gl_entries()
		self.del_payment_ledger_entry()
		self.del_payment_entry()
		self.del_child_table()
		self.update_status()
		self.reset_return_to_paid()

	def del_gl_entries(self):
		if(frappe.db.exists({"doctype": "GL Entry", "docstatus": 1, "against_voucher": self.name})):
			frappe.db.sql(f""" delete from `tabGL Entry` Where against_voucher = "{self.name}" """)

	def del_payment_entry(self):
		payment = frappe.db.get_value("Payment Entry Reference", 
			{"docstatus": 1, "reference_doctype": "Donation", "reference_name":self.name},
			["name", "parent"], as_dict=1)
		if(payment):
			frappe.db.sql(f""" delete from `tabPayment Entry Reference` Where name = "{payment.name}" """)
			frappe.db.sql(f""" delete from `tabPayment Entry` Where name = "{payment.parent}" """)
			frappe.db.sql(f""" delete from `tabGL Entry` Where  voucher_no = "{payment.parent}" """)

	def del_payment_ledger_entry(self):
		if(frappe.db.exists({"doctype": "Payment Ledger Entry", "docstatus": 1, "against_voucher_no": self.name})):
			frappe.db.sql(f""" delete from `tabPayment Ledger Entry` Where against_voucher_no = "{self.name}" """)

	def del_child_table(self):
		if(self.unknown_to_known):
			for row in self.payment_detail:
				if(frappe.db.exists({"doctype": "Payment Detail", "docstatus": 1, "parent": self.return_against, "random_id": row.random_id})):
					frappe.db.set_value("Payment Detail", {"docstatus": 1, "parent": self.return_against, "random_id": row.random_id}, "unknown_to_known", 0)

			# if(frappe.db.exists({"doctype": "Deduction Breakeven", "docstatus": 1, "parent": self.name})):
			# 	frappe.db.sql(f""" delete from `tabDeduction Breakeven` Where docstatus= 1 and parent = "{self.name}" """)

	def reset_return_to_paid(self):
		if(not self.return_against): return
		_actual_donors = frappe.db.get_value("Donation", {'docstatus': 1, 'name': self.return_against}, 'total_donors')
		_total_donors = get_total_donors_return(self.return_against)
		if(_actual_donors == _total_donors):
			frappe.db.set_value("Donation", self.return_against, 'status', 'Credit Note Issued')
		elif(_actual_donors > _total_donors and _total_donors>0):
			frappe.db.set_value("Donation", self.return_against, 'status', 'Partly Return')
		else:
			frappe.db.set_value("Donation", self.return_against, 'status', 'Paid')

	@frappe.whitelist()
	def provision_doubtful_debt_func(self, values: dict):
		from akf_accounts.akf_accounts.doctype.donation.doubtful_debt import provision_doubtful_debt_func
		args = self.get_gl_entry_dict()
		return provision_doubtful_debt_func(self, args, values)
	
	@frappe.whitelist()
	def bad_debt_written_off(self, values: dict):
		from akf_accounts.akf_accounts.doctype.donation.doubtful_debt import bad_debt_written_off
		args = self.get_gl_entry_dict()
		return bad_debt_written_off(self, args, values)


def get_currency_args():
	return {
		# Company Currency
		"debit": 0,
		"credit": 0,
		# Account Currency
		"debit_in_account_currency": 0,
		"credit_in_account_currency": 0,
		# Transaction Currency
		"debit_in_transaction_currency": 0,
		"credit_in_transaction_currency": 0
	}

@frappe.whitelist()
def get_donors_list(donation_id, is_doubtful_debt: bool, is_written_off:bool, is_payment_entry: bool):
	conditions = ""
	# if(is_doubtful_debt):
	# 	conditions = " and ifnull(provision_doubtful_debt, '')=''  "
	if(is_written_off):
		# conditions = " and is_written_off=0 and ifnull(provision_doubtful_debt, '')!='' "
		conditions = " and  doubtful_debt_amount>0 "
	if(is_payment_entry):
		pass
		# conditions = " and is_written_off=0 "
	result = frappe.db.sql(f""" 
				Select 
					donor, 
     				idx, 
					(outstanding_amount) as remaining_amount
     				-- (outstanding_amount-doubtful_debt_amount) as remaining_amount
				From 
					`tabPayment Detail` 
				Where
					outstanding_amount>0 and parent='{donation_id}' {conditions} 
				Having 
					remaining_amount
				""", as_dict=0)
				
	donors_list = {d[0] for d in result} if(result) else []
	idx_list = {}
	for donor in donors_list:
		idx_list[donor] = sorted([r[1] for r in result if(r[0]==donor)])
	return {
		"donors_list": sorted(list(donors_list)) if(donors_list) else [],
		"idx_list": idx_list if(idx_list) else {},
	}

@frappe.whitelist()
def get_idx_list_unknown(donation_id):
	result = frappe.db.sql(f""" 
			select idx 
		 	from `tabPayment Detail` 
		  	where paid = 0 and unknown_to_known=0 and parent='{donation_id}' """, as_dict=0)
	idx_list = sorted([r[0] for r in result])
	return idx_list

@frappe.whitelist()
def get_outstanding(filters):
	filters = ast.literal_eval(filters)
	result = frappe.db.sql(""" 
		Select 
			outstanding_amount, 
			doubtful_debt_amount,
			bad_debt_amount
			-- (case when is_written_off=1 then (outstanding_amount - bad_debt_amount) else 0 end) remaining_amount
			-- base_outstanding_amount
		From 
  			`tabPayment Detail` 
		Where 
  			docstatus=1
			and parent = %(name)s and donor = %(donor_id)s and idx = %(idx)s """, filters)
	args = {
		"outstanding_amount": 0.0,
		"doubtful_debt_amount": 0.0,
	}
	if(result):
		args.update({
			"outstanding_amount": result[0][0],
			"doubtful_debt_amount": result[0][1],
			'bad_debt_amount': result[0][2],
			# "remaining_amount": result[0][3],
		})
	return args


@frappe.whitelist()
def pledge_payment_entry(doc, values):
	from frappe.utils import getdate
	curdate = getdate()

	# Accept either a JSON string, a Python literal string, or an already-parsed dict
	def _parse_arg(val):
		# If it's already a mapping-like object, return as-is
		if isinstance(val, (dict, frappe._dict)):
			return val
		# If it's a string, try JSON first (standard from JS), then fall back to ast.literal_eval
		if isinstance(val, str):
			try:
				return json.loads(val)
			except Exception:
				try:
					return ast.literal_eval(val)
				except Exception:
					# As a last resort, return the original string
					return val
		# Unknown type: return as-is
		return val

	parsed_doc = _parse_arg(doc)
	parsed_values = _parse_arg(values)

	# Wrap in frappe._dict for convenient attribute access
	doc = frappe._dict(parsed_doc)
	values = frappe._dict(parsed_values)
	row = frappe.db.get_value('Payment Detail', {'parent': doc.name, 'donor': values.donor_id, "idx": values.serial_no}, ['*'], as_dict=1)

	if(not row): frappe.throw(f"You're paying more than donation amount.")
	exchange_rate = get_exchange_rate(doc.currency, doc.to_currency, curdate)
	args = frappe._dict({
		"doctype": "Payment Entry",
		"payment_type" : "Receive",
		"party_type" : "Donor",
		"party" : row.donor,
		"party_name" : row.donor_name,
		"posting_date" : curdate,
		"company" : doc.company,
		"mode_of_payment" : values.mode_of_payment,
		"reference_no" : values.cheque_reference_no,
		"source_exchange_rate" : exchange_rate,
		"target_exchange_rate": 1,
		"paid_from" : row.receivable_account,
		"paid_to" : values.account_paid_to,
		"reference_date" : curdate,
		"paid_amount" : values.paid_amount,
		"received_amount" : (values.paid_amount * exchange_rate),
		# Dimensions
		"donor": row.donor,
		"donor_type": row.donor_type,
		"donor_desk": row.donor_desk,
		"donation_type": row.intention,
		"transaction_type": row.transaction_type,
		"fund_class": row.fund_class,
		"service_area": row.pay_service_area,
		"subservice_area": row.pay_subservice_area,
		"product": row.pay_product if(row.pay_product) else row.product,
		# "project": row.project,
		"cost_center": row.cost_center,
		"account": row.equity_account,

		"references": [{
				"reference_doctype": "Donation",
				"reference_name" : doc.name,
				"due_date" : curdate,
				"total_amount" : doc.total_donation,
				# "outstanding_amount" : values.paid_amount,			
				"outstanding_amount" : doc.outstanding_amount,
				"allocated_amount" : values.paid_amount,
				"custom_donation_payment_detail": row.name
		}]
	})
	_doc = frappe.get_doc(args)
	_doc.save(ignore_permissions=True)
	_doc.submit()
	# frappe.db.set_value("Payment Detail", row.name, "paid", values.paid)
	# frappe.db.set_value("Payment Detail", row.name, "outstanding_amount", values.outstanding_amount)
	pe_link = get_link_to_form("Payment Entry", _doc.name, "Payment Entry")
	frappe.msgprint(f"{pe_link} has been paid successfully!", alert=True)
	return _doc.name

@frappe.whitelist()
def return_payment_entry(doc):
	from frappe.utils import getdate
	curdate = getdate()

	doc = frappe._dict(ast.literal_eval(doc))
	
	args =  frappe._dict({
		"doctype": "Payment Entry",
		"payment_type" :  "Pay",
		"party_type" : "Donor",
		"posting_date" : curdate,
		"company" : doc.company,
		"source_exchange_rate" : 0.3,
		"target_exchange_rate": 1,
		"reference_date" : curdate,
	})
	
	for row in doc.payment_detail:
		row = frappe._dict(row)
		args.update({
			"party" : row.donor,
			"party_name" : row.donor_name,
			"mode_of_payment" :  row.mode_of_payment,
			"paid_from" : row.account_paid_to,
			"paid_to" : row.receivable_account,
			"reference_no" : row.transaction_no_cheque_no,
			"paid_amount" : row.outstanding_amount,
			"received_amount" : row.outstanding_amount,

			# Dimensions
			"donor": row.donor,
			"donor_type": row.donor_type,
			"donor_desk": row.donor_desk,
			"donation_type": row.intention,
			"transaction_type": row.transaction_type,
			"fund_class": row.fund_class,
			"service_area": row.pay_service_area,
			"subservice_area": row.pay_subservice_area,
			"product": row.pay_product if(row.pay_product) else row.product,
			# "project": row.project,
			"cost_center": row.cost_center,

			"references": [{
					"reference_doctype": "Donation",
					"reference_name" : doc.name,
					"due_date" : curdate,
					"total_amount" : doc.base_total_donation,
					"outstanding_amount" : -1 * row.outstanding_amount,
					"allocated_amount" : -1 * row.outstanding_amount,
			}]
		})
	
	_doc = frappe.get_doc(args)
	_doc.save(ignore_permissions=True)

	# frappe.db.set_value("Payment Detail", row.name, "paid", values.paid)
	pe_link = get_link_to_form("Payment Entry", _doc.name, "Payment Entry")
	frappe.msgprint(f"{pe_link} has been created successfully!", alert=True)
	return _doc.name

@frappe.whitelist()
def get_min_max_percentage(fund_class, account):
	result = frappe.db.sql("""
		SELECT min_percent, max_percent
		FROM `tabDeduction Details`
		WHERE parent = %s AND account = %s
	""", (fund_class, account), as_dict=True)
	if result:
		return result[0].min_percent, result[0].max_percent
	else:
		return None, None

# @frappe.whitelist()
# def get_min_max_percentage(service_area, account):
# 	result = frappe.db.sql("""
# 		SELECT min_percent, max_percent
# 		FROM `tabDeduction Details`
# 		WHERE parent = %s AND account = %s
# 	""", (service_area, account), as_dict=True)
# 	if result:
# 		return result[0].min_percent, result[0].max_percent
# 	else:
# 		return None, None

@frappe.whitelist()
def set_unknown_to_known(name, values):
	
	"""  
	=> Update donor information in these doctypes.
		Donation
		Payment Detail [child table]
		GL Entry
		Payment Ledger Entry
		Payment Entry
	""" 
	import ast
	values = frappe._dict(ast.literal_eval(values))
	
	pid = frappe.db.get_value("Payment Detail", 
		{"parent": name, "idx": values.serial_no}, ["name", "payment_entry"], as_dict=1)

	if(not pid): frappe.throw(f"Payment Detail Serial No: {values.serial_no}", title="Not Found")
	
	info = frappe.db.get_value("Donor", values.donor, "*", as_dict=1)

	# Update Payment Details
	frappe.db.sql(f""" 
		Update 
			`tabPayment Detail`
		Set 
			reverse_donor = 'Unknown To Known', 
			donor = '{info.name}', donor_name='{info.donor_name}',
			donor = '{info.name}',
			donor_type='{info.donor_type if (info.donor_type) else ""}', 
			contact_no='{info.contact_no if (info.contact_no) else "" }',  
			address= '{info.address if (info.address) else "" }', 
			email='{info.email if (info.email) else ""}',
			city = '{info.city if(info.city) else ""}'
		Where 
			docstatus=1
			and parent = '{name}'
			and name = '{pid.name}'
	 """)

	# Update gl entry for debit
	frappe.db.sql(f""" 
	Update 
		`tabGL Entry`
	Set 
		party = '{info.name}',
		donor = '{info.name}',
		reverse_donor = 'Unknown To Known'
	Where 
		docstatus=1
		and ifnull(party, "")!=""
		and voucher_no = '{name}'
		and voucher_detail_no = '{pid.name}'
	""")

	# Update gl entry for credit
	frappe.db.sql(f""" 
	Update 
		`tabGL Entry`
	Set 
		donor = '{info.name}',
		reverse_donor = 'Unknown To Known'
	Where 
		docstatus=1
		and voucher_no = '{name}'
		and voucher_detail_no = '{pid.name}'
	""")

	frappe.db.sql(f""" 
	Update 
		`tabDeduction Breakeven`
	Set
		donor = '{info.name}',
		reverse_donor = 'Unknown To Known'
	Where 
		docstatus=1
		and parent = '{name}'
		and payment_detail_id = '{values.serial_no}'
	""")

	frappe.db.sql(f""" 
	Update 
		`tabGL Entry`
	Set 
		donor = '{info.name}',
		reverse_donor = 'Unknown To Known'
	Where 
		docstatus=1
		and voucher_no = '{name}'
		and voucher_detail_no in (select name from `tabDeduction Breakeven` where docstatus=1 and parent = '{name}' and payment_detail_id = '{values.serial_no}')
	""")

	frappe.db.sql(f""" 
	Update 
		`tabPayment Ledger Entry`
	Set 
		donor = '{info.name}', party = '{info.name}', reverse_donor = 'Unknown To Known'
	Where 
		docstatus=1
		and against_voucher_no = '{name}'
	""")

	frappe.db.sql(f""" 
	Update 
		`tabPayment Entry`
	Set 
		party = '{info.name}', party_name= '{info.donor_name}', donor='{info.name}', reverse_donor = 'Unknown To Known'
	Where 
		docstatus=1
		and name = '{pid.payment_entry}'
	""")

	frappe.db.sql(f""" 
	Update 
		`tabGL Entry`
	Set 
		party = '{info.name}', donor='{info.name}', reverse_donor = 'Unknown To Known'
	Where 
		docstatus=1
		and voucher_no = '{pid.payment_entry}'
	""")


	frappe.msgprint("Donor id, updated in [<b>Payment Detail, Deduction Breakeven, GL Entry, Payment Entry, Payment Ledger Entry</b>] accounting dimensions/doctypes.", alert=1)

@frappe.whitelist()
def get_total_donors_return(return_against):
	result = frappe.db.sql(f""" 
		select ifnull(sum(total_donors),0) as total_donors 
		from `tabDonation` 
		where docstatus<2 and return_against='{return_against}' 
	""")
	return result[0][0] if(result) else 0

""" 12-09-2024 
Nabeel Saleem 
-> Return / Credit Note 
"""

import frappe
from frappe.model.mapper import get_mapped_doc

@frappe.whitelist()
def make_donation_return(source_name, target_doc=None):
	# from erpnext.controllers.sales_and_purchase_return import make_return_doc
	return make_return_doc("Donation", source_name, target_doc)


@frappe.whitelist()
def create_and_insert_donation_return(source_name, preserved_payment_details=None):
	"""
	Map a Donation to its return (Credit Note), optionally restore preserved payment_detail fields,
	mark it unknown_to_known and insert the document server-side.

	Arguments:
	- source_name: name of the Donation to return against
	- preserved_payment_details: JSON-stringified list of dicts with fields to restore on each payment_detail row

	Returns: name of created Donation (return document)
	"""
	import ast

	# Create mapped document (in-memory)
	mapped = make_return_doc(source_name)
	if not mapped:
		frappe.throw("Failed to map Donation to return document")

	# Restore preserved payment detail fields if provided
	if preserved_payment_details:
		try:
			preserved = ast.literal_eval(preserved_payment_details) if isinstance(preserved_payment_details, str) else preserved_payment_details
		except Exception:
			preserved = None

		if preserved and isinstance(preserved, (list, tuple)):
			try:
				for idx, row in enumerate(mapped.payment_detail):
					if idx < len(preserved):
						orig = preserved[idx]
						if isinstance(orig, dict):
							for k, v in orig.items():
								if v is not None and v != "":
									row[k] = v
			except Exception:
				# Non-fatal: don't block creation if restore fails
				frappe.log_error(f"Failed to restore preserved payment detail fields for return of {source_name}")

	# Mark the mapped doc as unknown_to_known and an actual return
	try:
		mapped.unknown_to_known = 1
	except Exception:
		pass

	# Insert on server (ignore permissions since this is an internal/controlled flow)
	try:
		mapped.insert(ignore_permissions=True)
	except Exception as e:
		frappe.log_error(message=str(e), title=f"Failed to insert mapped return for {source_name}")
		raise

	return mapped.name

def make_return_doc(
	doctype: str, source_name: str, target_doc=None, return_against_rejected_qty=False
):
	from frappe.model.mapper import get_mapped_doc
	
	def set_missing_values(source, target):
		doc = frappe.get_doc(target)
		doc.is_return = 1
		doc.status = "Return"
		doc.return_against = source.name
		doc.reverse_against = ""
	
	def update_payment_detail(source_doc, target_doc, source_parent):
		# target_doc.donation_amount = -1 * source_doc.donation_amount
		target_doc.donation_amount = source_doc.donation_amount
		target_doc.paid = 0
		# Clear receipt_number for return documents to avoid duplicate key error
		target_doc.receipt_number = ""

	doclist = get_mapped_doc(
		doctype,
		source_name,
		{
			doctype: {
				"doctype": doctype,
				"validation": {
					"docstatus": ["=", 1],
				},
			},
			"Payment Detail": {
				"doctype": "Payment Detail",
				# "field_map": {"*"},
				"postprocess": update_payment_detail,
			},
			# "Payment Schedule": {"doctype": "Payment Schedule", "postprocess": update_terms},
		},
		target_doc,
		set_missing_values,
	)

	return doclist

@frappe.whitelist()
def verify_payment_entry(doctype, reference_name, fieldname):
	return frappe.db.sql(f""" 
		select {fieldname}
		from `tab{doctype}`
		where docstatus<2
		and reference_name = '{reference_name}'
	 """)

# akf_accounts.akf_accounts.doctype.donation.donation.cron_for_notify_overdue_tasks

#Mubashir Bashir Start 9-12-24
@frappe.whitelist()
def cron_for_notify_overdue_tasks():	#Mubashir

	processed_projects = set()    
	donation_docs = frappe.get_all(
		'Donation',
		filters={
			'docstatus': 1,
			'contribution_type': 'Donation',
		},
		fields=['name'] 
	)
	
	for donation in donation_docs:
		donation_doc = frappe.get_doc('Donation', donation['name'])
		for payment in donation_doc.payment_detail:
			project = payment.get('project')
			
			if project and project not in processed_projects:
				processed_projects.add(project)                
				notify_overdue_tasks(project)

@frappe.whitelist()
def notify_overdue_tasks(project):	#Mubashir
	"""
	Notify users with the 'Project Manager' role about overdue tasks related to a specific project.
	"""
	project_name = frappe.db.get_value("Project", project, "project_name") or project

	overdue_tasks = frappe.get_all(
		"Task",
		filters={
			"project": project,
			"status": "Overdue"
		},
		fields=["name", "subject", "status", "exp_end_date"]
	)

	if overdue_tasks:
		task_details = "".join(
			f"<li><b>{task['subject']}</b> (Status: {task['status']}, Due Date: {task['exp_end_date']})</li>"
			for task in overdue_tasks
		)
		project_users = frappe.get_all(
			"Project User",
			filters={"parent": project},
			fields=["email", "full_name"]
		)

		for user in project_users:
			email = user.get("email")
			full_name = user.get("full_name", "Project Manager")

			# Check if the user has the 'Project Manager' role
			if email:
				roles = frappe.get_all(
					"Has Role",
					filters={"parent": email, "role": "Projects Manager"},
					fields=["role"]
				)
				if roles:
					subject = f"Overdue Tasks Alert for Project: {project_name}"
					message = f"""
					Dear {full_name},<br><br>
					The following tasks in the project <b>{project_name}</b> are overdue:<br>
					<ul>{task_details}</ul>
					Please take necessary actions to resolve these tasks.<br><br>
					Regards,<br>
					Project Management System
					"""
					print(f'sending email to {email}')
					try:
						frappe.sendmail(
							recipients=email,
							subject=subject,
							message=message
						)
						print(f'email sent to {email}')
					except Exception as e:
						frappe.log_error(message=str(e), title="Error in Task Overdue Notification")
#Mubashir Bashir End 9-12-24

""" Doubtful Debtors """
@frappe.whitelist()
def get_donation_details(filters):
	filters = ast.literal_eval(filters)
	# frappe.msgprint(f"{filters}")
	if(filters.get("is_doubtful_debt")):
		return frappe.db.sql("""
            Select 
            	donation_amount, 
				(outstanding_amount - doubtful_debt_amount) as outstanding_amount,
				0 as doubtful_debt_amount, 
    			bad_debt_expense, 
       			provision_doubtful_debt
			From 
   				`tabPayment Detail` 
			Where docstatus=1
				and parent = %(name)s and donor = %(donor_id)s and idx = %(idx)s """, filters, as_dict=1)[0]
	elif(filters.get("is_written_off")):
		return frappe.db.sql(""" select 
                    donation_amount, 
                    outstanding_amount, 
                    doubtful_debt_amount, 
                    bad_debt_expense, 
                    provision_doubtful_debt
			from `tabPayment Detail` 
			where docstatus=1
			and parent = %(name)s and donor = %(donor_id)s and idx = %(idx)s """, filters, as_dict=1)[0]
		
# @frappe.whitelist()
# def record_doubtful_debt(doc, values):
# 	frappe.msgprint('under development')
# 	doc = frappe._dict(ast.literal_eval(doc))
# 	values = frappe._dict(ast.literal_eval(values))
