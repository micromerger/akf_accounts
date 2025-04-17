import frappe
# from erpnext.stock.doctype.purchase_receipt.purchase_receipt import PurchaseReceipt
import json

from akf_stock.customization.extends.custom_purchase_receipt import XPurchaseReceipt
class XAssetInvenPurchase(XPurchaseReceipt):
    # def validate(self):
        # frappe.msgprint('accounts')
        # super().validate()
        # frappe.msgprint("This is extended code. ")
        # self.create_donor_gl_entries_from_purchase_receipt_aq()
        # self.populate_childtable()

    def on_submit(self):
        super().on_submit()
        # frappe.msgprint("This is on_submit extended code. ")
        self.create_asset_inven_purchase_gl_entries()
        # self.populate_childtab.le()
        
    def on_cancel(self):
        super().on_cancel()
        # frappe.msgprint("This is on_submit extended code. ")
        self.delete_all_gl_entries()

    def delete_all_gl_entries(self):
        frappe.db.sql("DELETE FROM `tabGL Entry` WHERE voucher_no = %s", self.name)

    def create_asset_inven_purchase_gl_entries(self):
        if self.custom_type_of_transaction == "Asset Purchase":
            self.create_gl_entries_for_asset_purchase()
        elif self.custom_type_of_transaction == "Inventory Purchase Restricted":
            self.create_donor_gl_entries_from_purchase_receipt()
            # self.create_additional_gl_entries_for_purchase_receipt()

    def create_gl_entries_for_asset_purchase(self):
        company = frappe.get_doc("Company", self.company)
        debit_account = company.custom_default_fund
        credit_account = company.custom_default_designated_asset_fund_account

        if not debit_account or not credit_account:
            frappe.throw("Required accounts not found in the company")

        # Create the GL entry for the debit account and update
        debit_entry = self.get_gl_entry_dict()
        debit_entry.update({
            'account': debit_account,
            'debit': self.grand_total,
            'credit': 0,
            'debit_in_account_currency': self.grand_total,
            'credit_in_account_currency': 0
        })
        debit_gl = frappe.get_doc(debit_entry)
        debit_gl.insert()
        debit_gl.submit()

        # Create the GL entry for the credit account and update
        credit_entry = self.get_gl_entry_dict()
        credit_entry.update({
            'account': credit_account,
            'debit': 0,
            'credit': self.grand_total,
            'debit_in_account_currency': 0,
            'credit_in_account_currency': self.grand_total
        })
        credit_gl = frappe.get_doc(credit_entry)
        credit_gl.insert()
        credit_gl.submit()

    def get_gl_entry_dict(self):
        return frappe._dict({
            'doctype': 'GL Entry',
            'posting_date': self.posting_date,
            'transaction_date': self.posting_date,
            'party_type' : "Donor",
            'party' : self.donor,
            'cost_center' : self.cost_center,
            'against': f"Purchase Receipt: {self.name}",
            'against_voucher_type': 'Purchase Receipt',
            'against_voucher' : self.name,
            'voucher_type': 'Purchase Receipt',
            'voucher_subtype': 'Receive',
            'voucher_no': self.name,
            'project': self.project,
            'company': self.company,
        })
    
    def create_donor_gl_entries_from_purchase_receipt(self):
        inventory_account = frappe.db.get_value("Company", {"name": self.company}, "custom_default_inventory_fund_account")
        last_donor_not_fully_used = None
        # frappe.msgprint(frappe.as_json("create_donor_gl_entries_from_purchase_receipt_aq"))

        donor_list_data = self.donor_list_data_from_purchase_receipt()
        donor_list = donor_list_data.get("donor_list", [])

        if not donor_list:
            frappe.msgprint("No donor list found.")
            return

        total_amount = donor_list_data.get("total_amount", 0.0)
        required_total = self.total
        remaining_amount = required_total - total_amount

        if remaining_amount == 0:
            # frappe.msgprint("Donated amount equals the required total amount.")
            for donor_entry in donor_list:
                donor = donor_entry.get('donor')
                cost_center = donor_entry.get('cost_center')
                project = donor_entry.get('project')
                program = donor_entry.get('program')
                subservice_area = donor_entry.get('subservice_area')
                product = donor_entry.get('product')
                amount = donor_entry.get('amount', 0.0)

                gl_entry = frappe.get_doc({
                    'doctype': 'GL Entry',
                    'posting_date': self.posting_date,
                    'transaction_date': self.posting_date,
                    'account': "Capital Stock - AKFP",
                    'against_voucher_type': 'Purchase Receipt',
                    'against_voucher': self.name,
                    'cost_center': cost_center,
                    'debit': amount,
                    'credit': 0.0,
                    'account_currency': 'PKR',
                    'debit_in_account_currency': amount,
                    'credit_in_account_currency': 0.0,
                    'against': "Capital Stock - AKFP",
                    'voucher_type': 'Purchase Receipt',
                    'voucher_no': self.name,
                    'remarks': 'Donation for item',
                    'is_opening': 'No',
                    'is_advance': 'No',
                    'fiscal_year': '2024-2025',
                    'company': self.company,
                    'transaction_currency': 'PKR',
                    'debit_in_transaction_currency': amount,
                    'credit_in_transaction_currency': 0.0,
                    'transaction_exchange_rate': 1,
                    'project': project,
                    'program': program,
                    'party_type': 'Donor',
                    'party': donor,
                    'subservice_area': subservice_area,
                    'donor': donor,
                    'inventory_flag': 'Purchased',
                    'product': product
                })

                gl_entry.insert()
                gl_entry.submit()

                gl_entry_inventory_fund = frappe.get_doc({
                    'doctype': 'GL Entry',
                    'posting_date': self.posting_date,
                    'transaction_date': self.posting_date,
                    'account': inventory_account,  
                    'against_voucher_type': 'Purchase Receipt',
                    'against_voucher': self.name,
                    'cost_center': cost_center,
                    'debit': 0.0,
                    'credit': amount,
                    'account_currency': 'PKR',
                    'debit_in_account_currency': 0.0,
                    'credit_in_account_currency': amount,
                    'against': "Capital Stock - AKFP",
                    'voucher_type': 'Purchase Receipt',
                    'voucher_no': self.name,
                    'remarks': 'Inventory fund for item',
                    'is_opening': 'No',
                    'is_advance': 'No',
                    'fiscal_year': '2024-2025',
                    'company': self.company,
                    'transaction_currency': 'PKR',
                    'debit_in_transaction_currency': 0.0,
                    'credit_in_transaction_currency':amount,
                    'transaction_exchange_rate': 1,
                    'project': project,
                    'program': program,
                    'party_type': 'Donor',
                    'party': donor,
                    'subservice_area': subservice_area,
                    'donor': donor,
                    'inventory_flag': 'Purchased',
                    'product': product
                })
                gl_entry_inventory_fund.insert()
                gl_entry_inventory_fund.submit()

            frappe.msgprint("GL Entries created successfully for equal donated and total amounts.")
            return

        if remaining_amount > 0:
            # frappe.msgprint("if remaining_amount > 0:")
            # Handle case where total_amount is less than required_total
            if len(donor_list) == 1:
                donor_entry = donor_list[0]
                donor = donor_entry.get('donor')
                cost_center = donor_entry.get('cost_center')
                project = donor_entry.get('project')
                program = donor_entry.get('program')
                subservice_area = donor_entry.get('subservice_area')
                product = donor_entry.get('product')
                amount = donor_entry.get('amount', 0.0)

                amount += remaining_amount
                frappe.msgprint(f"Donor {donor} is debited by an additional {remaining_amount} PKR.")

                gl_entry = frappe.get_doc({
                    'doctype': 'GL Entry',
                    'posting_date': self.posting_date,
                    'transaction_date': self.posting_date,
                    'account': "Capital Stock - AKFP",
                    'against_voucher_type': 'Purchase Receipt',
                    'against_voucher': self.name,
                    'cost_center': cost_center,
                    'debit': amount,
                    'credit': 0.0,
                    'account_currency': 'PKR',
                    'debit_in_account_currency': amount,
                    'credit_in_account_currency': 0.0,
                    'against': "Capital Stock - AKFP",
                    'voucher_type': 'Purchase Receipt',
                    'voucher_no': self.name,
                    'remarks': 'Donation for item',
                    'is_opening': 'No',
                    'is_advance': 'No',
                    'fiscal_year': '2024-2025',
                    'company': self.company,
                    'transaction_currency': 'PKR',
                    'debit_in_transaction_currency': amount,
                    'credit_in_transaction_currency': 0.0,
                    'transaction_exchange_rate': 1,
                    'project': project,
                    'program': program,
                    'party_type': 'Donor',
                    'party': donor,
                    'subservice_area': subservice_area,
                    'donor': donor,
                    'inventory_flag': 'Purchased',
                    'product': product
                })

                gl_entry.insert()
                gl_entry.submit()

                gl_entry_inventory_fund = frappe.get_doc({
                    'doctype': 'GL Entry',
                    'posting_date': self.posting_date,
                    'transaction_date': self.posting_date,
                    'account': inventory_account,  
                    'against_voucher_type': 'Purchase Receipt',
                    'against_voucher': self.name,
                    'cost_center': cost_center,
                    'debit': 0.0,
                    'credit': amount,
                    'account_currency': 'PKR',
                    'debit_in_account_currency': 0.0,
                    'credit_in_account_currency': amount,
                    'against': "Capital Stock - AKFP",
                    'voucher_type': 'Purchase Receipt',
                    'voucher_no': self.name,
                    'remarks': 'Inventory fund for item',
                    'is_opening': 'No',
                    'is_advance': 'No',
                    'fiscal_year': '2024-2025',
                    'company': self.company,
                    'transaction_currency': 'PKR',
                    'debit_in_transaction_currency': 0.0,
                    'credit_in_transaction_currency':amount,
                    'transaction_exchange_rate': 1,
                    'project': project,
                    'program': program,
                    'party_type': 'Donor',
                    'party': donor,
                    'subservice_area': subservice_area,
                    'donor': donor,
                    'inventory_flag': 'Purchased',
                    'product': product
                })
                gl_entry_inventory_fund.insert()
                gl_entry_inventory_fund.submit()

            else:
                # frappe.msgprint("Elseeee if remaining_amount > 0:")
                for i, donor_entry in enumerate(donor_list):
                    donor = donor_entry.get('donor')
                    cost_center = donor_entry.get('cost_center')
                    project = donor_entry.get('project')
                    program = donor_entry.get('program')
                    subservice_area = donor_entry.get('subservice_area')
                    amount = donor_entry.get('amount', 0.0)
                    product = donor_entry.get('product')

                    if i == len(donor_list) - 1:
                        amount += remaining_amount
                        frappe.msgprint(f"Donor {donor} is debited by an additional {remaining_amount} PKR.")
                    elif len(donor_list) == 1:
                        amount
                        frappe.msgprint(f"Donor {donor} is debited by an additional {remaining_amount} PKR.")

                    gl_entry = frappe.get_doc({
                        'doctype': 'GL Entry',
                        'posting_date': self.posting_date,
                        'transaction_date': self.posting_date,
                        'account': "Capital Stock - AKFP",
                        'against_voucher_type': 'Purchase Receipt',
                        'against_voucher': self.name,
                        'cost_center': cost_center,
                        'debit': amount,
                        'credit': 0.0,
                        'account_currency': 'PKR',
                        'debit_in_account_currency': amount,
                        'credit_in_account_currency': 0.0,
                        'against': "Capital Stock - AKFP",
                        'voucher_type': 'Purchase Receipt',
                        'voucher_no': self.name,
                        'remarks': 'Donation for item',
                        'is_opening': 'No',
                        'is_advance': 'No',
                        'fiscal_year': '2024-2025',
                        'company': self.company,
                        'transaction_currency': 'PKR',
                        'debit_in_transaction_currency': amount,
                        'credit_in_transaction_currency': 0.0,
                        'transaction_exchange_rate': 1,
                        'project': project,
                        'program': program,
                        'party_type': 'Donor',
                        'party': donor,
                        'subservice_area': subservice_area,
                        'donor': donor,
                        'inventory_flag': 'Purchased',
                        'product': product
                    })

                    gl_entry.insert()
                    gl_entry.submit()

                    gl_entry_inventory_fund = frappe.get_doc({
                    'doctype': 'GL Entry',
                    'posting_date': self.posting_date,
                    'transaction_date': self.posting_date,
                    'account': inventory_account,  
                    'against_voucher_type': 'Purchase Receipt',
                    'against_voucher': self.name,
                    'cost_center': cost_center,
                    'debit': 0.0,
                    'credit': amount,
                    'account_currency': 'PKR',
                    'debit_in_account_currency': 0.0,
                    'credit_in_account_currency': amount,
                    'against': "Capital Stock - AKFP",
                    'voucher_type': 'Purchase Receipt',
                    'voucher_no': self.name,
                    'remarks': 'Inventory fund for item',
                    'is_opening': 'No',
                    'is_advance': 'No',
                    'fiscal_year': '2024-2025',
                    'company': self.company,
                    'transaction_currency': 'PKR',
                    'debit_in_transaction_currency': 0.0,
                    'credit_in_transaction_currency':amount,
                    'transaction_exchange_rate': 1,
                    'project': project,
                    'program': program,
                    'party_type': 'Donor',
                    'party': donor,
                    'subservice_area': subservice_area,
                    'donor': donor,
                    'inventory_flag': 'Purchased',
                    'product': product
                })
                    gl_entry_inventory_fund.insert()
                    gl_entry_inventory_fund.submit()

        elif remaining_amount < 0:
            # frappe.msgprint("remaining_amount < 0")
            # frappe.msgprint(frappe.as_json("required_amount"))
            required_amount_for_item = required_total
            last_donor_not_fully_used = None 
            for donor_entry in donor_list:
                donor = donor_entry.get('donor')
                cost_center = donor_entry.get('cost_center')
                project = donor_entry.get('project')
                program = donor_entry.get('program')
                subservice_area = donor_entry.get('subservice_area')
                total_debit = donor_entry.get('total_debit', 0.0)
                product = donor_entry.get('product')
                amount = donor_entry.get('amount', 0.0)
                # frappe.msgprint("amount_from_donor_list")
                # frappe.msgprint(frappe.as_json(amount))

                if required_amount_for_item > 0:
                    amount_to_use = min(amount, required_amount_for_item)
                    # frappe.msgprint("amount_to_use")
                    # frappe.msgprint(frappe.as_json(amount_to_use))

                    # Create and insert GL Entry for donation
                    gl_entry_donation = frappe.get_doc({
                        'doctype': 'GL Entry',
                        'posting_date': self.posting_date,
                        'transaction_date': self.posting_date,
                        'account': "Capital Stock - AKFP",
                        'against_voucher_type': 'Purchase Receipt',
                        'against_voucher': self.name,
                        'cost_center': cost_center,
                        'debit': amount_to_use,
                        'credit': 0.0,
                        'account_currency': 'PKR',
                        'debit_in_account_currency': amount_to_use,
                        'credit_in_account_currency': 0.0,
                        'against': "Capital Stock - AKFP",
                        'voucher_type': 'Purchase Receipt',
                        'voucher_no': self.name,
                        'remarks': 'Donation for item',
                        'is_opening': 'No',
                        'is_advance': 'No',
                        'fiscal_year': '2024-2025',
                        'company': self.company,
                        'transaction_currency': 'PKR',
                        'debit_in_transaction_currency': amount_to_use,
                        'credit_in_transaction_currency': 0.0,
                        'transaction_exchange_rate': 1,
                        'project': project,
                        'program': program,
                        'party_type': 'Donor',
                        'party': donor,
                        'subservice_area': subservice_area,
                        'donor': donor,
                        'inventory_flag': 'Purchased',
                        'product': product
                    })
                    gl_entry_donation.insert()
                    gl_entry_donation.submit()

                    gl_entry_inventory_fund = frappe.get_doc({
                        'doctype': 'GL Entry',
                        'posting_date': self.posting_date,
                        'transaction_date': self.posting_date,
                        'account': inventory_account,  
                        'against_voucher_type': 'Purchase Receipt',
                        'against_voucher': self.name,
                        'cost_center': cost_center,
                        'debit': 0.0,
                        'credit': amount_to_use,
                        'account_currency': 'PKR',
                        'debit_in_account_currency': 0.0,
                        'credit_in_account_currency': amount_to_use,
                        'against': "Capital Stock - AKFP",
                        'voucher_type': 'Purchase Receipt',
                        'voucher_no': self.name,
                        'remarks': 'Inventory fund for item',
                        'is_opening': 'No',
                        'is_advance': 'No',
                        'fiscal_year': '2024-2025',
                        'company': self.company,
                        'transaction_currency': 'PKR',
                        'debit_in_transaction_currency': 0.0,
                        'credit_in_transaction_currency':amount_to_use,
                        'transaction_exchange_rate': 1,
                        'project': project,
                        'program': program,
                        'party_type': 'Donor',
                        'party': donor,
                        'subservice_area': subservice_area,
                        'donor': donor,
                        'inventory_flag': 'Purchased',
                        'product': product
                    })
                    gl_entry_inventory_fund.insert()
                    gl_entry_inventory_fund.submit()

                    required_amount_for_item -= amount_to_use

                if required_amount_for_item == 0:
                    last_donor_not_fully_used = donor
                    break  

            if last_donor_not_fully_used:
                frappe.msgprint(f"The last donor whose full amount has not been used is {last_donor_not_fully_used}.")

            frappe.msgprint("GL Entries created successfully.")
    
    def donor_list_data_from_purchase_receipt(self):
        donor_list = []
        total_amount = 0
        unique_entries = set()
        condition = ""

        for p in self.custom_program_details:
            condition = f"and subservice_area = '{p.pd_subservice_area}'" if p.pd_subservice_area else ""
            condition += f"and donor = '{p.pd_donor}'" if p.pd_donor else ""
            condition += f"and project = '{p.pd_project}'" if p.pd_project else ""
            condition += f"and cost_center = '{p.pd_cost_center}'" if p.pd_cost_center else ""
            condition += f"and product = '{p.pd_product}'" if p.pd_product else ""
            condition += f"and program = '{p.pd_service_area}'" if p.pd_service_area else ""

            total_debit = frappe.db.sql(f"""
                SELECT SUM(credit - debit) as total_debit,
                    donor,
                    program,
                    subservice_area,
                    project,
                    cost_center,
                    product
                FROM `tabGL Entry`
                WHERE 
                    account = 'Capital Stock - AKFP'
                    {condition}
                GROUP BY donor, program, subservice_area, project, cost_center, product
                ORDER BY total_debit DESC
            """, as_dict=True)

            for entry in total_debit:
                entry_key = (
                    entry.get('subservice_area'),
                    entry.get('donor'),
                    entry.get('project'),
                    entry.get('cost_center'),
                    entry.get('product'),
                    entry.get('program')
                )

                if entry_key not in unique_entries:
                    unique_entries.add(entry_key)
                    amount = entry['total_debit']
                    if amount > 0:
                        db_dict = {
                            'subservice_area': p.pd_subservice_area,
                            'donor': p.pd_donor,
                            'project': p.pd_project,
                            'cost_center': p.pd_cost_center,
                            'product': p.pd_product,
                            'amount': amount,
                            'program': p.pd_service_area
                        }
                        donor_list.append(db_dict)
                        total_amount += amount

        return {
            "total_amount": total_amount,
            "donor_list": donor_list  
        }

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

    processed_entries = set()

    for p in doc.custom_program_details:
        entry_key = (
            p.pd_donor,
            p.pd_service_area,
            p.pd_subservice_area,
            p.pd_project,
            p.pd_cost_center,
            p.pd_product,
        )

        if entry_key in processed_entries:
            frappe.msgprint(f"Duplicate Entry detected for donor '<bold>{p.pd_donor}</bold>' with provided details.")
            continue

        processed_entries.add(entry_key)

        condition_parts = [
            f"(subservice_area = '{p.pd_subservice_area}' OR (subservice_area IS NULL AND '{p.pd_subservice_area}' = '') OR subservice_area = '')" if p.pd_subservice_area else "1=1",
            f"(donor = '{p.pd_donor}' OR (donor IS NULL AND '{p.pd_donor}' = '') OR donor = '')" if p.pd_donor else "1=1",
            f"(project = '{p.pd_project}' OR (project IS NULL AND '{p.pd_project}' = '') OR project = '')" if p.pd_project else "1=1",
            f"(cost_center = '{p.pd_cost_center}' OR (cost_center IS NULL AND '{p.pd_cost_center}' = '') OR cost_center = '')" if p.pd_cost_center else "1=1",
            f"(product = '{p.pd_product}' OR (product IS NULL AND '{p.pd_product}' = '') OR product = '')" if p.pd_product else "1=1",
            f"(program = '{p.pd_service_area}' OR (program IS NULL AND '{p.pd_service_area}' = '') OR program = '')" if p.pd_service_area else "1=1"
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
                       product
                FROM `tabGL Entry`
                WHERE 
                    account = 'Capital Stock - AKFP'
                    {f'AND {condition}' if condition else ''}
                GROUP BY donor, program, subservice_area, project, cost_center, product
                HAVING total_balance >= -1000000
                ORDER BY total_balance DESC
            """, as_dict=True)
        except Exception as e:
            frappe.throw(f"Error executing query: {e}")

        match_found = False

        for entry in donor_entries:
            if ((entry.get('program') == p.pd_service_area or (not entry.get('program') and not p.pd_service_area)) and
                (entry.get('subservice_area') == p.pd_subservice_area or (not entry.get('subservice_area') and not p.pd_subservice_area)) and
                (entry.get('project') == p.pd_project or (not entry.get('project') and not p.pd_project)) and
                (entry.get('cost_center') == p.pd_cost_center or (not entry.get('cost_center') and not p.pd_cost_center)) and
                (entry.get('product') == p.pd_product or (not entry.get('product') and not p.pd_product))):

                entry_key = (
                    entry.get('donor'), 
                    entry.get('program'), 
                    entry.get('subservice_area'), 
                    entry.get('project'),
                    entry.get('cost_center'),
                    entry.get('product'),
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
                                    AND voucher_no = '{doc.name}'
                                    {f'AND {condition}' if condition else ''}
                            """, as_dict=True)
                            if used_amount_data:
                                used_amount = used_amount_data[0].get('used_amount', 0)
                        except Exception as e:
                            frappe.throw(f"Error fetching used amount: {e}")

                    donor_list.append({
                        "donor": p.pd_donor,
                        "service_area": p.pd_service_area,
                        "subservice_area": p.pd_subservice_area,
                        "project": p.pd_project,
                        "cost_center": p.pd_cost_center,
                        "product": p.pd_product,
                        "balance": balance,
                        "used_amount": used_amount,
                    })

                    total_balance += balance
                    match_found = True
                    break

        if not match_found:
            frappe.msgprint(f"No such entry exists for donor '<bold>{p.pd_donor}</bold>' with provided details.")

    return {
        "total_balance": total_balance,
        "donor_list": donor_list  
    }


# @frappe.whitelist()
# def donor_list_data(doc):
#     try:
#         doc = frappe.get_doc(json.loads(doc))
#     except (json.JSONDecodeError, TypeError) as e:
#         frappe.throw(f"Invalid input: {e}")

#     donor_list = []
#     total_balance = 0
#     unique_entries = set()
#     docstatus = doc.docstatus

#     for p in doc.custom_program_details:
#         condition_parts = [
#             f"(subservice_area = '{p.pd_subservice_area}' OR (subservice_area IS NULL AND '{p.pd_subservice_area}' = '') OR subservice_area = '')" if p.pd_subservice_area else "1=1",
#             f"(donor = '{p.pd_donor}' OR (donor IS NULL AND '{p.pd_donor}' = '') OR donor = '')" if p.pd_donor else "1=1",
#             f"(project = '{p.pd_project}' OR (project IS NULL AND '{p.pd_project}' = '') OR project = '')" if p.pd_project else "1=1",
#             f"(cost_center = '{p.pd_cost_center}' OR (cost_center IS NULL AND '{p.pd_cost_center}' = '') OR cost_center = '')" if p.pd_cost_center else "1=1",
#             f"(product = '{p.pd_product}' OR (product IS NULL AND '{p.pd_product}' = '') OR product = '')" if p.pd_product else "1=1",
#             f"(program = '{p.pd_service_area}' OR (program IS NULL AND '{p.pd_service_area}' = '') OR program = '')" if p.pd_service_area else "1=1"
#         ]
#         condition = " AND ".join(condition_parts)
#         try:
#             donor_entries = frappe.db.sql(f"""
#                 SELECT SUM(credit - debit) as total_balance,
#                        donor,
#                        program,
#                        subservice_area,
#                        project,
#                        cost_center,
#                        product
#                 FROM `tabGL Entry`
#                 WHERE 
#                     account = 'Capital Stock - AKFP'
#                     {f'AND {condition}' if condition else ''}
#                 GROUP BY donor, program, subservice_area, project, cost_center, product
#                 HAVING total_balance >= -1000000
#                 ORDER BY total_balance DESC
#             """, as_dict=True)
#         except Exception as e:
#             frappe.throw(f"Error executing query: {e}")

#         match_found = False

#         for entry in donor_entries:
#             if ((entry.get('program') == p.pd_service_area or (not entry.get('program') and not p.pd_service_area)) and
#                 (entry.get('subservice_area') == p.pd_subservice_area or (not entry.get('subservice_area') and not p.pd_subservice_area)) and
#                 (entry.get('project') == p.pd_project or (not entry.get('project') and not p.pd_project)) and
#                 (entry.get('cost_center') == p.pd_cost_center or (not entry.get('cost_center') and not p.pd_cost_center)) and
#                 (entry.get('product') == p.pd_product or (not entry.get('product') and not p.pd_product))):

#                 entry_key = (
#                     entry.get('donor'), 
#                     entry.get('program'), 
#                     entry.get('subservice_area'), 
#                     entry.get('project'),
#                     entry.get('cost_center'),
#                     entry.get('product'),
#                 )

#                 if entry_key not in unique_entries:
#                     unique_entries.add(entry_key)
#                     balance = entry['total_balance']
#                     used_amount = 0

#                     if docstatus == 1:
#                         try:
#                             used_amount_data = frappe.db.sql(f"""
#                                 SELECT SUM(debit) as used_amount
#                                 FROM `tabGL Entry`
#                                 WHERE 
#                                     account = 'Capital Stock - AKFP'
#                                     AND voucher_no = '{doc.name}'
#                                     {f'AND {condition}' if condition else ''}
#                             """, as_dict=True)
#                             if used_amount_data:
#                                 used_amount = used_amount_data[0].get('used_amount', 0)
#                         except Exception as e:
#                             frappe.throw(f"Error fetching used amount: {e}")

#                     donor_list.append({
#                         "donor": p.pd_donor,
#                         "service_area": p.pd_service_area,
#                         "subservice_area": p.pd_subservice_area,
#                         "project": p.pd_project,
#                         "cost_center": p.pd_cost_center,
#                         "product": p.pd_product,
#                         "balance": balance,
#                         "used_amount": used_amount,
#                     })

#                     total_balance += balance
#                     match_found = True
#                     break

#         if not match_found:
#             frappe.msgprint(f'No such entry exists for donor "<bold>{p.pd_donor}</bold>" with provided details.')

#     return {
#         "total_balance": total_balance,
#         "donor_list": donor_list  
#     }
