import frappe
import json
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
# from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice 


class XSalesInvoice(SalesInvoice):

    def validate(self):
        super().validate()
        self.validate_qty()

    def on_submit(self):
        super().on_submit()
        self.create_gl_entries_for_sales_disposal_sale_gain()

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

    def create_gl_entries_for_sales_disposal_sale_gain(self):
        inventory_account = frappe.db.get_value("Company", {"name": self.company}, "custom_default_inventory_fund_account")
        unrestricted_fund_account = frappe.db.get_value("Company", {"name": self.company}, "custom_default_unrestricted_fund_account")
        
        frappe.msgprint(frappe.as_json(inventory_account))
        frappe.msgprint(frappe.as_json(unrestricted_fund_account))
        
        actual_item_price = frappe.db.sql("""
            SELECT sii.item_code, i.valuation_rate 
            FROM `tabSales Invoice` AS si 
            INNER JOIN `tabSales Invoice Item` AS sii ON si.name = sii.parent 
            INNER JOIN `tabItem` AS i ON sii.item_code = i.item_code
            WHERE si.name = %s
        """, (self.name,), as_dict=True)
        
        frappe.msgprint(frappe.as_json(actual_item_price))

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
                    frappe.msgprint(f"Gain for item {i.item_code}: Valuation Rate: {valuation_rate}, Sale Rate: {i.rate}")

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

                elif valuation_rate > i.rate:
                    frappe.msgprint(f"Loss for item {i.item_code}: Valuation Rate: {valuation_rate}, Sale Rate: {i.rate}")

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

                else:
                    frappe.msgprint(f"No gain or loss for item {i.item_code}: Valuation Rate: {valuation_rate}, Sale Rate: {i.rate}")
            else:
                frappe.msgprint(f"No valuation rate found for item {i.item_code}")

            gl_entry_inventory_account.insert(ignore_permissions=True)
            gl_entry_inventory_account.submit()
            gl_entry_unrestricted_fund_account.insert(ignore_permissions=True)
            gl_entry_unrestricted_fund_account.submit()
