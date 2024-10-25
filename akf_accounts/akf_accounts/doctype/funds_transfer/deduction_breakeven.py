
import frappe

def apply_deduction_breakeven(self):

    def reset_mode_of_payment(row):
        if(self.contribution_type == "Pledge"):
            row.mode_of_payment = None
            row.account_paid_to = None
            row.transaction_no_cheque_no = ""
            row.reference_date = None

    def get_deduction_details(row, deduction_breakeven):
        
        _breakeven = [d for d in deduction_breakeven if(d.random_id == row.random_id)]
        
        if (_breakeven):
            return _breakeven

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
                    and parent = '{row.ft_service_area}'
                    and project = '{row.project}'
                """, as_dict=True)

    def set_deduction_details(row, args):
        args.update({
                "donor": row.ft_donor,
                "program": row.ft_service_area,
                "subservice_area": row.ft_subservice_area,
                "product": row.ft_product,
                "donation_amount": row.ft_amount,
                "amount": percentage_amount,
                "base_amount": percentage_amount,
                "service_area": row.ft_service_area,
                "project": row.project,
                
                "cost_center": self.to_cost_center,
                "random_id": row.random_id,
                })
        self.append("deduction_breakeven", args)

    def get_defaul_accounts(service_area, fieldname):
        return frappe.db.get_value('Accounts Default', {'parent': service_area, 'company': self.company}, fieldname)

    def set_total_donors():
        self.total_donors = len(self.payment_detail)

    deduction_breakeven = self.deduction_breakeven
    self.set("deduction_breakeven", [])
    total_deduction=0
    total_amount=0
    outstanding_amount=0

    for row in self.funds_transfer_to:
        # print("payment_detail: ", row.random_id)
        # reset_mode_of_payment(row)
        if(not row.ft_amount): frappe.throw(f"Row#{row.idx}, please set amount in `Funds Transfer To`!")
        total_amount+= row.ft_amount
        # row.base_donation_amount = self.apply_currecny_exchange(row.donation_amount)
        # Setup Deduction Breakeven
        temp_deduction_amount=0
        # Looping
        """ _breakeven = [d for d in deduction_breakeven if(d.random_id == row.random_id)]
        _deduction_breakeven = _breakeven if(_breakeven) else get_deduction_details(row) """
        for args in get_deduction_details(row, deduction_breakeven):
            # print("_deduction_breakeven: ", args.random_id)
            percentage_amount = 0
            base_amount = 0
            
            if(row.ft_amount>0 or self.is_return):
                percentage_amount = row.ft_amount*(args.percentage/100)
                # base_amount = self.apply_currecny_exchange(percentage_amount)
                temp_deduction_amount += percentage_amount
            
            set_deduction_details(row, args)			
        
        # row.equity_account = row.equity_account  if(row.equity_account) else get_defaul_accounts(row.pay_service_area, 'equity_account')
        # row.receivable_account = row.receivable_account if(row.receivable_account) else get_defaul_accounts(row.pay_service_area, 'receivable_account')
        
        # row.cost_center = self.donation_cost_center
        # row.deduction_amount = temp_deduction_amount    
        # row.net_amount = (row.donation_amount-row.deduction_amount)
        row.outstanding_amount = (row.ft_amount - temp_deduction_amount)
        total_deduction +=  temp_deduction_amount
        outstanding_amount += (total_amount-total_deduction)
        # row.base_outstanding_amount = self.apply_currecny_exchange(row.outstanding_amount)
        # deduction_amount += temp_deduction_amount
    
    self.total_amount = total_amount
    self.total_deduction = total_deduction
    self.outstanding_amount = outstanding_amount  
    # calculate total
    # set_total_donors()
    # self.calculate_total(total_donation, deduction_amount)

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
            "cost_center": row.cost_center,
            "debit": debit,
            "credit": credit,
            "debit_in_account_currency": debit,
            "credit_in_account_currency": credit,

            "debit_in_transaction_currency": debit,
            "credit_in_transaction_currency": credit,
            
            "donor": row.donor,
            "program": row.program,
            "subservice_area": row.subservice_area,
            "product": row.product,
            "project": row.project,
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