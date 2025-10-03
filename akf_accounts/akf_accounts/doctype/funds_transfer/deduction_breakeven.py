
import frappe

def apply_deduction_breakeven(self):

	def get_deduction_details(row, deduction_breakeven):
		
		# _breakeven = [d for d in deduction_breakeven if(d.random_id == row.random_id)]
		
		# if (_breakeven):
		# 	return _breakeven

		return frappe.db.sql(f"""
				SELECT 
					company, income_type,
					(select project from `tabIncome Type` where name = dd.income_type) as project, 
					account, percentage, min_percent, max_percent
					
				FROM 
					`tabDeduction Details` dd
				WHERE 
					ifnull(account, "")!=""
					and company = '{self.company}'
					and parent = '{row.fund_class}'
				""", as_dict=True)

	def set_deduction_details(row, args):
		args.update({
				"project_id": row.project,
				"cost_center_id": row.ff_cost_center,
				"fund_class_id": row.fund_class,
				"service_area_id": row.ff_service_area,
				"subservice_area_id": row.ff_subservice_area,
				"product_id": row.ff_product,
				
				"donor_id": row.ff_donor,
				"donor_type_id": row.donor_type,
				"donor_desk_id": row.donor_desk,
				"intention_id": row.donation_type,
				"transaction_type_id": row.transaction_type,
				
				"donation_amount": row.ff_transfer_amount,
				"amount": percentage_amount,
				"base_amount": percentage_amount
				})
		self.append("deduction_breakeven", args)

	deduction_breakeven = self.deduction_breakeven
	self.set("deduction_breakeven", [])
	total_deduction=0
	total_amount=0
	outstanding_amount=0

	for row in self.funds_transfer_from:
		amount = row.ff_transfer_amount
		if(not amount): frappe.throw(f"Row#{row.idx}, please set amount in `Funds Transfer To`!")
		total_amount+= amount
		
		# Setup Deduction Breakeven
		temp_deduction_amount=0
		# Looping
		""" _breakeven = [d for d in deduction_breakeven if(d.random_id == row.random_id)]
		_deduction_breakeven = _breakeven if(_breakeven) else get_deduction_details(row) """
		for args in get_deduction_details(row, deduction_breakeven):
			# print("_deduction_breakeven: ", args.random_id)
			percentage_amount = 0
			
			if(amount>0 or self.is_return):
				percentage_amount = amount*(args.percentage/100)
				# base_amount = self.apply_currecny_exchange(percentage_amount)
				temp_deduction_amount += percentage_amount
			
			set_deduction_details(row, args)			
		
		
		row.outstanding_amount = (amount - temp_deduction_amount)
		total_deduction +=  temp_deduction_amount
		outstanding_amount += (total_amount-total_deduction)
		
	
	self.total_amount = total_amount
	self.total_deduction = total_deduction
	self.outstanding_amount = outstanding_amount  

def make_deduction_gl_entries(self):
	args = get_gl_entry_dict(self)
	# Loop through each row in the child table `deduction_breakeven`
	for row in self.deduction_breakeven:
		""" In normal case, accounts are going to be credit
		But, in return case accounts are debit.
			"""
		# debit = row.base_amount if(self.is_return) else 0
		# credit = 0 if(self.is_return) else row.base_amount
		debit = 0
		credit = row.base_amount

		args.update({
			"account": row.account,
			"cost_center": row.cost_center_id,
			"debit": debit,
			"credit": credit,
			"debit_in_account_currency": debit,
			"credit_in_account_currency": credit,

			"debit_in_transaction_currency": debit,
			"credit_in_transaction_currency": credit,
			
			"project": row.project_id,
			"cost_center": row.cost_center_id,
			"fund_class": row.fund_class_id,
			"service_area": row.service_area_id,
			"subservice_area": row.subservice_area_id,
			"product": row.product_id,
			
			"donor": row.donor_id,
			"donor_type": row.donor_type_id,
			"donor_desk": row.donor_desk_id,
			"donation_type": row.intention_id,
			"transaction_type": row.transaction_type_id,
			
			"voucher_detail_no": row.name,
		})
		doc = frappe.get_doc(args)
		doc.save(ignore_permissions=True)
		doc.submit()

def get_gl_entry_dict(self):
		return frappe._dict({
			'doctype': 'GL Entry',
			'posting_date': self.posting_date,
			'transaction_date': self.posting_date,
			'against': f"Funds Transfer: {self.name}",
			'against_voucher_type': 'Funds Transfer',
			'against_voucher': self.name,
			'voucher_type': 'Funds Transfer',
			'voucher_no': self.name,
			'voucher_subtype': 'Receive',
			# 'remarks': self.instructions_internal,
			# 'is_opening': 'No',
			# 'is_advance': 'No',
			'company': self.company,
			# 'transaction_currency': self.to_currency,
			'transaction_exchange_rate': "1",
		})
