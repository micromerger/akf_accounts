#Dev Aqsa Abbasi 
#Currently Used Purchase Receipt in hooks

import frappe
import json
from erpnext.accounts.utils import get_fiscal_year
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import PurchaseReceipt

class XAssetInvenPurchase(PurchaseReceipt):
    def validate(self):
       
        super().validate()
        # frappe.msgprint('accounts')
    def on_submit(self):
        super().on_submit()
        self.make_gl_entries()
        self.update_stock_ledger_entry()
        messages = self.empty_message()
        # frappe.throw(f"{messages}")
        if messages:
            message_str = "\n".join(messages)
            frappe.throw(f"Please adjust /entries: {message_str}" )

        if self.custom_type_of_transaction in ("Asset Purchase Restricted", "Inventory Purchase Restricted" ):
            self.create_donor_gl_entries_from_purchase_receipt()
        elif self.custom_type_of_transaction == "Normal":
            # frappe.msgrpint("This one is normal")
            pass
        # self.create_asset_inven_purchase_gl_entries()
 
    def on_cancel(self):
        super().on_cancel()
        self.delete_all_gl_entries()
    
        
    def delete_all_gl_entries(self):
        frappe.db.sql("DELETE FROM `tabGL Entry` WHERE voucher_no = %s", self.name)
    def make_gl_entries(self):
        pass

    def create_donor_gl_entries_from_purchase_receipt(self):

         # Get the current fiscal year based on the posting date
        fiscal_year = get_fiscal_year(self.posting_date, company=self.company)[0]
        core_debit = frappe.db.get_value("Company", {"name": self.company}, "custom_default_inventory_asset_account")
        core_credit = frappe.db.get_value("Company", {"name": self.company}, "custom_stock_received_not_billed")
        donation_account = frappe.db.get_value("Company", {"name": self.company}, "custom_donation_account") 
        if self.custom_type_of_transaction == "Inventory Purchase Restricted":
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
                for donor_entry in donor_list:
                    donor = donor_entry.get('donor')
                    cost_center = donor_entry.get('cost_center')
                    project = donor_entry.get('project')
                    program = donor_entry.get('program')
                    subservice_area = donor_entry.get('subservice_area')
                    product = donor_entry.get('product')
                    amount = donor_entry.get('amount', 0.0)



                    gl_entry_core_debit = frappe.get_doc({
                            'doctype': 'GL Entry',
                            'posting_date': self.posting_date,
                            'transaction_date': self.posting_date,
                            'account': core_debit,
                            'against_voucher_type': 'Purchase Receipt',
                            'against_voucher': self.name,
                            'cost_center': cost_center,
                            'debit': amount_to_use,
                            'credit': 0.0,
                            'account_currency': 'PKR',
                            'debit_in_account_currency': amount_to_use,
                            'credit_in_account_currency': 0.0,
                            'against':core_debit,
                            'voucher_type': 'Purchase Receipt',
                            'voucher_no': self.name,
                            'remarks': 'Donation for item',
                            'is_opening': 'No',
                            'is_advance': 'No',
                            'fiscal_year': fiscal_year,
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
                    gl_entry_core_debit.insert(ignore_permissions=True)
                    gl_entry_core_debit.submit()


                    gl_entry_core_credit = frappe.get_doc({
                            'doctype': 'GL Entry',
                            'posting_date': self.posting_date,
                            'transaction_date': self.posting_date,
                            'account': core_credit,  
                            'against_voucher_type': 'Purchase Receipt',
                            'against_voucher': self.name,
                            'cost_center': cost_center,
                            'debit': 0.0,
                            'credit': amount_to_use,
                            'account_currency': 'PKR',
                            'debit_in_account_currency': 0.0,
                            'credit_in_account_currency': amount_to_use,
                            'against': core_credit,
                            'voucher_type': 'Purchase Receipt',
                            'voucher_no': self.name,
                            'remarks': 'Inventory fund for item',
                            'is_opening': 'No',
                            'is_advance': 'No',
                            'fiscal_year': fiscal_year,
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
                    gl_entry_core_credit.insert(ignore_permissions=True)
                    gl_entry_core_credit.submit()

                    gl_entry = frappe.get_doc({
                        'doctype': 'GL Entry',
                        'posting_date': self.posting_date,
                        'transaction_date': self.posting_date,
                        'account': donation_account,
                        'against_voucher_type': 'Purchase Receipt',
                        'against_voucher': self.name,
                        'cost_center': cost_center,
                        'debit': amount,
                        'credit': 0.0,
                        'account_currency': 'PKR',
                        'debit_in_account_currency': amount,
                        'credit_in_account_currency': 0.0,
                        'against': donation_account,
                        'voucher_type': 'Purchase Receipt',
                        'voucher_no': self.name,
                        'remarks': 'Donation for item',
                        'is_opening': 'No',
                        'is_advance': 'No',
                        'fiscal_year': fiscal_year,
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

                    gl_entry.insert(ignore_permissions=True)
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
                        'against': donation_account,
                        'voucher_type': 'Purchase Receipt',
                        'voucher_no': self.name,
                        'remarks': 'Inventory fund for item',
                        'is_opening': 'No',
                        'is_advance': 'No',
                        'fiscal_year': fiscal_year,
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
                    gl_entry_inventory_fund.insert(ignore_permissions=True)
                    gl_entry_inventory_fund.submit()

                frappe.msgprint("GL Entries created successfully")
                return

            if remaining_amount > 0:
                frappe.throw("Insufficient Balance: The donated amount is less than the required amount.")

            
            elif remaining_amount < 0:
                # frappe.msgprint("remaining_amount < 0")
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

                    if required_amount_for_item > 0:
                        amount_to_use = min(amount, required_amount_for_item)

                       #core entries are sub-divded
                        gl_entry_core_debit = frappe.get_doc({
                            'doctype': 'GL Entry',
                            'posting_date': self.posting_date,
                            'transaction_date': self.posting_date,
                            'account': core_debit,
                            'against_voucher_type': 'Purchase Receipt',
                            'against_voucher': self.name,
                            'cost_center': cost_center,
                            'debit': amount_to_use,
                            'credit': 0.0,
                            'account_currency': 'PKR',
                            'debit_in_account_currency': amount_to_use,
                            'credit_in_account_currency': 0.0,
                            'against':core_debit,
                            'voucher_type': 'Purchase Receipt',
                            'voucher_no': self.name,
                            'remarks': 'Donation for item',
                            'is_opening': 'No',
                            'is_advance': 'No',
                            'fiscal_year': fiscal_year,
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
                        gl_entry_core_debit.insert(ignore_permissions=True)
                        gl_entry_core_debit.submit()


                        gl_entry_core_credit = frappe.get_doc({
                            'doctype': 'GL Entry',
                            'posting_date': self.posting_date,
                            'transaction_date': self.posting_date,
                            'account': core_credit,  
                            'against_voucher_type': 'Purchase Receipt',
                            'against_voucher': self.name,
                            'cost_center': cost_center,
                            'debit': 0.0,
                            'credit': amount_to_use,
                            'account_currency': 'PKR',
                            'debit_in_account_currency': 0.0,
                            'credit_in_account_currency': amount_to_use,
                            'against': core_credit,
                            'voucher_type': 'Purchase Receipt',
                            'voucher_no': self.name,
                            'remarks': 'Inventory fund for item',
                            'is_opening': 'No',
                            'is_advance': 'No',
                            'fiscal_year': fiscal_year,
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
                        gl_entry_core_credit.insert(ignore_permissions=True)
                        gl_entry_core_credit.submit()

                        gl_entry_donation = frappe.get_doc({
                            'doctype': 'GL Entry',
                            'posting_date': self.posting_date,
                            'transaction_date': self.posting_date,
                            'account': donation_account,
                            'against_voucher_type': 'Purchase Receipt',
                            'against_voucher': self.name,
                            'cost_center': cost_center,
                            'debit': amount_to_use,
                            'credit': 0.0,
                            'account_currency': 'PKR',
                            'debit_in_account_currency': amount_to_use,
                            'credit_in_account_currency': 0.0,
                            'against': donation_account,
                            'voucher_type': 'Purchase Receipt',
                            'voucher_no': self.name,
                            'remarks': 'Donation for item',
                            'is_opening': 'No',
                            'is_advance': 'No',
                            'fiscal_year': fiscal_year,
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
                        gl_entry_donation.insert(ignore_permissions=True)
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
                            'against': inventory_account,
                            'voucher_type': 'Purchase Receipt',
                            'voucher_no': self.name,
                            'remarks': 'Inventory fund for item',
                            'is_opening': 'No',
                            'is_advance': 'No',
                            'fiscal_year': fiscal_year,
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
                        gl_entry_inventory_fund.insert(ignore_permissions=True)
                        gl_entry_inventory_fund.submit()

                        required_amount_for_item -= amount_to_use

                    if required_amount_for_item == 0:
                        last_donor_not_fully_used = donor
                        break  

                if last_donor_not_fully_used:
                    frappe.msgprint(f"Donor whose full amount has not been used is {last_donor_not_fully_used}.")

                frappe.msgprint("GL Entries created successfully.")
        elif self.custom_type_of_transaction == "Asset Purchase Restricted":
            asset_debit_account = frappe.db.get_value("Company", {"name": self.company}, "custom_default_fund")
            asset_credit_account = frappe.db.get_value("Company", {"name": self.company}, "custom_default_designated_asset_fund_account")
           
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
                frappe.msgprint(frappe.as_json("Asset remaining_amount == 0:"))
                for donor_entry in donor_list:
                    donor = donor_entry.get('donor')
                    cost_center = donor_entry.get('cost_center')
                    project = donor_entry.get('project')
                    program = donor_entry.get('program')
                    subservice_area = donor_entry.get('subservice_area')
                    product = donor_entry.get('product')
                    amount = donor_entry.get('amount', 0.0)


                    gl_entry_core_debit = frappe.get_doc({
                        'doctype': 'GL Entry',
                        'posting_date': self.posting_date,
                        'transaction_date': self.posting_date,
                        'account': core_debit,
                        'against_voucher_type': 'Purchase Receipt',
                        'against_voucher': self.name,
                        'cost_center': cost_center,
                        'debit': amount,
                        'credit': 0.0,
                        'account_currency': 'PKR',
                        'debit_in_account_currency': amount,
                        'credit_in_account_currency': 0.0,
                        'against':core_debit,
                        'voucher_type': 'Purchase Receipt',
                        'voucher_no': self.name,
                        'remarks': 'Donation for item',
                        'is_opening': 'No',
                        'is_advance': 'No',
                        'fiscal_year': fiscal_year,
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

                    gl_entry_core_debit.insert(ignore_permissions=True)
                    gl_entry_core_debit.submit()

                    gl_entry_core_credit = frappe.get_doc({
                        'doctype': 'GL Entry',
                        'posting_date': self.posting_date,
                        'transaction_date': self.posting_date,
                        'account': core_credit,  
                        'against_voucher_type': 'Purchase Receipt',
                        'against_voucher': self.name,
                        'cost_center': cost_center,
                        'debit': 0.0,
                        'credit': amount,
                        'account_currency': 'PKR',
                        'debit_in_account_currency': 0.0,
                        'credit_in_account_currency': amount,
                        'against': core_credit,
                        'voucher_type': 'Purchase Receipt',
                        'voucher_no': self.name,
                        'remarks': 'Inventory fund for item',
                        'is_opening': 'No',
                        'is_advance': 'No',
                        'fiscal_year': fiscal_year,
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
                    gl_entry_core_credit.insert(ignore_permissions=True)
                    gl_entry_core_credit.submit()

                    gl_entry = frappe.get_doc({
                        'doctype': 'GL Entry',
                        'posting_date': self.posting_date,
                        'transaction_date': self.posting_date,
                        'account': donation_account,
                        'against_voucher_type': 'Purchase Receipt',
                        'against_voucher': self.name,
                        'cost_center': cost_center,
                        'debit': amount,
                        'credit': 0.0,
                        'account_currency': 'PKR',
                        'debit_in_account_currency': amount,
                        'credit_in_account_currency': 0.0,
                        'against': donation_account,
                        'voucher_type': 'Purchase Receipt',
                        'voucher_no': self.name,
                        'remarks': 'Donation for item',
                        'is_opening': 'No',
                        'is_advance': 'No',
                        'fiscal_year': fiscal_year,
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

                    gl_entry.insert(ignore_permissions=True)
                    gl_entry.submit()

                    gl_entry_inventory_fund = frappe.get_doc({
                        'doctype': 'GL Entry',
                        'posting_date': self.posting_date,
                        'transaction_date': self.posting_date,
                        'account': asset_credit_account,  
                        'against_voucher_type': 'Purchase Receipt',
                        'against_voucher': self.name,
                        'cost_center': cost_center,
                        'debit': 0.0,
                        'credit': amount,
                        'account_currency': 'PKR',
                        'debit_in_account_currency': 0.0,
                        'credit_in_account_currency': amount,
                        'against': asset_credit_account,
                        'voucher_type': 'Purchase Receipt',
                        'voucher_no': self.name,
                        'remarks': 'Inventory fund for item',
                        'is_opening': 'No',
                        'is_advance': 'No',
                        'fiscal_year': fiscal_year,
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
                    gl_entry_inventory_fund.insert(ignore_permissions=True)
                    gl_entry_inventory_fund.submit()

                frappe.msgprint("GL Entries created successfully")
                return

            if remaining_amount > 0:
                frappe.throw("Insufficient Balance: The donated amount is less than the required amount.")

            
            elif remaining_amount < 0:
                # frappe.msgprint(frappe.as_json("Asset remaining_amount < 0:"))
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

                    if required_amount_for_item > 0:
                        amount_to_use = min(amount, required_amount_for_item)

                       

                        # Create Core Debit Entry
                        gl_entry_core_debit = frappe.get_doc({
                            'doctype': 'GL Entry',
                            'posting_date': self.posting_date,
                            'transaction_date': self.posting_date,
                            'account': core_debit,
                            'against_voucher_type': 'Purchase Receipt',
                            'against_voucher': self.name,
                            'cost_center': cost_center,
                            'debit': amount_to_use,
                            'credit': 0.0,
                            'account_currency': 'PKR',
                            'debit_in_account_currency': amount_to_use,
                            'credit_in_account_currency': 0.0,
                            'against': core_debit,
                            'voucher_type': 'Purchase Receipt',
                            'voucher_no': self.name,
                            'remarks': 'Donation for item',
                            'is_opening': 'No',
                            'is_advance': 'No',
                            'fiscal_year': fiscal_year,
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
                        gl_entry_core_debit.insert(ignore_permissions=True)
                        gl_entry_core_debit.submit()

                        # Create Core Credit Entry
                        gl_entry_core_credit = frappe.get_doc({
                            'doctype': 'GL Entry',
                            'posting_date': self.posting_date,
                            'transaction_date': self.posting_date,
                            'account': core_credit,
                            'against_voucher_type': 'Purchase Receipt',
                            'against_voucher': self.name,
                            'cost_center': cost_center,
                            'debit': 0.0,
                            'credit': amount_to_use,
                            'account_currency': 'PKR',
                            'debit_in_account_currency': 0.0,
                            'credit_in_account_currency': amount_to_use,
                            'against': core_credit,
                            'voucher_type': 'Purchase Receipt',
                            'voucher_no': self.name,
                            'remarks': 'Inventory fund for item',
                            'is_opening': 'No',
                            'is_advance': 'No',
                            'fiscal_year': fiscal_year,
                            'company': self.company,
                            'transaction_currency': 'PKR',
                            'debit_in_transaction_currency': 0.0,
                            'credit_in_transaction_currency': amount_to_use,
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
                        gl_entry_core_credit.insert(ignore_permissions=True)
                        gl_entry_core_credit.submit()


                         # Create GL Entry for Donation
                        gl_entry_donation = frappe.get_doc({
                            'doctype': 'GL Entry',
                            'posting_date': self.posting_date,
                            'transaction_date': self.posting_date,
                            'account': donation_account,
                            'against_voucher_type': 'Purchase Receipt',
                            'against_voucher': self.name,
                            'cost_center': cost_center,
                            'debit': amount_to_use,
                            'credit': 0.0,
                            'account_currency': 'PKR',
                            'debit_in_account_currency': amount_to_use,
                            'credit_in_account_currency': 0.0,
                            'against': asset_credit_account,
                            'voucher_type': 'Purchase Receipt',
                            'voucher_no': self.name,
                            'remarks': 'Donation for item',
                            'is_opening': 'No',
                            'is_advance': 'No',
                            'fiscal_year': fiscal_year,
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
                        gl_entry_donation.insert(ignore_permissions=True)
                        gl_entry_donation.submit()

                        # Create Inventory Fund Entry
                        gl_entry_inventory_fund = frappe.get_doc({
                            'doctype': 'GL Entry',
                            'posting_date': self.posting_date,
                            'transaction_date': self.posting_date,
                            'account': asset_credit_account,
                            'against_voucher_type': 'Purchase Receipt',
                            'against_voucher': self.name,
                            'cost_center': cost_center,
                            'debit': 0.0,
                            'credit': amount_to_use,
                            'account_currency': 'PKR',
                            'debit_in_account_currency': 0.0,
                            'credit_in_account_currency': amount_to_use,
                            'against': asset_credit_account,
                            'voucher_type': 'Purchase Receipt',
                            'voucher_no': self.name,
                            'remarks': 'Inventory fund for item',
                            'is_opening': 'No',
                            'is_advance': 'No',
                            'fiscal_year': fiscal_year,
                            'company': self.company,
                            'transaction_currency': 'PKR',
                            'debit_in_transaction_currency': 0.0,
                            'credit_in_transaction_currency': amount_to_use,
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
                        gl_entry_inventory_fund.insert(ignore_permissions=True)
                        gl_entry_inventory_fund.submit()

                        required_amount_for_item -= amount_to_use

                    if required_amount_for_item == 0:
                        last_donor_not_fully_used = donor
                        break  

                if last_donor_not_fully_used:
                    frappe.msgprint(f"Donor whose full amount has not been used is {last_donor_not_fully_used}.")

                frappe.msgprint("GL Entries created successfully.")
                

    def update_stock_ledger_entry(self):
        # frappe.msgprint(frappe.as_json("update_stock_ledger_entry working!"))
        final_list = []
        all_donor_id = []

        for row in self.items:
            if hasattr(row, "custom_new") or hasattr(row, "custom_used"):
                if frappe.db.exists(
                    "Stock Ledger Entry",
                    {
                        "docstatus": 1,
                        "voucher_no": self.name,
                    },
                ):
                    frappe.db.sql(
                        f""" 
                            UPDATE `tabStock Ledger Entry`
                            SET custom_new = {row.custom_new}, custom_used = {row.custom_used}
                            WHERE docstatus = 1 
                            AND voucher_detail_no = '{row.name}'
                            AND voucher_no = '{self.name}'
                        """
                    )

        donor_list_data = self.donor_list_data_from_purchase_receipt()
        donor_list = donor_list_data.get("donor_list", [])

        for d in donor_list:
            all_donor_id.append(d.get('donor'))
            # frappe.msgprint(f"Current donors list: {frappe.as_json(all_donor_id)}")

        # Initialize variables with default values
        cost_center = ''
        program = ''
        subservice_area = ''
        product = ''
        project = ''

        if donor_list:
            first_donor = donor_list[0]
            cost_center = first_donor.get('cost_center', '')
            program = first_donor.get('program', '')
            subservice_area = first_donor.get('subservice_area', '')
            product = first_donor.get('product', '')
            project = first_donor.get('project', '')

            final_output = {
                "donors": ", ".join(all_donor_id),
                "cost_center": cost_center,
                "product": product,
                "program": program,
                "project": project,
                "subservice_area": subservice_area,
            }
            # frappe.msgprint(frappe.as_json("final_output"))
            # frappe.msgprint(frappe.as_json(final_output))

            final_list.append(final_output)
            # frappe.msgprint(f"Final output list: {frappe.as_json(final_list)}")

        if frappe.db.exists(
            "Stock Ledger Entry",
            {
                "docstatus": 1,
                "voucher_no": self.name,
            },
        ):
            all_donor_id_json = json.dumps(all_donor_id)
            frappe.db.sql(
                f""" 
                    UPDATE 
                        `tabStock Ledger Entry`
                    SET 
                        custom_donor_list = '{all_donor_id_json}',
                        program = '{program}',
                        subservice_area = '{subservice_area}',
                        product = '{product}',
                        project = '{project}',
                        custom_cost_center = '{cost_center}',
                        inventory_flag = "Purchased"
                    WHERE 
                        docstatus = 1 
                        AND voucher_no = '{self.name}'
                """
            )

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
    

   
    def empty_message(self):
        donor_list = []
        total_balance = 0
        unique_entries = set()
        docstatus = self.docstatus

        insufficient_balance_msg = "Insufficient balance for:\n"
        no_entry_msg = "No such entry exists for:\n"
        messages = []

        for p in self.custom_program_details:
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

                    match_found = True
                    balance = entry['total_balance']

                    # if balance == 0.0 and not self.is_new() and docstatus == 0:
                    if balance == 0.0:
                        insufficient_balance_msg += f"{entry.get('donor')}\n"

                    entry_key = (
                        entry.get('donor'), 
                        entry.get('program'), 
                        entry.get('subservice_area'), 
                        entry.get('project'),
                        entry.get('cost_center'),
                        entry.get('product'),
                    )

                    if entry_key in unique_entries:
                        frappe.throw(f"Duplicate Entry for donor '{entry.get('donor')}' with provided details.")

                    unique_entries.add(entry_key)

                    used_amount = 0
                    if docstatus == 1:
                        try:
                            used_amount_data = frappe.db.sql(f"""
                                SELECT SUM(debit) as used_amount
                                FROM `tabGL Entry`
                                WHERE 
                                    account = 'Capital Stock - AKFP'
                                    AND voucher_no = '{self.name}'
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
                    break

            if not match_found:
                no_entry_msg += f"{p.pd_donor}\n"

        if insufficient_balance_msg != "Insufficient balance for:\n" or no_entry_msg != "No such entry exists for:\n":
            
            if insufficient_balance_msg != "Insufficient balance for:\n":
                messages.append(insufficient_balance_msg)
            if no_entry_msg != "No such entry exists for:\n":
                messages.append(no_entry_msg)
            frappe.msgprint("\n".join(messages))

        return messages

    #added 0 logic with insufficient balanace 


@frappe.whitelist()
def donor_list_data_purchsae_receipt(doc):
    try:
        doc = frappe.get_doc(json.loads(doc))
    except (json.JSONDecodeError, TypeError) as e:
        frappe.throw(f"Invalid input: {e}")

    donor_list = []
    total_balance = 0
    unique_entries = set()
    docstatus = doc.docstatus

    insufficient_balance_msg = "Insufficient balance for:\n"
    no_entry_msg = "No such entry exists for:\n"

    for p in doc.custom_program_details:
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

                match_found = True
                balance = entry['total_balance']
                #for handling 0 after submit
                if balance == 0.0 and not doc.is_new() and docstatus == 0:
                    insufficient_balance_msg += f"{entry.get('donor')}\n"

                entry_key = (
                    entry.get('donor'), 
                    entry.get('program'), 
                    entry.get('subservice_area'), 
                    entry.get('project'),
                    entry.get('cost_center'),
                    entry.get('product'),
                )

                if entry_key in unique_entries:
                    frappe.throw(f"Duplicate Entry for donor '{entry.get('donor')}' with provided details.")

                unique_entries.add(entry_key)

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
                break

        if not match_found:
            no_entry_msg += f"{p.pd_donor}\n"

   
    if insufficient_balance_msg != "Insufficient balance for:\n" or no_entry_msg != "No such entry exists for:\n":
        messages = []
        if insufficient_balance_msg != "Insufficient balance for:\n":
            messages.append(insufficient_balance_msg)
        if no_entry_msg != "No such entry exists for:\n":
            messages.append(no_entry_msg)
        frappe.msgprint("\n".join(messages))

    return {
        "total_balance": total_balance,
        "donor_list": donor_list  
    }




@frappe.whitelist()
def donor_list_data_frappe_on_submit(doc):
    empty_message = None
    frappe.msgprint(frappe.as_json("Submitted Worked!!"))
    
    try:
        if isinstance(doc, str):
            doc = json.loads(doc)
        print("------------------------------------------------TEST")
        print(doc)
        doc = frappe.get_doc(doc)
    except (json.JSONDecodeError, TypeError) as e:
        frappe.throw(f"Invalid input: {e}")

    donor_list = []
    total_balance = 0
    unique_entries = set()
    docstatus = doc.docstatus

    insufficient_balance_msg = "Insufficient balance for:\n"
    no_entry_msg = "No such entry exists for:\n"

    for p in doc.custom_program_details:
        condition_parts = [
            f"(subservice_area = '{p.pd_subservice_area}' OR (subservice_area IS NULL AND '{p.pd_subservice_area}' = '') OR subservice_area = '')" if p.pd_subservice_area else "1=1",
            f"(donor = '{p.pd_donor}' OR (donor IS NULL AND '{p.pd_donor}' = '') OR donor = '')" if p.pd_donor else "1=1",
            f"(project = '{p.pd_project}' OR (project IS NULL AND '{p.pd_project}' = '') OR project = '')" if p.pd_project else "1=1",
            f"(cost_center = '{p.pd_cost_center}' OR (cost_center IS NULL AND '{p.pd_cost_center}' = '') OR cost_center = '')" if p.pd_cost_center else "1=1",
            f"(product = '{p.pd_product}' OR (product IS NULL AND '{p.pd_product}' = '') OR product = '')" if p.pd_product else "1=1",
            f"(program = '{p.pd_service_area}' OR (program IS NULL AND '{p.pd_service_area}' = '') OR program = '')" if p.pd_service_area else "1=1"
        ]
        condition = " AND ".join(condition_parts)

        # Debugging condition
        frappe.msgprint(f"Condition: {condition}")

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

                match_found = True
                balance = entry['total_balance']

                if balance == 0.0 and not doc.is_new() and docstatus == 0:
                    insufficient_balance_msg += f"DONOR--{entry.get('donor')}\n"

                entry_key = (
                    entry.get('donor'), 
                    entry.get('program'), 
                    entry.get('subservice_area'), 
                    entry.get('project'),
                    entry.get('cost_center'),
                    entry.get('product'),
                )

                if entry_key in unique_entries:
                    frappe.throw(f"Duplicate Entry for donor '{entry.get('donor')}' with provided details.")

                unique_entries.add(entry_key)

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
                break

        if not match_found:
            no_entry_msg += f"DONOR--{p.pd_donor}\n"

    if insufficient_balance_msg != "Insufficient balance for:\n" or no_entry_msg != "No such entry exists for:\n":
        messages = []
        if insufficient_balance_msg != "Insufficient balance for:\n":
            messages.append(insufficient_balance_msg)
        if no_entry_msg != "No such entry exists for:\n":
            messages.append(no_entry_msg)
        frappe.msgprint("\n".join(messages))
        empty_message = False
    else:
        empty_message = True

    # Update the message display for debugging purposes
    frappe.msgprint(frappe.as_json(f"Empty Message: {empty_message}"))

    return empty_message


##TEST DONOR LIST FUNC
@frappe.whitelist()
def donor_list_data_on_submit(doc):
    frappe.msgprint(frappe.as_json("Submitted Called"))
    try:
        if isinstance(doc, str):
            doc = json.loads(doc)
        print("------------------------------------------------TEST")

        print(doc)
        # frappe.msgprint(frappe.as_json(doc))
        doc = frappe.get_doc(doc)
    except (json.JSONDecodeError, TypeError) as e:
        frappe.throw(f"Invalid input: {e}")


    donor_list = []
    total_balance = 0
    unique_entries = set()
    docstatus = doc.docstatus

    for p in doc.custom_program_details:
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

                match_found = True
                entry_key = (
                    entry.get('donor'), 
                    entry.get('program'), 
                    entry.get('subservice_area'), 
                    entry.get('project'),
                    entry.get('cost_center'),
                    entry.get('product'),
                )

                if entry_key in unique_entries:
                    frappe.throw(f"Duplicate Entry for donor '{entry.get('donor')}' with provided details.")

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
                
                if balance == 0.0 and not doc.is_new() and docstatus == 0:
                    return frappe.throw(f"Submit Insufficient balance for donor '{entry.get('donor')}'")

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
                break

        if not match_found:
            frappe.throw(f'No such entry exists for donor "<bold>{p.pd_donor}</bold>" with provided details.')

    return {
        "total_balance": total_balance,
        "donor_list": donor_list  
    }