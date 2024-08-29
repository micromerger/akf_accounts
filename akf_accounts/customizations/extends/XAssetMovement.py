import frappe
from frappe import _
from erpnext.assets.doctype.asset_movement.asset_movement import AssetMovement
from frappe.utils import nowdate

class AssetMovementExtendedClass(AssetMovement):
    def validate(self):
        super().validate()
        # frappe.msgprint("This is my extended code Asset Movement.")
        # self.create_asset_movement_gl_entries()
    def on_submit(self):
        super().on_submit()
        # frappe.msgprint("This is my extended submit code Asset Movement.")
        self.create_asset_movement_gl_entries()
        self.change_cost_center()

    def create_asset_movement_gl_entries(self):
        if self.purpose == "Transfer":
            self.create_gl_entries_for_asset_movement()

    def create_gl_entries_for_asset_movement(self):
        company = frappe.get_doc("Company", self.company)
        credit_account1 = company.custom_default_asset_account                    #Asset cost credited
        credit_account2 = company.custom_default_designated_asset_fund_account    #Asset worth credited
        debit_account1 = company.custom_default_designated_asset_fund_account     #Asset worth debited
        debit_account2 = company.accumulated_depreciation_account                 #Asset worth debited
        debit_account3 = company.custom_default_asset_nbv_account                 #Asset worth debited
        # frappe.msgprint(frappe.as_json("credit_account1"))
        # frappe.msgprint(frappe.as_json(credit_account1))
        # frappe.msgprint(frappe.as_json("credit_account2"))
        # frappe.msgprint(frappe.as_json(credit_account2))
        # frappe.msgprint(frappe.as_json("debit_account1"))
        # frappe.msgprint(frappe.as_json(debit_account1))
        # frappe.msgprint(frappe.as_json("debit_account2"))
        # frappe.msgprint(frappe.as_json(debit_account2))
        # frappe.msgprint(frappe.as_json("debit_account3"))
        # frappe.msgprint(frappe.as_json(debit_account3))

        if not credit_account1 or not credit_account2 or not debit_account1 or not debit_account2 or not debit_account3:
            frappe.throw(_("The company does not have the required accounts configured."))

        for item in self.assets:
            # frappe.msgprint(frappe.as_json("item.asset"))
            # frappe.msgprint(frappe.as_json(item.asset))
            if not item.asset:
                
                frappe.msgprint(_("Asset field is empty for some asset items."))
                continue

            try:
                asset_doc = frappe.get_doc("Asset", item.asset)
                # frappe.msgprint(frappe.as_json("asset_doc"))
                # frappe.msgprint(frappe.as_json(asset_doc))
                total_asset_cost = frappe.db.get_value("Asset", asset_doc, "total_asset_cost")
                # frappe.msgprint(frappe.as_json("total_asset_cost"))
                # frappe.msgprint(frappe.as_json(total_asset_cost))
                asset_worth = frappe.db.get_value("Asset", asset_doc, "custom_asset_worth")
                # frappe.msgprint(frappe.as_json("asset_worth"))
                # frappe.msgprint(frappe.as_json(asset_worth))
                accumulated_depreciation = frappe.db.get_value("Asset", asset_doc, "custom_total_accumulated_depreciation")
                # frappe.msgprint(frappe.as_json("accumulated_depreciation"))
                # frappe.msgprint(frappe.as_json(accumulated_depreciation))
        
                
            except Exception:
                frappe.msgprint(_("Error fetching asset document."))
                continue
            
            if not total_asset_cost:
                frappe.msgprint(_("The asset does not have a total asset cost specified."))
                continue

            # frappe.msgprint(f"The total cost is {total_asset_cost}")
            # frappe.msgprint(f"The worth is {asset_worth} and depreciation is {accumulated_depreciation}")

            if asset_worth or accumulated_depreciation:
                # frappe.msgprint("##########################")
                # frappe.msgprint("When it's not None")
                # Create credit entry1
                credit_entry1 = self.get_gl_entry_dict(item.custom_target_cost_center)
                credit_entry1.update({
                    'account': credit_account1,
                    'debit': 0,
                    'credit': total_asset_cost,
                    'debit_in_account_currency': 0,
                    'credit_in_account_currency': total_asset_cost
                })
                credit_gl1 = frappe.get_doc(credit_entry1)
                credit_gl1.insert(ignore_permissions = True)
                credit_gl1.submit()

                # Create credit entry2
                credit_entry2 = self.get_gl_entry_dict(item.custom_target_cost_center)
                credit_entry2.update({
                    'account': credit_account2,
                    'debit': 0,
                    'credit': asset_worth,
                    'debit_in_account_currency': 0,
                    'credit_in_account_currency': asset_worth
                })  
                credit_gl2 = frappe.get_doc(credit_entry2)
                credit_gl2.insert(ignore_permissions = True)
                credit_gl2.submit()

                # Create debit entry 1
                debit_entry1 = self.get_gl_entry_dict(item.custom_source_cost_center)
                debit_entry1.update({
                    'account': debit_account1,
                    'debit': asset_worth,
                    'credit': 0,
                    'debit_in_account_currency': asset_worth,
                    'credit_in_account_currency': 0
                })
                debit_gl1 = frappe.get_doc(debit_entry1)
                debit_gl1.insert(ignore_permissions = True)
                debit_gl1.submit()

                # Create debit entry 2
                debit_entry2 = self.get_gl_entry_dict(item.custom_source_cost_center)
                debit_entry2.update({
                    'account': debit_account2,
                    'debit': accumulated_depreciation,
                    'credit': 0,
                    'debit_in_account_currency': accumulated_depreciation,
                    'credit_in_account_currency': 0
                })
                debit_gl2 = frappe.get_doc(debit_entry2)
                debit_gl2.insert(ignore_permissions=True)
                debit_gl2.submit()

                # Create Debit Entry 3 (Asset Worth to Asset NBV)
                debit_entry3 = self.get_gl_entry_dict(item.custom_source_cost_center)
                debit_entry3.update({
                    'account': debit_account3,
                    'debit': asset_worth,
                    'credit': 0,
                    'debit_in_account_currency': asset_worth,
                    'credit_in_account_currency': 0
                })
                debit_gl3 = frappe.get_doc(debit_entry3)
                debit_gl3.insert(ignore_permissions = True)
                debit_gl3.submit()
                frappe.msgprint("GL Entries have been created")
            elif asset_worth is None or accumulated_depreciation is None:
                # frappe.msgprint("##########################")
                # frappe.msgprint("When it's None")
                # Create credit entry1
                credit_entry1 = self.get_gl_entry_dict(item.custom_target_cost_center)
                credit_entry1.update({
                    'account': credit_account1,
                    'debit': 0,
                    'credit': total_asset_cost,
                    'debit_in_account_currency': 0,
                    'credit_in_account_currency': total_asset_cost
                })
                credit_gl1 = frappe.get_doc(credit_entry1)
                credit_gl1.insert(ignore_permissions = True)
                credit_gl1.submit()

                # Create credit entry2
                credit_entry2 = self.get_gl_entry_dict(item.custom_target_cost_center)
                credit_entry2.update({
                    'account': credit_account2,
                    'debit': 0,
                    'credit': total_asset_cost,
                    'debit_in_account_currency': 0,
                    'credit_in_account_currency': total_asset_cost
                })  
                credit_gl2 = frappe.get_doc(credit_entry2)
                credit_gl2.insert(ignore_permissions = True)
                credit_gl2.submit()

                # Create debit entry 1
                debit_entry1 = self.get_gl_entry_dict(item.custom_source_cost_center)
                debit_entry1.update({
                    'account': debit_account1,
                    'debit': total_asset_cost,
                    'credit': 0,
                    'debit_in_account_currency': total_asset_cost,
                    'credit_in_account_currency': 0
                })
                debit_gl1 = frappe.get_doc(debit_entry1)
                debit_gl1.insert(ignore_permissions = True)
                debit_gl1.submit()

                # Create debit entry 2
                debit_entry2 = self.get_gl_entry_dict(item.custom_source_cost_center)
                debit_entry2.update({
                    'account': debit_account2,
                    'debit': total_asset_cost,
                    'credit': 0,
                    'debit_in_account_currency': total_asset_cost,
                    'credit_in_account_currency': 0
                })
                debit_gl2 = frappe.get_doc(debit_entry2)
                debit_gl2.insert(ignore_permissions=True)
                debit_gl2.submit()

                # Create Debit Entry 3 (Asset Worth to Asset NBV)
                debit_entry3 = self.get_gl_entry_dict(item.custom_source_cost_center)
                debit_entry3.update({
                    'account': debit_account3,
                    'debit': total_asset_cost,
                    'credit': 0,
                    'debit_in_account_currency': total_asset_cost,
                    'credit_in_account_currency': 0
                })
                debit_gl3 = frappe.get_doc(debit_entry3)
                debit_gl3.insert(ignore_permissions = True)
                debit_gl3.submit()
                frappe.msgprint("GL Entries have been created")
            else: 
                # frappe.msgprint("Else part is runninggggg!")
                pass
            

    def get_gl_entry_dict(self, custom_target_cost_center=None):
        return frappe._dict({
            'doctype': 'GL Entry',
            'posting_date': nowdate(),  # Current date for posting_date
            'transaction_date': nowdate(),  # Current date for transaction_date
            'cost_center': custom_target_cost_center,
            'against': f"Asset Movement: {self.name}",
            'against_voucher_type': 'Asset Movement',
            'against_voucher': self.name,
            'voucher_type': 'Asset Movement',
            'voucher_subtype': 'Transfer',
            'voucher_no': self.name,
            'company': self.company,
        })
    def change_cost_center(self):
        for item in self.assets:
            if item.asset:
                frappe.db.set_value('Asset', item.asset, 'cost_center', item.custom_target_cost_center)




@frappe.whitelist()
def get_target_cost_center(custom_source_cost_center):
    cost_centers = frappe.db.sql("""
        SELECT name 
        FROM `tabCost Center` 
        WHERE name != %s
    """, (custom_source_cost_center,), as_dict=True)
    return [cc['name'] for cc in cost_centers]