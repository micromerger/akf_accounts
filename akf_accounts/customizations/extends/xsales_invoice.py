import frappe
import json
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice

class XSalesInvoice(SalesInvoice):

    def validate(self):
        super().validate()
        for i in self.items:
            if not i.asset:
                self.validate_qty()
            else:
                pass
                

    def on_submit(self):
        super().on_submit()
        for i in self.items:
            if i.asset:
                self.create_asset_gl_entries_for_asset_purchase()
            else:
                # pass
                # self.make_gl_entries()
                self.gl_entries_inventory_purchase_disposal_sale_gain()


    def create_asset_gl_entries_for_asset_purchase(self):
        default_income = frappe.db.get_value("Company", {"name": self.company}, "custom_default_income")
        accumulated_depreciation_account = frappe.db.get_value("Company", {"name": self.company}, "accumulated_depreciation_account")
        custom_default_asset_account = frappe.db.get_value("Company", {"name": self.company}, "custom_default_asset_account")
        gain_account = 'Gain - AKFP'
        loss_account = 'Loss - AKFP'
        unrestricted_fund_account = frappe.db.get_value("Company", {"name": self.company}, "custom_default_unrestricted_fund_account")
        designated_fund_account = frappe.db.get_value("Company", {"name": self.company}, "custom_default_designated_asset_fund_account")
        frappe.msgprint("designated_fund_account")
        frappe.msgprint(designated_fund_account)
        frappe.msgprint(default_income)
        frappe.msgprint(accumulated_depreciation_account)
        frappe.msgprint(custom_default_asset_account)
        frappe.msgprint(gain_account)
        frappe.msgprint(loss_account)
        frappe.msgprint(unrestricted_fund_account)

        for i in self.items:
            actual_price_asset = frappe.db.sql("""
                SELECT 
                    gross_purchase_amount AS purchasing_cost,
                    CASE 
                        WHEN calculate_depreciation = 0 THEN gross_purchase_amount
                        WHEN calculate_depreciation = 1 AND IFNULL(custom_current_asset_worth, 0) != 0 THEN custom_current_asset_worth
                        ELSE gross_purchase_amount
                    END AS current_worth
                FROM `tabAsset`
                WHERE name = %s
            """, (i.asset,))

            # Convert the results to floats
            asset_purchase = float(actual_price_asset[0][0]) if actual_price_asset else 0.0
            depreciation_charged = float(actual_price_asset[0][1]) if actual_price_asset else 0.0
            current_worth = asset_purchase - depreciation_charged
            frappe.msgprint(f"depreciation_amount: {depreciation_charged}")
            frappe.msgprint(f"Purchasing Cost: {asset_purchase}")
            frappe.msgprint(f"Purchasing Cost: {current_worth}")

            if actual_price_asset:
                asset_purchase = float(actual_price_asset[0][0])
                current_worth = float(actual_price_asset[0][1]) if actual_price_asset[0][1] is not None else 0.0
            else:
                asset_purchase = 0.0
                current_worth = 0.0


            if float(i.rate) > asset_purchase:
                frappe.msgprint("Gain Entry")
                frappe.msgprint(f"Rate: {i.rate}")
                gain = float(i.rate) - current_worth
                frappe.msgprint(f"Difference: {gain}")



                gl_entry_default_income_account = frappe.get_doc({
                    'doctype': 'GL Entry',
                    'posting_date': self.posting_date,
                    'transaction_date': self.posting_date,
                    'account': default_income,
                    'against_voucher_type': 'Sales Invoice',
                    'against_voucher': self.name,
                    'cost_center': i.cost_center,
                    'debit': i.rate,
                    'credit': 0.0,
                    'account_currency': 'PKR',
                    'debit_in_account_currency': i.rate,
                    'credit_in_account_currency': 0.0,
                    'against': "Sales Invoice",
                    'voucher_type': 'Sales Invoice',
                    'voucher_no': self.name,
                    'remarks': 'Sold Item',
                    'is_opening': 'No',
                    'is_advance': 'No',
                    'fiscal_year': '2024-2025',
                    'company': self.company,
                    'transaction_currency': 'PKR',
                    'debit_in_transaction_currency': i.rate,
                    'credit_in_transaction_currency': 0.0,
                    'transaction_exchange_rate': 1,

                })
                gl_entry_default_income_account.insert(ignore_permissions=True)
                gl_entry_default_income_account.submit()

                gl_entry_accumulated_depreciation_account = frappe.get_doc({
                    'doctype': 'GL Entry',
                    'posting_date': self.posting_date,
                    'transaction_date': self.posting_date,
                    'account': accumulated_depreciation_account,
                    'against_voucher_type': 'Sales Invoice',
                    'against_voucher': self.name,
                    'cost_center': i.cost_center,
                    'debit': depreciation_charged,
                    'credit': 0.0,
                    'account_currency': 'PKR',
                    'debit_in_account_currency':  depreciation_charged,
                    'credit_in_account_currency': 0.0,
                    'against': "Sales Invoice",
                    'voucher_type': 'Sales Invoice',
                    'voucher_no': self.name,
                    'remarks': 'Sold Item',
                    'is_opening': 'No',
                    'is_advance': 'No',
                    'fiscal_year': '2024-2025',
                    'company': self.company,
                    'transaction_currency': 'PKR',
                    'debit_in_transaction_currency':  depreciation_charged,
                    'credit_in_transaction_currency': 0.0,
                    'transaction_exchange_rate': 1,

                })
                gl_entry_accumulated_depreciation_account.insert(ignore_permissions=True)
                gl_entry_accumulated_depreciation_account.submit()

                gl_entry_custom_default_asset_account = frappe.get_doc({
                    'doctype': 'GL Entry',
                    'posting_date': self.posting_date,
                    'transaction_date': self.posting_date,
                    'account': custom_default_asset_account,
                    'against_voucher_type': 'Sales Invoice',
                    'against_voucher': self.name,
                    'cost_center': i.cost_center,
                    'debit': 0.0,
                    'credit': asset_purchase,
                    'account_currency': 'PKR',
                    'debit_in_account_currency': 0.0,
                    'credit_in_account_currency':asset_purchase,
                    'against': "Sales Invoice",
                    'voucher_type': 'Sales Invoice',
                    'voucher_no': self.name,
                    'remarks': 'Sold Item',
                    'is_opening': 'No',
                    'is_advance': 'No',
                    'fiscal_year': '2024-2025',
                    'company': self.company,
                    'transaction_currency': 'PKR',
                    'debit_in_transaction_currency': 0.0,
                    'credit_in_transaction_currency':asset_purchase,
                    'transaction_exchange_rate': 1,

                })
                gl_entry_custom_default_asset_account.insert(ignore_permissions=True)
                gl_entry_custom_default_asset_account.submit()

                gl_entry_gain_account = frappe.get_doc({
                    'doctype': 'GL Entry',
                    'posting_date': self.posting_date,
                    'transaction_date': self.posting_date,
                    'account': gain_account,
                    'against_voucher_type': 'Sales Invoice',
                    'against_voucher': self.name,
                    'cost_center': i.cost_center,
                    'debit': 0.0,
                    'credit': gain,
                    'account_currency': 'PKR',
                    'debit_in_account_currency':0.0,
                    'credit_in_account_currency': gain,
                    'against': "Sales Invoice",
                    'voucher_type': 'Sales Invoice',
                    'voucher_no': self.name,
                    'remarks': 'Sold Item',
                    'is_opening': 'No',
                    'is_advance': 'No',
                    'fiscal_year': '2024-2025',
                    'company': self.company,
                    'transaction_currency': 'PKR',
                    'debit_in_transaction_currency': 0.0,
                    'credit_in_transaction_currency':gain,
                    'transaction_exchange_rate': 1,

                })
                gl_entry_gain_account.insert(ignore_permissions=True)
                gl_entry_gain_account.submit()

                gl_entry_designated_fund_account = frappe.get_doc({
                    'doctype': 'GL Entry',
                    'posting_date': self.posting_date,
                    'transaction_date': self.posting_date,
                    'account': designated_fund_account,
                    'against_voucher_type': 'Sales Invoice',
                    'against_voucher': self.name,
                    'cost_center': i.cost_center,
                    'debit': current_worth,
                    'credit': 0.0,
                    'account_currency': 'PKR',
                    'debit_in_account_currency': current_worth,
                    'credit_in_account_currency': 0.0,
                    'against': "Sales Invoice",
                    'voucher_type': 'Sales Invoice',
                    'voucher_no': self.name,
                    'remarks': 'Sold Item',
                    'is_opening': 'No',
                    'is_advance': 'No',
                    'fiscal_year': '2024-2025',
                    'company': self.company,
                    'transaction_currency': 'PKR',
                    'debit_in_transaction_currency': current_worth,
                    'credit_in_transaction_currency': 0.0,
                    'transaction_exchange_rate': 1,

                })
                gl_entry_designated_fund_account.insert(ignore_permissions = True)
                gl_entry_designated_fund_account.submit()


                gl_entry_unrestricted_fund_account = frappe.get_doc({
                    'doctype': 'GL Entry',
                    'posting_date': self.posting_date,
                    'transaction_date': self.posting_date,
                    'account': unrestricted_fund_account,
                    'against_voucher_type': 'Sales Invoice',
                    'against_voucher': self.name,
                    'cost_center': i.cost_center,
                    'debit': 0.0,
                    'credit':current_worth,
                    'account_currency': 'PKR',
                    'debit_in_account_currency':0.0,
                    'credit_in_account_currency': current_worth,
                    'against': "Sales Invoice",
                    'voucher_type': 'Sales Invoice',
                    'voucher_no': self.name,
                    'remarks': 'Sold Item',
                    'is_opening': 'No',
                    'is_advance': 'No',
                    'fiscal_year': '2024-2025',
                    'company': self.company,
                    'transaction_currency': 'PKR',
                    'debit_in_transaction_currency': 0.0,
                    'credit_in_transaction_currency':current_worth,
                    'transaction_exchange_rate': 1,

                })
                gl_entry_unrestricted_fund_account.insert()
                gl_entry_unrestricted_fund_account.submit()

            elif float(i.rate) < float(asset_purchase):
                frappe.msgprint("Loss Entry")
                frappe.msgprint(f"Rate: {i.rate}")
                loss = current_worth - float(i.rate)
                frappe.msgprint(f"Difference: {loss}")



                gl_entry_default_income_account = frappe.get_doc({
                    'doctype': 'GL Entry',
                    'posting_date': self.posting_date,
                    'transaction_date': self.posting_date,
                    'account': default_income,
                    'against_voucher_type': 'Sales Invoice',
                    'against_voucher': self.name,
                    'cost_center': i.cost_center,
                    'debit': i.rate,
                    'credit': 0.0,
                    'account_currency': 'PKR',
                    'debit_in_account_currency': i.rate,
                    'credit_in_account_currency': 0.0,
                    'against': "Sales Invoice",
                    'voucher_type': 'Sales Invoice',
                    'voucher_no': self.name,
                    'remarks': 'Sold Item',
                    'is_opening': 'No',
                    'is_advance': 'No',
                    'fiscal_year': '2024-2025',
                    'company': self.company,
                    'transaction_currency': 'PKR',
                    'debit_in_transaction_currency': i.rate,
                    'credit_in_transaction_currency': 0.0,
                    'transaction_exchange_rate': 1,

                })
                gl_entry_default_income_account.insert(ignore_permissions=True)
                gl_entry_default_income_account.submit()

                gl_entry_accumulated_depreciation_account = frappe.get_doc({
                    'doctype': 'GL Entry',
                    'posting_date': self.posting_date,
                    'transaction_date': self.posting_date,
                    'account': accumulated_depreciation_account,
                    'against_voucher_type': 'Sales Invoice',
                    'against_voucher': self.name,
                    'cost_center': i.cost_center,
                    'debit': depreciation_charged,
                    'credit': 0.0,
                    'account_currency': 'PKR',
                    'debit_in_account_currency':  depreciation_charged,
                    'credit_in_account_currency': 0.0,
                    'against': "Sales Invoice",
                    'voucher_type': 'Sales Invoice',
                    'voucher_no': self.name,
                    'remarks': 'Sold Item',
                    'is_opening': 'No',
                    'is_advance': 'No',
                    'fiscal_year': '2024-2025',
                    'company': self.company,
                    'transaction_currency': 'PKR',
                    'debit_in_transaction_currency':  depreciation_charged,
                    'credit_in_transaction_currency': 0.0,
                    'transaction_exchange_rate': 1,

                })
                gl_entry_accumulated_depreciation_account.insert(ignore_permissions=True)
                gl_entry_accumulated_depreciation_account.submit()

                gl_entry_custom_default_asset_account = frappe.get_doc({
                    'doctype': 'GL Entry',
                    'posting_date': self.posting_date,
                    'transaction_date': self.posting_date,
                    'account': custom_default_asset_account,
                    'against_voucher_type': 'Sales Invoice',
                    'against_voucher': self.name,
                    'cost_center': i.cost_center,
                    'debit': 0.0,
                    'credit': asset_purchase,
                    'account_currency': 'PKR',
                    'debit_in_account_currency': 0.0,
                    'credit_in_account_currency':asset_purchase,
                    'against': "Sales Invoice",
                    'voucher_type': 'Sales Invoice',
                    'voucher_no': self.name,
                    'remarks': 'Sold Item',
                    'is_opening': 'No',
                    'is_advance': 'No',
                    'fiscal_year': '2024-2025',
                    'company': self.company,
                    'transaction_currency': 'PKR',
                    'debit_in_transaction_currency': 0.0,
                    'credit_in_transaction_currency':asset_purchase,
                    'transaction_exchange_rate': 1,

                })
                gl_entry_custom_default_asset_account.insert(ignore_permissions=True)
                gl_entry_custom_default_asset_account.submit()

                gl_entry_loss_account = frappe.get_doc({
                    'doctype': 'GL Entry',
                    'posting_date': self.posting_date,
                    'transaction_date': self.posting_date,
                    'account': loss_account,
                    'against_voucher_type': 'Sales Invoice',
                    'against_voucher': self.name,
                    'cost_center': i.cost_center,
                    'debit': 0.0,
                    'credit': loss,
                    'account_currency': 'PKR',
                    'debit_in_account_currency':0.0,
                    'credit_in_account_currency': loss,
                    'against': "Sales Invoice",
                    'voucher_type': 'Sales Invoice',
                    'voucher_no': self.name,
                    'remarks': 'Sold Item',
                    'is_opening': 'No',
                    'is_advance': 'No',
                    'fiscal_year': '2024-2025',
                    'company': self.company,
                    'transaction_currency': 'PKR',
                    'debit_in_transaction_currency': 0.0,
                    'credit_in_transaction_currency':loss,
                    'transaction_exchange_rate': 1,

                })
                gl_entry_loss_account.insert(ignore_permissions=True)
                gl_entry_loss_account.submit()

                gl_entry_designated_fund_account = frappe.get_doc({
                    'doctype': 'GL Entry',
                    'posting_date': self.posting_date,
                    'transaction_date': self.posting_date,
                    'account': designated_fund_account,
                    'against_voucher_type': 'Sales Invoice',
                    'against_voucher': self.name,
                    'cost_center': i.cost_center,
                    'debit': current_worth,
                    'credit': 0.0,
                    'account_currency': 'PKR',
                    'debit_in_account_currency': current_worth,
                    'credit_in_account_currency': 0.0,
                    'against': "Sales Invoice",
                    'voucher_type': 'Sales Invoice',
                    'voucher_no': self.name,
                    'remarks': 'Sold Item',
                    'is_opening': 'No',
                    'is_advance': 'No',
                    'fiscal_year': '2024-2025',
                    'company': self.company,
                    'transaction_currency': 'PKR',
                    'debit_in_transaction_currency': current_worth,
                    'credit_in_transaction_currency': 0.0,
                    'transaction_exchange_rate': 1,

                })
                gl_entry_designated_fund_account.insert(ignore_permissions=True)
                gl_entry_designated_fund_account.submit()


                gl_entry_unrestricted_fund_account = frappe.get_doc({
                    'doctype': 'GL Entry',
                    'posting_date': self.posting_date,
                    'transaction_date': self.posting_date,
                    'account': unrestricted_fund_account,
                    'against_voucher_type': 'Sales Invoice',
                    'against_voucher': self.name,
                    'cost_center': i.cost_center,
                    'debit': 0.0,
                    'credit':current_worth,
                    'account_currency': 'PKR',
                    'debit_in_account_currency':0.0,
                    'credit_in_account_currency': current_worth,
                    'against': "Sales Invoice",
                    'voucher_type': 'Sales Invoice',
                    'voucher_no': self.name,
                    'remarks': 'Sold Item',
                    'is_opening': 'No',
                    'is_advance': 'No',
                    'fiscal_year': '2024-2025',
                    'company': self.company,
                    'transaction_currency': 'PKR',
                    'debit_in_transaction_currency': 0.0,
                    'credit_in_transaction_currency':current_worth,
                    'transaction_exchange_rate': 1,

                })
                gl_entry_unrestricted_fund_account.insert(ignore_permissions=True)
                gl_entry_unrestricted_fund_account.submit()
            else:
                frappe.msgprint("No Loss/Profit")

          

       
    def validate_qty(self):
        # if (
        #     self.stock_entry_type == "Donated Inventory Consumption - Restricted"
        #     or self.stock_entry_type == "Donated Inventory Transfer - Restricted"
        # ):
            for item in self.items:
                condition_parts = [
                    (
                        f"(custom_new = '{item.custom_new}' OR (custom_new IS NULL AND '{item.custom_new}' = '') OR custom_new = '')"
                        if item.custom_new
                        else "1=1"
                    ),
                    (
                        f"(custom_used = '{item.custom_used}' OR (custom_used IS NULL AND '{item.custom_used}' = '') OR custom_used = '')"
                        if item.custom_used
                        else "1=1"
                    ),
                    (
                        f"(warehouse = '{item.warehouse}' OR (warehouse IS NULL AND '{item.warehouse}' = '') OR warehouse = '')"
                        if item.warehouse
                        else "1=1"
                    ),
                    (
                        f"(inventory_flag = '{item.inventory_flag}' OR (inventory_flag IS NULL AND '{item.inventory_flag}' = '') OR inventory_flag = '')"
                        if item.inventory_flag
                        else "1=1"
                    ),
                    (
                        f"(program = '{item.program}' OR (program IS NULL AND '{item.program}' = '') OR program = '')"
                        if item.program
                        else "1=1"
                    ),
                    (
                        f"(subservice_area = '{item.subservice_area}' OR (subservice_area IS NULL AND '{item.subservice_area}' = '') OR subservice_area = '')"
                        if item.subservice_area
                        else "1=1"
                    ),
                    (
                        f"(product = '{item.product}' OR (product IS NULL AND '{item.product}' = '') OR product = '')"
                        if item.product
                        else "1=1"
                    ),
                    (
                        f"(project = '{item.project}' OR (project IS NULL AND '{item.project}' = '') OR project = '')"
                        if item.project
                        else "1=1"
                    ),
                ]
                condition = " AND ".join(condition_parts)
                # frappe.msgprint(frappe.as_json(condition))

                try:
                    donated_invetory = frappe.db.sql(
                        f"""
                        SELECT ifnull(SUM(actual_qty),0) as donated_qty,
                            item_code
                        FROM `tabStock Ledger Entry`
                        WHERE
                            item_code='{item.item_code}'
                            {f'AND {condition}' if condition else ''}
                    """,
                        as_dict=True,
                    )

                    # frappe.msgprint(frappe.as_json(donated_invetory))
                except Exception as e:
                    frappe.throw(f"Error executing query: {e}")

                for di in donated_invetory:
                    if di.donated_qty > item.qty:
                        pass
                    else:
                        frappe.throw(
                            f"{item.item_code} quantity doesn't exist against condtions {condition}"
                    
                        )


    def make_gl_entries(self):
        pass
    def gl_entries_inventory_purchase_disposal_sale_gain(self):
        inventory_account = frappe.db.get_value("Company", {"name": self.company}, "custom_default_inventory_fund_account")
        unrestricted_fund_account = frappe.db.get_value("Company", {"name": self.company}, "custom_default_unrestricted_fund_account")
        
        # frappe.msgprint(frappe.as_json(inventory_account))
        # frappe.msgprint(frappe.as_json(unrestricted_fund_account))
        
        actual_item_price = frappe.db.sql("""
            SELECT sii.item_code, i.valuation_rate 
            FROM `tabSales Invoice` AS si 
            INNER JOIN `tabSales Invoice Item` AS sii ON si.name = sii.parent 
            INNER JOIN `tabItem` AS i ON sii.item_code = i.item_code
            WHERE si.name = %s
        """, (self.name,), as_dict=True)
        
        # frappe.msgprint(frappe.as_json(actual_item_price))

        item_valuation_dict = {item['item_code']: item['valuation_rate'] for item in actual_item_price}

        for i in self.items:
            gl_entry_inventory_account = frappe.get_doc({
                'doctype': 'GL Entry',
                'posting_date': self.posting_date,
                'transaction_date': self.posting_date,
                'account': inventory_account,
                'against_voucher_type': 'Sales Invoice',
                'against_voucher': self.name,
                'cost_center': i.cost_center,
                'debit': i.rate,
                'credit': 0.0,
                'account_currency': 'PKR',
                'debit_in_account_currency': i.rate,
                'credit_in_account_currency': 0.0,
                'against': unrestricted_fund_account,
                'voucher_type': 'Sales Invoice',
                'voucher_no': self.name,
                'remarks': 'Sold Item',
                'is_opening': 'No',
                'is_advance': 'No',
                'fiscal_year': '2024-2025',
                'company': self.company,
                'transaction_currency': 'PKR',
                'debit_in_transaction_currency': i.rate,
                'credit_in_transaction_currency': 0.0,
                'transaction_exchange_rate': 1,
                'project': i.project,
                'program': i.program,
                'subservice_area': i.subservice_area,
                'product': i.product
            })

            gl_entry_unrestricted_fund_account = frappe.get_doc({
                'doctype': 'GL Entry',
                'posting_date': self.posting_date,
                'transaction_date': self.posting_date,
                'account': unrestricted_fund_account,
                'against_voucher_type': 'Sales Invoice',
                'against_voucher': self.name,
                'cost_center': i.cost_center,
                'debit': 0.0,
                'credit': i.rate,
                'account_currency': 'PKR',
                'debit_in_account_currency': 0.0,
                'credit_in_account_currency': i.rate,
                'against': inventory_account,
                'voucher_type': 'Sales Invoice',
                'voucher_no': self.name,
                'remarks': 'Sold Item',
                'is_opening': 'No',
                'is_advance': 'No',
                'fiscal_year': '2024-2025',
                'company': self.company,
                'transaction_currency': 'PKR',
                'debit_in_transaction_currency': 0.0,
                'credit_in_transaction_currency': i.rate,
                'transaction_exchange_rate': 1,
                'project': i.project,
                'program': i.program,
                'subservice_area': i.subservice_area,
                'product': i.product
            })

            valuation_rate = item_valuation_dict.get(i.item_code)
            if valuation_rate:
                if valuation_rate < i.rate:
                    # frappe.msgprint(f"Gain for item {i.item_code}: Valuation Rate: {valuation_rate}, Sale Rate: {i.rate}")

                    gl_entry_gain_account = frappe.get_doc({
                        'doctype': 'GL Entry',
                        'posting_date': self.posting_date,
                        'transaction_date': self.posting_date,
                        'account': 'Gain - AKFP',
                        'against_voucher_type': 'Sales Invoice',
                        'against_voucher': self.name,
                        'cost_center': i.cost_center,
                        'debit': 0.0,
                        'credit': i.rate - valuation_rate,
                        'account_currency': 'PKR',
                        'debit_in_account_currency': 0.0,
                        'credit_in_account_currency': i.rate - valuation_rate,
                        'against': inventory_account,
                        'voucher_type': 'Sales Invoice',
                        'voucher_no': self.name,
                        'remarks': 'Gain on Sale',
                        'is_opening': 'No',
                        'is_advance': 'No',
                        'fiscal_year': '2024-2025',
                        'company': self.company,
                        'transaction_currency': 'PKR',
                        'debit_in_transaction_currency': 0.0,
                        'credit_in_transaction_currency': i.rate - valuation_rate,
                        'transaction_exchange_rate': 1,
                        'project': i.project,
                        'program': i.program,
                        'subservice_area': i.subservice_area,
                        'product': i.product
                    })

                    gl_entry_gain_account.insert(ignore_permissions=True)
                    gl_entry_gain_account.submit()
                    frappe.msgprint("GL Entries created successfully")

                elif valuation_rate > i.rate:
                    # frappe.msgprint(f"Loss for item {i.item_code}: Valuation Rate: {valuation_rate}, Sale Rate: {i.rate}")

                    gl_entry_loss_account = frappe.get_doc({
                        'doctype': 'GL Entry',
                        'posting_date': self.posting_date,
                        'transaction_date': self.posting_date,
                        'account': 'Loss - AKFP',
                        'against_voucher_type': 'Sales Invoice',
                        'against_voucher': self.name,
                        'cost_center': i.cost_center,
                        'debit': valuation_rate - i.rate,
                        'credit': 0.0,
                        'account_currency': 'PKR',
                        'debit_in_account_currency': valuation_rate - i.rate,
                        'credit_in_account_currency': 0.0,
                        'against': inventory_account,
                        'voucher_type': 'Sales Invoice',
                        'voucher_no': self.name,
                        'remarks': 'Loss on Sale',
                        'is_opening': 'No',
                        'is_advance': 'No',
                        'fiscal_year': '2024-2025',
                        'company': self.company,
                        'transaction_currency': 'PKR',
                        'debit_in_transaction_currency': valuation_rate - i.rate,
                        'credit_in_transaction_currency': 0.0,
                        'transaction_exchange_rate': 1,
                        'project': i.project,
                        'program': i.program,
                        'subservice_area': i.subservice_area,
                        'product': i.product
                    })

                    gl_entry_loss_account.insert(ignore_permissions=True)
                    gl_entry_loss_account.submit()
                    frappe.msgprint("GL Entries created successfully")

                else:
                    pass
                    # frappe.msgprint(f"No gain or loss for item {i.item_code}: Valuation Rate: {valuation_rate}, Sale Rate: {i.rate}")
            else:
                pass
                # frappe.msgprint(f"No valuation rate found for item {i.item_code}")

            gl_entry_inventory_account.insert(ignore_permissions=True)
            gl_entry_inventory_account.submit()
            gl_entry_unrestricted_fund_account.insert(ignore_permissions=True)
            gl_entry_unrestricted_fund_account.submit()
