# Developer Aqsa Abbasi
import frappe
from frappe.model.document import Document
import json
import datetime
# from frappe import today

class FundsTransfer(Document):
    # def validate(self):
    #     transaction_types = ['Inter Branch', 'Inter Fund', 'Inter Company']
    #     if self.transaction_type in transaction_types:
        #    self.create_gl_entries_for_inter_funds_transfer() 
    def validate(self):
        today_date = datetime.datetime.now().today()
        self.posting_date = today_date
        # self.create_gl_entries_for_inter_funds_transfer()
        self.validate_cost_center()
        self.validate_bank_accounts()
        # self.create_gl_entries_for_inter_funds_transfer()

    def on_submit(self):
        transaction_types = ['Inter Branch', 'Inter Fund']
        if self.transaction_type in transaction_types:
            self.create_gl_entries_for_inter_funds_transfer()
    def on_cancel(self):
        self.delete_all_gl_entries()
    
    def delete_all_gl_entries(self):
        frappe.db.sql("DELETE FROM `tabGL Entry` WHERE voucher_no = %s", self.name)

    def validate_cost_center(self):
        if self.transaction_type == 'Inter Branch':
            if self.custom_from_cost_center == self.custom_to_cost_center:
                frappe.throw("Cost Centers cannot be same in Inter Branch Transfer")

    def validate_bank_accounts(self):
        if self.transaction_type == 'Inter Branch':
            if self.custom_from_bank_account == self.custom_to_bank_account:
                frappe.throw("Banks cannot be same in Inter Branch Transfer")
    
    def create_gl_entries_for_inter_funds_transfer(self):
        if not self.funds_transfer_to:
            frappe.throw("There is no information to transfer funds.")
            return

        donor_list_data = self.donor_list_for_purchase_receipt()
        donor_list = donor_list_data['donor_list']
        previous_dimensions = []
        new_dimensions = []
        total_balance = 0.0

        # Extract donor IDs from funds_transfer_from and funds_transfer_to
        donor_ids_from = {p.ff_donor for p in self.funds_transfer_from if p.ff_donor}
        donor_ids_to = {n.ft_donor for n in self.funds_transfer_to if n.ft_donor}

        # Check if any donor ID in funds_transfer_from is not in funds_transfer_to
        missing_donor_ids = donor_ids_from - donor_ids_to
        if missing_donor_ids:
            missing_donors_message = ", ".join(missing_donor_ids)
            frappe.throw(f"No details are provided for Donor(s): {missing_donors_message}")

        if donor_list:
            for d in donor_list:
                prev_donor = d.get('donor')
                prev_cost_center = d.get('cost_center')
                prev_project = d.get('project')
                prev_program = d.get('service_area')
                prev_subservice_area = d.get('subservice_area')
                prev_product = d.get('product')
                prev_amount = float(d.get('balance', 0.0))
                prev_account = d.get('account')
                prev_company = d.get('company')

                total_transfer_amount = 0.0

                # Iterate over each fund transfer to match with funds_transfer_from
                for n in self.funds_transfer_to:
                    new_donor = n.get('ft_donor')
                    new_amount = float(n.get('ft_amount', 0.0))  # Required amount to transfer
                    new_cost_center = n.get('ft_cost_center')
                    new_account = n.get('ft_account')
                    new_project = n.get('ft_project')
                    new_program = n.get('ft_service_area')
                    new_subservice_area = n.get('ft_subservice_area')
                    new_product = n.get('ft_product')
                    new_company = n.get('ft_company')

                    if prev_donor == new_donor:
                        if prev_amount >= new_amount:  # Sufficient balance for this transfer
                            # frappe.msgprint(f"Donor {prev_donor} has enough balance. Transferring {new_amount}.")

                            # Credit entry for new dimension
                            gl_entry_for_bank_credit = frappe.get_doc({
                                'doctype': 'GL Entry',
                                'posting_date': self.posting_date,
                                'transaction_date': self.posting_date,
                                'account': self.custom_from_bank,
                                'against_voucher_type': 'Funds Transfer',
                                'against_voucher': self.name,
                                'cost_center': new_cost_center,
                                'debit': 0.0,
                                'credit': new_amount,
                                'account_currency': 'PKR',
                                'debit_in_account_currency': 0.0,
                                'credit_in_account_currency': new_amount,
                                'against': new_account,
                                'voucher_type': 'Funds Transfer',
                                'voucher_no': self.name,
                                'remarks': 'Funds Transferred',
                                'is_opening': 'No',
                                'is_advance': 'No',
                                'fiscal_year': '2024-2025',
                                'company': new_company,
                                'transaction_currency': 'PKR',
                                'debit_in_transaction_currency': 0.0,
                                'credit_in_transaction_currency': new_amount,
                                'transaction_exchange_rate': 1,
                                'project': new_project,
                                'program': new_program,
                                'party_type': 'Donor',
                                'party': new_donor,
                                'subservice_area': new_subservice_area,
                                'donor': new_donor,
                                'inventory_flag': 'Purchased',
                                'product': new_product
                            })

                            gl_entry_for_bank_credit.insert(ignore_permissions=True)
                            gl_entry_for_bank_credit.submit()
                            
                            # Debit entry for previous dimension
                            gl_entry_for_previous_dimension = frappe.get_doc({
                                'doctype': 'GL Entry',
                                'posting_date': self.posting_date,
                                'transaction_date': self.posting_date,
                                'account': prev_account,
                                'against_voucher_type': 'Funds Transfer',
                                'against_voucher': self.name,
                                'cost_center': prev_cost_center,
                                'debit': new_amount,
                                'credit': 0.0,
                                'account_currency': 'PKR',
                                'debit_in_account_currency': new_amount,
                                'credit_in_account_currency': 0.0,
                                'against': prev_account,
                                'voucher_type': 'Funds Transfer',
                                'voucher_no': self.name,
                                'remarks': 'Funds Transferred',
                                'is_opening': 'No',
                                'is_advance': 'No',
                                'fiscal_year': '2024-2025',
                                'company': prev_company,
                                'transaction_currency': 'PKR',
                                'debit_in_transaction_currency': new_amount,
                                'credit_in_transaction_currency': 0.0,
                                'transaction_exchange_rate': 1,
                                'project': prev_project,
                                'program': prev_program,
                                'party_type': 'Donor',
                                'party': prev_donor,
                                'subservice_area': prev_subservice_area,
                                'donor': prev_donor,
                                'inventory_flag': 'Purchased',
                                'product': prev_product
                            })

                            gl_entry_for_previous_dimension.insert(ignore_permissions=True)
                            gl_entry_for_previous_dimension.submit()


                            # Debit entry for previous dimension
                            gl_entry_for_previous_bank = frappe.get_doc({
                                'doctype': 'GL Entry',
                                'posting_date': self.posting_date,
                                'transaction_date': self.posting_date,
                                'account': self.custom_to_bank,
                                'against_voucher_type': 'Funds Transfer',
                                'against_voucher': self.name,
                                'cost_center': prev_cost_center,
                                'debit': new_amount,
                                'credit': 0.0,
                                'account_currency': 'PKR',
                                'debit_in_account_currency': new_amount,
                                'credit_in_account_currency': 0.0,
                                'against': prev_account,
                                'voucher_type': 'Funds Transfer',
                                'voucher_no': self.name,
                                'remarks': 'Funds Transferred',
                                'is_opening': 'No',
                                'is_advance': 'No',
                                'fiscal_year': '2024-2025',
                                'company': prev_company,
                                'transaction_currency': 'PKR',
                                'debit_in_transaction_currency': new_amount,
                                'credit_in_transaction_currency': 0.0,
                                'transaction_exchange_rate': 1,
                                'project': prev_project,
                                'program': prev_program,
                                'party_type': 'Donor',
                                'party': prev_donor,
                                'subservice_area': prev_subservice_area,
                                'donor': prev_donor,
                                'inventory_flag': 'Purchased',
                                'product': prev_product
                            })

                            gl_entry_for_previous_bank.insert(ignore_permissions=True)
                            gl_entry_for_previous_bank.submit()

                            # Credit entry for new dimension
                            gl_entry_for_new_dimension = frappe.get_doc({
                                'doctype': 'GL Entry',
                                'posting_date': self.posting_date,
                                'transaction_date': self.posting_date,
                                'account': new_account,
                                'against_voucher_type': 'Funds Transfer',
                                'against_voucher': self.name,
                                'cost_center': new_cost_center,
                                'debit': 0.0,
                                'credit': new_amount,
                                'account_currency': 'PKR',
                                'debit_in_account_currency': 0.0,
                                'credit_in_account_currency': new_amount,
                                'against': new_account,
                                'voucher_type': 'Funds Transfer',
                                'voucher_no': self.name,
                                'remarks': 'Funds Transferred',
                                'is_opening': 'No',
                                'is_advance': 'No',
                                'fiscal_year': '2024-2025',
                                'company': new_company,
                                'transaction_currency': 'PKR',
                                'debit_in_transaction_currency': 0.0,
                                'credit_in_transaction_currency': new_amount,
                                'transaction_exchange_rate': 1,
                                'project': new_project,
                                'program': new_program,
                                'party_type': 'Donor',
                                'party': new_donor,
                                'subservice_area': new_subservice_area,
                                'donor': new_donor,
                                'inventory_flag': 'Purchased',
                                'product': new_product
                            })

                            gl_entry_for_new_dimension.insert(ignore_permissions=True)
                            gl_entry_for_new_dimension.submit()


                            

                            frappe.msgprint("GL Entries Created Successfully")
                        else:
                            frappe.throw(f"Not enough amount to transfer for Donor {new_donor}")

    


           

    

    # def create_gl_entries_for_inter_funds_transfer(self):
    #     if not self.funds_transfer_to:
    #         frappe.throw("There is no information to transfer funds.")
    #         return
    #     donor_list_data = self.donor_list_for_purchase_receipt()
    #     donor_list = donor_list_data['donor_list']
    #     # frappe.msgprint(frappe.as_json("donor_list"))
    #     # frappe.msgprint(frappe.as_json(donor_list))
        
    #     previous_dimensions = []
    #     new_dimensions = []
    #     total_balance = 0.0

    #     # Extract donor IDs from funds_transfer_from
    #     donor_ids_from = {p.ff_donor for p in self.funds_transfer_from if p.ff_donor}
    #     # Extract donor IDs from funds_transfer_to
    #     donor_ids_to = {n.ft_donor for n in self.funds_transfer_to if n.ft_donor}

    #     # Check if any donor ID in funds_transfer_from is not in funds_transfer_to
    #     missing_donor_ids = donor_ids_from - donor_ids_to
    #     if missing_donor_ids:
    #         missing_donors_message = ", ".join(missing_donor_ids)
    #         frappe.throw(f"No details are provided for Donor(s): {missing_donors_message}")

    #     if donor_list:
    #         for d in donor_list:
    #             prev_donor = d.get('donor')
    #             prev_cost_center = d.get('cost_center')
    #             prev_project = d.get('project')
    #             prev_program = d.get('service_area')
    #             prev_subservice_area = d.get('subservice_area')
    #             prev_product = d.get('product')
    #             prev_amount = float(d.get('balance', 0.0))
    #             prev_account = d.get('account')
    #             prev_company = d.get('company')

    #             # Debugging messages
    #             # frappe.msgprint(frappe.as_json("prev_amount"))
    #             # frappe.msgprint(frappe.as_json(prev_amount))
       
            
    #     #     if prev_program is None:
    #     #         frappe.msgprint(f"Program for donor {prev_donor} is missing or not set.")
    #     #     else:
    #     #         frappe.msgprint(f"Program for donor {prev_donor} is {prev_program}.")
    #     # else:
    #     #     frappe.msgprint("Donor list is empty.")

    #     new_dimensions_list = self.get_new_dimensions(donor_list)
    #     for f in new_dimensions_list:
    #         returned_fields = f.get('fields')

    #         for new in returned_fields:
    #             new_donor = new.get('donor')
    #             new_cost_center = new.get('cost_center')
    #             new_project = new.get('project')
    #             new_program = new.get('service_area')
    #             new_subservice_area = new.get('subservice_area')
    #             new_product = new.get('product')
    #             new_amount = float(new.get('amount', 0.0))
    #             new_account = new.get('account')
    #             new_company = new.get('company')
    #             # frappe.msgprint(frappe.as_json("new_program"))
    #             # frappe.msgprint(frappe.as_json(new_program))

    #             if new_amount > 0:  
    #                 # frappe.msgprint(frappe.as_json("new_amount > 0"))
    #                 # frappe.msgprint(frappe.as_json(new_amount))
                  
    #                 if new_amount <= prev_amount:
    #                     # frappe.msgprint(frappe.as_json("new_amount <= prev_amount:"))
    #                     # frappe.msgprint(f"New amount {new_amount} is less than or equal to the previous amount {prev_amount}. Donation is allowed.")
                        
    #                     #Creating GL entry for previous dimension (debit)
    #                     gl_entry_for_previous_dimension = frappe.get_doc({
    #                         'doctype': 'GL Entry',
    #                         'posting_date': self.posting_date,
    #                         'transaction_date': self.posting_date,
    #                         'account': prev_account,
    #                         'against_voucher_type': 'Funds Transfer',
    #                         'against_voucher': self.name,
    #                         'cost_center': prev_cost_center,
    #                         'debit': new_amount,
    #                         'credit': 0.0,
    #                         'account_currency': 'PKR',
    #                         'debit_in_account_currency': new_amount,
    #                         'credit_in_account_currency': 0.0,
    #                         'against': prev_account,
    #                         'voucher_type': 'Funds Transfer',
    #                         'voucher_no': self.name,
    #                         'remarks': 'Funds Transferred',
    #                         'is_opening': 'No',
    #                         'is_advance': 'No',
    #                         'fiscal_year': '2024-2025',
    #                         'company': prev_company,
    #                         'transaction_currency': 'PKR',
    #                         'debit_in_transaction_currency': new_amount,
    #                         'credit_in_transaction_currency': 0.0,
    #                         'transaction_exchange_rate': 1,
    #                         'project': prev_project,
    #                         'program': prev_program,
    #                         'party_type': 'Donor',
    #                         'party': prev_donor,
    #                         'subservice_area': prev_subservice_area,
    #                         'donor': prev_donor,
    #                         'inventory_flag': 'Purchased',
    #                         'product': prev_product
    #                     })

    #                     # frappe.msgprint(frappe.as_json(gl_entry_for_previous_dimension.as_dict()))

    #                     gl_entry_for_previous_dimension.insert(ignore_permissions=True)
    #                     gl_entry_for_previous_dimension.submit()
                        

    #                     #Creating GL entry for new dimension (credit)
    #                     gl_entry_for_new_dimension = frappe.get_doc({
    #                         'doctype': 'GL Entry',
    #                         'posting_date': self.posting_date,
    #                         'transaction_date': self.posting_date,
    #                         'account': new_account,
    #                         'against_voucher_type': 'Funds Transfer',
    #                         'against_voucher': self.name,
    #                         'cost_center': new_cost_center,
    #                         'debit': 0.0,
    #                         'credit': new_amount,
    #                         'account_currency': 'PKR',
    #                         'debit_in_account_currency': 0.0,
    #                         'credit_in_account_currency': new_amount,
    #                         'against': new_account,
    #                         'voucher_type': 'Funds Transfer',
    #                         'voucher_no': self.name,
    #                         'remarks': 'Funds Transferred',
    #                         'is_opening': 'No',
    #                         'is_advance': 'No',
    #                         'fiscal_year': '2024-2025',
    #                         'company': new_company,
    #                         'transaction_currency': 'PKR',
    #                         'debit_in_transaction_currency': 0.0,
    #                         'credit_in_transaction_currency': new_amount,
    #                         'transaction_exchange_rate': 1,
    #                         'project': new_project,
    #                         'program': new_program,
    #                         'party_type': 'Donor',
    #                         'party': new_donor,
    #                         'subservice_area': new_subservice_area,
    #                         'donor': new_donor,
    #                         'inventory_flag': 'Purchased',
    #                         'product': new_product
    #                     })

    #                     # frappe.msgprint(frappe.as_json("new_program"))
    #                     # frappe.msgprint(frappe.as_json(new_program))
    #                     # frappe.msgprint(frappe.as_json(gl_entry_for_new_dimension.as_dict()))

    #                     gl_entry_for_new_dimension.insert(ignore_permissions=True)
    #                     gl_entry_for_new_dimension.submit()
    #                     frappe.msgprint("GL Entries Created Successfully")
    #                     break
                        
    #                 else:
    #                     # Check if the donor exists in 'Funds Transfer From'
    #                     donor_ids_from = {p.ff_donor for p in self.funds_transfer_from if p.ff_donor}
                        
    #                     if new_donor in donor_ids_from:
    #                         frappe.throw(f"Not enough amount to Transfer for Donor {new_donor}")
    #                     else:
    #                         frappe.throw(f"Not enough amount to Transfer against Cost Center {prev_cost_center} and Bank Account {prev_account}")

    #                     # frappe.throw(f"New amount {new_amount} is greater than the previous amount {prev_amount}. Not enough amount to donate.")
                        

    def donor_list_for_purchase_receipt(self):
        donor_list = []
        total_balance = 0
        unique_entries = set()
        docstatus = self.docstatus

        for p in self.funds_transfer_from:
            # Construct the condition
            condition_parts = []
            for field, value in [
                ('subservice_area', p.ff_subservice_area),
                ('donor', p.ff_donor),
                ('project', p.ff_project),
                ('cost_center', p.ff_cost_center),
                ('product', p.ff_product),
                ('program', p.ff_service_area),
                ('company', p.ff_company),
                ('account', p.ff_account)
            ]:
                if value in [None, 'None', '']:
                    condition_parts.append(f"({field} IS NULL OR {field} = '')")
                else:
                    condition_parts.append(f"{field} = '{value}'")

            condition = " AND ".join(condition_parts)

            # Print query for debugging
            # frappe.msgprint(f"Condition: {condition}")

            try:
                donor_entries = frappe.db.sql(f"""
                    SELECT 
                        SUM(credit - debit) AS total_balance,
                        donor,
                        program,
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
                   GROUP BY donor, program, subservice_area, project, cost_center, product, company, account
                    HAVING total_balance >= 0
                    ORDER BY total_balance DESC
                """, as_dict=True)
                # frappe.msgprint(f"Donor Entries: {donor_entries}")
            except Exception as e:
                frappe.throw(f"Error executing query: {e}")

            match_found = False

            for entry in donor_entries:
                if ((entry.get('program') == p.ff_service_area or (not entry.get('program') and not p.ff_service_area)) and
                    (entry.get('subservice_area') == p.ff_subservice_area or (not entry.get('subservice_area') and not p.ff_subservice_area)) and
                    (entry.get('project') == p.ff_project or (not entry.get('project') and not p.ff_project)) and
                    (entry.get('cost_center') == p.ff_cost_center or (not entry.get('cost_center') and not p.ff_cost_center)) and
                    (entry.get('product') == p.ff_product or (not entry.get('product') and not p.ff_product)) and
                    (entry.get('account') == p.ff_account or (not entry.get('account') and not p.ff_account)) and
                    (entry.get('company') == p.ff_company or (not entry.get('company') and not p.ff_company))):

                    entry_key = (
                        entry.get('donor'), 
                        entry.get('program'), 
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

                        if docstatus == 1:
                            try:
                                used_amount_data = frappe.db.sql(f"""
                                    SELECT SUM(debit) as used_amount
                                    FROM `tabGL Entry`
                                    WHERE 
                                        
                                        voucher_no = '{self.name}'
                                        {f'AND {condition}' if condition else ''}
                                """, as_dict=True)
                                if used_amount_data:
                                    used_amount = used_amount_data[0].get('used_amount', 0)
                            except Exception as e:
                                frappe.throw(f"Error fetching used amount: {e}")

                        donor_list.append({
                            "donor": p.ff_donor,
                            "service_area": p.ff_service_area,
                            "subservice_area": p.ff_subservice_area,
                            "project": p.ff_project,
                            "cost_center": p.ff_cost_center,
                            "product": p.ff_product,
                            "company": p.ff_company,
                            "account": p.ff_account,
                            "balance": balance,
                            "used_amount": used_amount,
                        })
                        # frappe.msgprint(f"donor_list: {donor_list}")
                        

                        total_balance += balance
                        match_found = True
                        break

            if not match_found:
                if p.ff_donor:
                    frappe.msgprint(f'No such entry exists for donor "<bold>{p.ff_donor}</bold>" with provided details.')
                else: 
                    frappe.msgprint(f'No such entry exists against Cost Center "<bold>{p.ff_cost_center,}</bold>" and Bank Account {p.ff_account}.')

        # if donor_list:
        #     frappe.msgprint('GL Entries Created Successfully')

        return {
            "total_balance": total_balance,
            "donor_list": donor_list  
        }


    def get_new_dimensions(self, donor_list):
        result = []
        fields = []
        docstatus = self.docstatus
        for n in self.funds_transfer_to:
            for p in donor_list:
                # if (n.ft_donor == p.get('donor') or n.ft_cost_center == p.get('cost_center') or
                #     n.ft_service_area == p.get('program') or n.ft_subservice_area == p.get('subservice_area')):
                    fields.append({
                        'donor': n.ft_donor,
                        'cost_center': n.ft_cost_center,
                        'project': n.ft_project,
                        'service_area': n.ft_service_area,
                        'subservice_area': n.ft_subservice_area,
                        'product': n.ft_product,
                        'amount': n.ft_amount,
                        'account': n.ft_account,
                        'company': n.ft_company
                    })
            if fields:
                result.append({
                    'fields': fields
                })
        return result


@frappe.whitelist()
def donor_list_data(doc):
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
            ('project', p.ff_project),
            ('cost_center', p.ff_cost_center),
            ('product', p.ff_product),
            ('program', p.ff_service_area),
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
                program,
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
               
            GROUP BY donor, program, subservice_area, project, cost_center, product, company, account
           
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
            if ((entry.get('program') == p.ff_service_area or (not entry.get('program') and not p.ff_service_area)) and
                (entry.get('subservice_area') == p.ff_subservice_area or (not entry.get('subservice_area') and not p.ff_subservice_area)) and
                (entry.get('project') == p.ff_project or (not entry.get('project') and not p.ff_project)) and
                (entry.get('cost_center') == p.ff_cost_center or (not entry.get('cost_center') and not p.ff_cost_center)) and
                (entry.get('product') == p.ff_product or (not entry.get('product') and not p.ff_product)) and
                (entry.get('account') == p.ff_account or (not entry.get('account') and not p.ff_account)) and
                (entry.get('company') == p.ff_company or (not entry.get('company') and not p.ff_company))):
                
                entry_key = (
                    entry.get('donor'), 
                    entry.get('program'), 
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
                    if balance == 0:
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
                        "project": p.ff_project,
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


# @frappe.whitelist()
# def get_service_areas(doctype, txt, searchfield, start, page_len, filters):
#     filters = frappe.parse_json(filters) if isinstance(filters, str) else filters
#     company = filters.get('company')
#     service_area = filters.get('service_area')

#     query = """
#         SELECT name
#         FROM `tabProgram` as p
#         WHERE EXISTS (
#             SELECT 1
#             FROM `tabAccounts Default` as ad
#             WHERE ad.parent = p.name AND company=%s
#         ) 
#     """

#     return frappe.db.sql(query, (company))

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

