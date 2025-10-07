# Developer Aqsa Abbasi
import frappe
from frappe.model.document import Document
import json
import datetime
from erpnext.accounts.utils import get_fiscal_year
from frappe.utils import (
    today, fmt_money, get_link_to_form
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
	
@frappe.whitelist()
def donor_list_data_funds_transfer(doc):
    try:
        doc = frappe.get_doc(json.loads(doc))
    except (json.JSONDecodeError, TypeError) as e:
        frappe.throw(f"Invalid input: {e}")

    donor_list = []
    total_balance = 0
    unique_entries = set()
    duplicate_entries = set()
    insufficient_balances = set()
    no_entries_found = set()
    docstatus = doc.docstatus
    
    
    def validate_missing_info(funds_from_row):
        # frappe.throw(frappe.as_json(funds_from_row))
        conditions = ""
        for field1, field2 in [
            ('gl.subservice_area', "ff_subservice_area"),
            ('gl.donor', "ff_donor"),
            ('gl.project', "project"),
            ('gl.cost_center', "ff_cost_center"),
            ('gl.product', "ff_product"),
            ('gl.service_area', "ff_service_area"),
            ('gl.company', "ff_company"),
            ('gl.account', "ff_account")]:
            value2 = funds_from_row.get(field2)
            if(value2):
                conditions += f" and {field1} = '{value2}' "
            else:
                label =  field2.replace("ff_", "")
                label =  label.replace("_", " ")
                frappe.throw(f"Row#{funds_from_row.idx}, please select <b>{label.capitalize()}</b>", title="Funds Transfer From")
        return conditions
    
    def get_donor_list(condition):
        """ sql by nabeel saleem """
        query = f"""  Select 
                ifnull((sum(distinct gl.credit) - sum(distinct gl.debit)),0) as total_balance,
                gl.donor,
                (select donor_name from `tabDonor` where name=gl.donor) as donor_name,
                gl.service_area,
                gl.subservice_area,
                gl.project,
                gl.cost_center,
                gl.product,
                gl.company,
                gl.account
            From 
                `tabGL Entry` gl, `tabDonation` d, `tabFunds Transfer` ft
            Where 
                (gl.voucher_no = d.name or gl.voucher_no = ft.name)
                and d.contribution_type ='Donation'
                and gl.is_cancelled=0
                and voucher_type  in ('Donation', 'Funds Transfer')
                and gl.account in (select name from `tabAccount` where disabled=0 and account_type='Equity' and name=gl.account)
                {f'{condition}' if condition else ''}
            Having 
                total_balance>0
            Order By 
                total_balance desc
            """
        return frappe.db.sql(query, as_dict=True)
            
    for p in doc.funds_transfer_from:
        # Construct the condition
        condition = validate_missing_info(p)
        try:
            donor_entries = get_donor_list(condition)
            # frappe.msgprint(f"donor_entries: {donor_entries}")
        except Exception as e:
            frappe.throw(f"Error executing query: {e}")
        match_found = False

        for entry in donor_entries:
            entry_key = (
                entry.get('donor'), 
                entry.get('service_area'), 
                entry.get('subservice_area'), 
                entry.get('project'),
                entry.get('cost_center'),
                entry.get('product'),
                entry.get('company'),
                entry.get('account'),
            )

            if entry_key in unique_entries:
                # Mark it as a duplicate and notify the user
                if entry_key not in duplicate_entries:
                    duplicate_entries.add(entry_key)
                    frappe.msgprint(f'<span style="color: red;">Row#{p.idx}; duplicate entry exists for donor "{entry.get("donor")}" with provided details.</span>')
            else:
                # Add to unique entries if not seen before
                unique_entries.add(entry_key)
                balance = entry.total_balance
                used_amount = 0

                # Handle balance checks
                if balance <= 0.0 and not doc.is_new() and docstatus == 0:
                    # Exclude negative balances and track insufficient balance
                    if balance < 0:
                        insufficient_balances.add(entry.get('donor'))
                    else:
                        if p.ff_donor:
                            insufficient_balances.add(p.ff_donor)
                        else: 
                            insufficient_balances.add(f"Cost Center '{p.ff_cost_center}' and Bank Account {p.ff_account}")
                    match_found = True
                    break

                # Fetch used amount if needed
                if docstatus == 1:
                    try:
                        used_amount_query = f"""
                            SELECT SUM(debit) as used_amount
                            FROM `tabGL Entry`
                            WHERE 
                                voucher_no = '{doc.name}'
                                {f'AND {condition}' if condition else ''}
                        """
                        used_amount_data = frappe.db.sql(used_amount_query, as_dict=True)
                        if used_amount_data:
                            used_amount = used_amount_data[0].get('used_amount', 0)
                    except Exception as e:
                        frappe.throw(f"Error fetching used amount: {e}")

                # Append donor data to the donor list
                donor_list.append({
                    "donor": p.ff_donor,
                    "donor_name": p.ff_donor_name or "-",
                    "service_area": p.ff_service_area,
                    "subservice_area": p.ff_subservice_area,
                    "project": p.project,
                    "cost_center": p.ff_cost_center,
                    "product": p.ff_product,
                    "company": p.ff_company,
                    "account": p.ff_account,
                    "balance": fmt_money(balance, currency="PKR"),
                    "used_amount": fmt_money(used_amount, currency="PKR"),
                })
                total_balance += balance
                match_found = True
    
        # Only add to no_entries_found if not a duplicate entry
        if not match_found and p.ff_donor not in [entry[0] for entry in duplicate_entries]:
            if p.ff_donor:
                no_entries_found.add(p.ff_donor)
            else: 
                no_entries_found.add(f"Cost Center '{p.ff_cost_center}' and Bank Account {p.ff_account}")

    # Display insufficient balance messages for tracked donors
    if docstatus == 0 :
        for donor in insufficient_balances:
            if donor not in [entry[0] for entry in duplicate_entries]:
                if donor:
                    frappe.msgprint(f'<span style="color: red;">Insufficient balance for donor "{donor}" with provided details.</span>')
                

        # Display no entries found messages
        for item in no_entries_found:
            frappe.msgprint(f'<span style="color: red;">No balance exists for <b>{item}</b> with provided details.</span>', title="Funds Transfer From")

    return {
        "total_balance": fmt_money(total_balance, currency="PKR"),
        "donor_list": donor_list  
    }

@frappe.whitelist()
def donor_list_data_funds_transfer_previous(doc):
    try:
        doc = frappe.get_doc(json.loads(doc))
    except (json.JSONDecodeError, TypeError) as e:
        frappe.throw(f"Invalid input: {e}")

    donor_list = []
    total_balance = 0
    unique_entries = set()
    docstatus = doc.docstatus

    for p in doc.funds_transfer_from:
        # Construct the condition
        condition_parts = []
        for field, value in [
            ('subservice_area', p.ff_subservice_area),
            ('donor', p.ff_donor),
            ('project', p.project),
            ('cost_center', p.ff_cost_center),
            ('product', p.ff_product),
            ('service_area', p.ff_service_area),
            ('company', p.ff_company),
            ('account', p.ff_account)
        ]:
            if value in [None, 'None', '']:
                condition_parts.append(f"({field} IS NULL OR {field} = '')")
            else:
                condition_parts.append(f"{field} = '{value}'")

        condition = " AND ".join(condition_parts)
        # frappe.msgprint(f"Condition: {condition}")

        query = f"""
            SELECT 
                SUM(credit - debit) AS total_balance,
                donor,
                service_area,
                subservice_area,
                project,
                cost_center,
                product,
                company,
                account
            FROM `tabGL Entry`
            WHERE 
                is_cancelled = 'No'
                {f'AND {condition}' if condition else ''}
               
            GROUP BY donor, service_area, subservice_area, project, cost_center, product, company, account
           
            ORDER BY total_balance DESC
        """
        # frappe.msgprint(f"Executing query: {query}")

        try:
            donor_entries = frappe.db.sql(query, as_dict=True)
            # frappe.msgprint(f"donor_entries: {donor_entries}")
        except Exception as e:
            frappe.throw(f"Error executing query: {e}")

        match_found = False

        for entry in donor_entries:
            if ((entry.get('service_area') == p.ff_service_area or (not entry.get('service_area') and not p.ff_service_area)) and
                (entry.get('subservice_area') == p.ff_subservice_area or (not entry.get('subservice_area') and not p.ff_subservice_area)) and
                (entry.get('project') == p.project or (not entry.get('project') and not p.project)) and
                (entry.get('cost_center') == p.ff_cost_center or (not entry.get('cost_center') and not p.ff_cost_center)) and
                (entry.get('product') == p.ff_product or (not entry.get('product') and not p.ff_product)) and
                (entry.get('account') == p.ff_account or (not entry.get('account') and not p.ff_account)) and
                (entry.get('company') == p.ff_company or (not entry.get('company') and not p.ff_company))):
                
                entry_key = (
                    entry.get('donor'), 
                    entry.get('service_area'), 
                    entry.get('subservice_area'), 
                    entry.get('project'),
                    entry.get('cost_center'),
                    entry.get('product'),
                    entry.get('company'),
                    entry.get('account'),
                )

                if entry_key not in unique_entries:
                    unique_entries.add(entry_key)
                    balance = entry['total_balance']
                    used_amount = 0

                    # Check if the balance is 0
                    if balance == 0.0 and not doc.is_new() and docstatus == 0:
                    # if balance <= 0:
                        if p.ff_donor:
                            frappe.msgprint(f"Insufficient balance for donor '{p.ff_donor}' with provided details.")
                        else: 
                            frappe.msgprint(f"Insufficient balance against Cost Center '{p.ff_cost_center}' and Bank Account {p.ff_account}")
                        match_found = True
                        break

                    if docstatus == 1:
                        try:
                            used_amount_query = f"""
                                SELECT SUM(debit) as used_amount
                                FROM `tabGL Entry`
                                WHERE 
                                    voucher_no = '{doc.name}'
                                    {f'AND {condition}' if condition else ''}
                            """
                            # frappe.msgprint(f"Executing used_amount_query: {used_amount_query}")
                            used_amount_data = frappe.db.sql(used_amount_query, as_dict=True)
                            if used_amount_data:
                                used_amount = used_amount_data[0].get('used_amount', 0)
                        except Exception as e:
                            frappe.throw(f"Error fetching used amount: {e}")

                    donor_list.append({
                        "donor": p.ff_donor,
                        "service_area": p.ff_service_area,
                        "subservice_area": p.ff_subservice_area,
                        "project": p.project,
                        "cost_center": p.ff_cost_center,
                        "product": p.ff_product,
                        "company": p.ff_company,
                        "account": p.ff_account,
                        "balance": balance,
                        "used_amount": used_amount,
                    })
                    # frappe.msgprint(f"Donor List: {donor_list}")
                    total_balance += balance
                    match_found = True
                    break


        if not match_found:
            if p.ff_donor:
                frappe.msgprint(f'No such entry exists for donor "<bold>{p.ff_donor}</bold>" with provided details.')
            else: 
                frappe.msgprint(f'No such entry exists against Cost Center "<bold>{p.ff_cost_center,}</bold>" and Bank Account {p.ff_account}with provided details.')
    if donor_list:
        pass
        # frappe.msgprint('GL Entries Created Successfully')

    return {
        "total_balance": total_balance,
        "donor_list": donor_list  
    }

@frappe.whitelist()
def get_service_areas(doc):
    try:
        doc = frappe.get_doc(json.loads(doc))
    except (json.JSONDecodeError, TypeError) as e:
        frappe.throw(f"Invalid input: {e}")
    # frappe.msgprint(frappe.as_json(doc))

    company = []
    for f in doc.funds_transfer_from:
        company.append(f.ff_company)
    # frappe.msgprint(frappe.as_json(company))
    return company


def _get_gl_structure(self):
	fiscal_year = get_fiscal_year(today(), company=self.company)[0]
	return {
		'doctype': 'GL Entry',
		'posting_date': self.posting_date,
		'transaction_date': self.posting_date,
		'party_type': '',
		'party': '',
		'voucher_type': 'Funds Transfer',
		'voucher_no': self.name,
		'against_voucher_type': 'Funds Transfer',
		'against_voucher': self.name,
		'remarks': 'Funds Transferred',
		'is_opening': 'No',
		'is_advance': 'No',
		'fiscal_year': fiscal_year,
		'company': self.company,
		'account_currency': 'PKR',
		'transaction_currency': 'PKR',
		'transaction_exchange_rate': 1,
		'project': '',
		'service_area': '',
		'subservice_area': '',
		'product': '',     
		'donor': '',
		'inventory_flag': '',
		# not common arguments
		'cost_center': '',
		'account': '',
		'against': '',
		'debit': 0.0,
		'credit': 0.0,
		'debit_in_account_currency': 0.0,
		'credit_in_account_currency': 0.0,
		'debit_in_transaction_currency': 0.0,
		'credit_in_transaction_currency': 0.0
	}
