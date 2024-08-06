# Developer Aqsa Abbasi

import frappe
from frappe.model.document import Document
import json

class FundsTransfer(Document):
    # def on_submit(self):
    #     transaction_types = ['Inter Branch', 'Inter Fund', 'Inter Company']
    #     if self.transaction_type in transaction_types:
    #         self.create_gl_entries_for_inter_funds_transfer()
    

    def validate(self):
        transaction_types = ['Inter Branch', 'Inter Fund', 'Inter Company']
        if self.transaction_type in transaction_types:
            self.create_gl_entries_for_inter_funds_transfer()

    def create_gl_entries_for_inter_funds_transfer(self):
        donor_list_data = self.donor_list_for_purchase_receipt()
        donor_list = donor_list_data['donor_list']

        for d in donor_list:
            donor = d.get('donor')
            cost_center = d.get('cost_center')
            project = d.get('project')
            program = d.get('service_area')  
            subservice_area = d.get('subservice_area')
            product = d.get('product')
            amount = d.get('balance', 0.0)  
            account = d.get('account')
            company = d.get('company')

            if not frappe.db.exists('Funds Transfer', self.name):
                frappe.throw(f"Funds Transfer document {self.name} does not exist.")

            frappe.msgprint(f"Creating GL Entry for Funds Transfer: {self.name}")
            frappe.msgprint(frappe.as_json(d))

            # gl_entry_for_previous_dimension = frappe.get_doc({
            #     'doctype': 'GL Entry',
            #     'posting_date': self.custom_posting_date,
            #     'transaction_date': self.custom_posting_date,
            #     'account': account,
            #     'against_voucher_type': 'Funds Transfer',
            #     'against_voucher': self.name,
            #     'cost_center': cost_center,
            #     'debit': amount,
            #     'credit': 0.0,
            #     'account_currency': 'PKR',
            #     'debit_in_account_currency': amount,
            #     'credit_in_account_currency': 0.0,
            #     'against': "Capital Stock - AKFP",
            #     'voucher_type': 'Funds Transfer',
            #     'voucher_no': self.name,
            #     'remarks': 'Funds Transfered',
            #     'is_opening': 'No',
            #     'is_advance': 'No',
            #     'fiscal_year': '2024-2025',
            #     'company': company,
            #     'transaction_currency': 'PKR',
            #     'debit_in_transaction_currency': amount,
            #     'credit_in_transaction_currency': 0.0,
            #     'transaction_exchange_rate': 1,
            #     'project': project,
            #     'program': program,
            #     'party_type': 'Donor',
            #     'party': donor,
            #     'subservice_area': subservice_area,
            #     'donor': donor,
            #     'inventory_flag': 'Purchased',
            #     'product': product
            # })

            # frappe.msgprint(frappe.as_json(gl_entry_for_previous_dimension.as_dict()))

            # gl_entry_for_previous_dimension.insert()
            # gl_entry_for_previous_dimension.submit()

        
        new_dimensions_list = self.get_new_dimensions(donor_list)
        frappe.msgprint(frappe.as_json("new_dimensions_list"))
        frappe.msgprint(frappe.as_json(new_dimensions_list))

        for new in new_dimensions_list:
            donor = new.get('donor')
            cost_center = new.get('cost_center')
            project = new.get('project')
            program = new.get('service_area') 
            subservice_area = new.get('subservice_area')
            product = new.get('product')
            amount = new.get('amount', 0.0)  
            account = new.get('account')
            company = new.get('company')
            frappe.msgprint(frappe.as_json("amount for new dimension"))
            frappe.msgprint(frappe.as_json(amount))

            # gl_entry_for_new_dimension = frappe.get_doc({
            #     'doctype': 'GL Entry',
            #     'posting_date': self.custom_posting_date,
            #     'transaction_date': self.custom_posting_date,
            #     'account': account,
            #     'against_voucher_type': 'Funds Transfer',
            #     'against_voucher': self.name,
            #     'cost_center': cost_center,
            #     'debit': 0.0,
            #     'credit': amount,
            #     'account_currency': 'PKR',
            #     'debit_in_account_currency': 0.0,
            #     'credit_in_account_currency': amount,
            #     'against': "Capital Stock - AKFP",
            #     'voucher_type': 'Purchase Receipt',
            #     'voucher_no': self.name,
            #     'remarks': 'Donation for item',
            #     'is_opening': 'No',
            #     'is_advance': 'No',
            #     'fiscal_year': '2024-2025',
            #     'company': company,
            #     'transaction_currency': 'PKR',
            #     'debit_in_transaction_currency': 0.0,
            #     'credit_in_transaction_currency': amount,
            #     'transaction_exchange_rate': 1,
            #     'project': project,
            #     'program': program,
            #     'party_type': 'Donor',
            #     'party': donor,
            #     'subservice_area': subservice_area,
            #     'donor': donor,
            #     'inventory_flag': 'Purchased',
            #     'product': product
            # })

            # gl_entry_for_new_dimension.insert()
            # gl_entry_for_new_dimension.submit()

    def donor_list_for_purchase_receipt(self):
        donor_list = []
        total_balance = 0
        unique_entries = set()
        docstatus = self.docstatus

        for p in self.funds_transfer_from:
            condition_parts = [
                f"(subservice_area = '{p.ff_subservice_area}' OR (subservice_area IS NULL AND '{p.ff_subservice_area}' = '') OR subservice_area = '')" if p.ff_subservice_area else "1=1",
                f"(donor = '{p.ff_donor}' OR (donor IS NULL AND '{p.ff_donor}' = '') OR donor = '')" if p.ff_donor else "1=1",
                f"(project = '{p.ff_project}' OR (project IS NULL AND '{p.ff_project}' = '') OR project = '')" if p.ff_project else "1=1",
                f"(cost_center = '{p.ff_cost_center}' OR (cost_center IS NULL AND '{p.ff_cost_center}' = '') OR cost_center = '')" if p.ff_cost_center else "1=1",
                f"(product = '{p.ff_product}' OR (product IS NULL AND '{p.ff_product}' = '') OR product = '')" if p.ff_product else "1=1",
                f"(program = '{p.ff_service_area}' OR (program IS NULL AND '{p.ff_service_area}' = '') OR program = '')" if p.ff_service_area else "1=1",
                f"(company = '{p.ff_company}' OR (company IS NULL AND '{p.ff_company}' = '') OR company = '')" if p.ff_company else "1=1",
                f"(account = '{p.ff_account}' OR (account IS NULL AND '{p.ff_account}' = '') OR account = '')" if p.ff_account else "1=1"
            ]
            condition = " AND ".join(condition_parts)

            try:
                donor_entries = frappe.db.sql(f"""
                    SELECT SUM(credit - debit) as total_balance,
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
                        account = 'Capital Stock - AKFP'
                        {f'AND {condition}' if condition else ''}
                    GROUP BY donor, program, subservice_area, project, cost_center, product, company, account
                    HAVING total_balance >= -1000000
                    ORDER BY total_balance DESC
                """, as_dict=True)
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
                                        account = 'Capital Stock - AKFP'
                                        {f'AND {condition}' if condition else ''}
                                """, as_dict=True)
                                if used_amount_data:
                                    used_amount = used_amount_data[0].get('used_amount', 0)
                            except Exception as e:
                                frappe.throw(f"Error executing used amount query: {e}")

                        available_balance = balance - used_amount

                        if available_balance > 0:
                            total_balance += available_balance
                            donor_list.append({
                                'donor': entry.get('donor'),
                                'service_area': entry.get('program'),
                                'subservice_area': entry.get('subservice_area'),
                                'project': entry.get('project'),
                                'cost_center': entry.get('cost_center'),
                                'product': entry.get('product'),
                                'balance': available_balance,
                                'account': entry.get('account'),
                                'company': entry.get('company')
                            })
                            match_found = True

            if not match_found:
                donor_list.append({
                    'donor': p.ff_donor,
                    'service_area': p.ff_service_area,
                    'subservice_area': p.ff_subservice_area,
                    'project': p.ff_project,
                    'cost_center': p.ff_cost_center,
                    'product': p.ff_product,
                    'balance': 0.0,
                    'account': p.ff_account,
                    'company': p.ff_company
                })

        return {
            'total_balance': total_balance,
            'donor_list': donor_list
        }

    def get_new_dimensions(self, donor_list):
        new_dimensions_list = []
        # frappe.msgprint(frappe.as_json("donor_list in New Dimension"))

        # frappe.msgprint(frappe.as_json(donor_list))
       
        for donor in donor_list:
            ff_donor = donor.get('donor')
            frappe.msgprint(frappe.as_json("Inside Loop donor"))
            frappe.msgprint(frappe.as_json(donor))
            
            match_found = []
        

            for f in self.funds_transfer_to:
                if f.get('ft_donor') == ff_donor:
                    match_found.append({
                        "company": f.get('ft_company'),
                        "account":f.get('ft_account'),
                        "cost_center":f.get('ft_cost_center'),
                        "service_area": f.get('ft_service_area'),
                        "subservice_area": f.get('ft_subservice_area'),
                        "product":f.get('ft_product'),
                        "project":f.get('ft_project'),
                        "amount": f.get('ft_amount')
                            
                    })

                if match_found:
                    frappe.msgprint(frappe.as_json("match_found"))
                    frappe.msgprint(frappe.as_json(match_found))
                    new_dimensions_list.append({
                        'fields': match_found

                    })
                
                frappe.msgprint(frappe.as_json("new_dimensions_list"))
                frappe.msgprint(frappe.as_json(new_dimensions_list))
               

        return new_dimensions_list


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
        condition_parts = [
            f"(subservice_area = '{p.ff_subservice_area}' OR (subservice_area IS NULL AND '{p.ff_subservice_area}' = '') OR subservice_area = '')" if p.ff_subservice_area else "1=1",
            f"(donor = '{p.ff_donor}' OR (donor IS NULL AND '{p.ff_donor}' = '') OR donor = '')" if p.ff_donor else "1=1",
            f"(project = '{p.ff_project}' OR (project IS NULL AND '{p.ff_project}' = '') OR project = '')" if p.ff_project else "1=1",
            f"(cost_center = '{p.ff_cost_center}' OR (cost_center IS NULL AND '{p.ff_cost_center}' = '') OR cost_center = '')" if p.ff_cost_center else "1=1",
            f"(product = '{p.ff_product}' OR (product IS NULL AND '{p.ff_product}' = '') OR product = '')" if p.ff_product else "1=1",
            f"(program = '{p.ff_service_area}' OR (program IS NULL AND '{p.ff_service_area}' = '') OR program = '')" if p.ff_service_area else "1=1",
            f"(company = '{p.ff_company}' OR (company IS NULL AND '{p.ff_company}' = '') OR company = '')" if p.ff_company else "1=1",
            f"(account = '{p.ff_account}' OR (account IS NULL AND '{p.ff_account}' = '') OR account = '')" if p.ff_account else "1=1"
        ]
        condition = " AND ".join(condition_parts)

        try:
            donor_entries = frappe.db.sql(f"""
                SELECT SUM(credit - debit) as total_balance,
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
                    account = 'Capital Stock - AKFP'
                    {f'AND {condition}' if condition else ''}
                GROUP BY donor, program, subservice_area, project, cost_center, product, company, account
                HAVING total_balance >= -1000000
                ORDER BY total_balance DESC
            """, as_dict=True)
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
                                    account = 'Capital Stock - AKFP'
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

                    total_balance += balance
                    match_found = True
                    break

        if not match_found:
            frappe.msgprint(f'No such entry exists for donor "<bold>{p.ff_donor}</bold>" with provided details.')

    return {
        "total_balance": total_balance,
        "donor_list": donor_list  
    }
