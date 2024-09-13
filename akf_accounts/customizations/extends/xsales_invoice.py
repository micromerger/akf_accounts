import frappe
import json
from erpnext.accounts.utils import get_fiscal_year
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice

class XSalesInvoice(SalesInvoice):

    def validate(self):
        super().validate()
        for i in self.items:
            if not i.asset:
                frappe.msgprint("There is no asset")
                self.validate_qty()
            else:
                # frappe.msgprint("Validate Else")
                pass
                

    def on_submit(self):
        super().on_submit()
        for i in self.items:
            if i.asset:
                frappe.msgprint("If On Submit")
                # pass
                # self.create_asset_gl_entries_for_asset_purchase()
                self.make_additional_gl_entries_for_asset()
            else:
                frappe.msgprint("Else On Submit")
                
                # pass
                self.validate_qty()
                frappe.msgprint("Else On Submit")
                self.gl_entries_inventory_purchase_disposal_sale_gain()

                
    def create_asset_gl_entries_for_asset_purchase(self):
        fiscal_year = get_fiscal_year(self.posting_date, company=self.company)[0]
        accounts_receivable = frappe.db.get_value("Company", {"name": self.company}, "default_receivable_account")
        accumulated_depreciation_account = frappe.db.get_value("Company", {"name": self.company}, "accumulated_depreciation_account")
        custom_default_asset_account = frappe.db.get_value("Company", {"name": self.company}, "custom_default_asset_account")
        gain_account = frappe.db.get_value("Company", {"name": self.company}, "custom_gain_account")
        loss_account = frappe.db.get_value("Company", {"name": self.company}, "custom_loss_account")
        unrestricted_fund_account = frappe.db.get_value("Company", {"name": self.company}, "custom_default_unrestricted_fund_account")
        designated_fund_account = frappe.db.get_value("Company", {"name": self.company}, "custom_default_designated_asset_fund_account")

        # Helper function to avoid repeating GL entry logic
        def create_gl_entry(account, debit, credit, remarks, cost_center):
            gl_entry = frappe.get_doc({
                'doctype': 'GL Entry',
                'posting_date': self.posting_date,
                'transaction_date': self.posting_date,
                'account': account,
                'against_voucher_type': 'Sales Invoice',
                'against_voucher': self.name,
                'cost_center': cost_center,
                'debit': debit,
                'credit': credit,
                'account_currency': 'PKR',
                'debit_in_account_currency': debit,
                'credit_in_account_currency': credit,
                'against': "Sales Invoice",
                'voucher_type': 'Sales Invoice',
                'voucher_no': self.name,
                'remarks': remarks,
                'is_opening': 'No',
                'is_advance': 'No',
                'fiscal_year': fiscal_year,
                'company': self.company,
                'transaction_currency': 'PKR',
                'debit_in_transaction_currency': debit,
                'credit_in_transaction_currency': credit,
                'transaction_exchange_rate': 1,
            })
            gl_entry.insert(ignore_permissions=True)
            gl_entry.submit()
        

        def create_gl_entry_accounts_receiveabe(account, debit, credit, remarks, cost_center):
            gl_entry = frappe.get_doc({
                'doctype': 'GL Entry',
                'posting_date': self.posting_date,
                'transaction_date': self.posting_date,
                'account': account,
                'against_voucher_type': 'Sales Invoice',
                'against_voucher': self.name,
                'cost_center': cost_center,
                'debit': debit,
                'credit': credit,
                'account_currency': 'PKR',
                'debit_in_account_currency': debit,
                'credit_in_account_currency': credit,
                'against': "Sales Invoice",
                'voucher_type': 'Sales Invoice',
                'voucher_no': self.name,
                'remarks': remarks,
                'is_opening': 'No',
                'is_advance': 'No',
                'fiscal_year': fiscal_year,
                'company': self.company,
                'transaction_currency': 'PKR',
                'debit_in_transaction_currency': debit,
                'credit_in_transaction_currency': credit,
                'transaction_exchange_rate': 1,
                'party_type': 'Customer',  
                'party': self.customer,
            })
            gl_entry.insert(ignore_permissions=True)
            gl_entry.submit()

        for i in self.items:
            actual_price_asset = frappe.db.sql("""
                SELECT 
                    gross_purchase_amount AS purchasing_cost,
                    CASE 
                        WHEN calculate_depreciation = 0 THEN 0
                        WHEN calculate_depreciation = 1 AND IFNULL(custom_current_asset_worth, 0) != 0 THEN custom_current_asset_worth
                        ELSE 0
                    END AS depreciation_charged
                FROM `tabAsset`
                WHERE name = %s
            """, (i.asset,), as_dict=True)

            if actual_price_asset:
                asset_purchase = float(actual_price_asset[0]['purchasing_cost'])
                depreciation_charged = float(actual_price_asset[0]['depreciation_charged'])
                
                current_worth_of_asset = asset_purchase - depreciation_charged
                
            else:
                asset_purchase = 0.0
                current_worth_of_asset = 0.0
            
            # frappe.msgprint(frappe.as_json("asset_purchase"))
            # frappe.msgprint(frappe.as_json(asset_purchase))

            # frappe.msgprint(frappe.as_json("depreciation_charged"))
            # frappe.msgprint(frappe.as_json(depreciation_charged))


            # frappe.msgprint(frappe.as_json("current_worth_of_asset"))
            # frappe.msgprint(frappe.as_json(current_worth_of_asset))

            
            if float(i.rate) > current_worth_of_asset:
                gain = float(i.rate) - current_worth_of_asset
                # frappe.msgprint(f"Gain Entry: Rate: {i.rate}, Gain: {gain}")

                # Create the gain GL entries
                create_gl_entry_accounts_receiveabe(accounts_receivable, i.rate, 0, 'Sold Item', i.cost_center)
                create_gl_entry(custom_default_asset_account, 0, asset_purchase, 'Sold Item', i.cost_center)
                create_gl_entry(gain_account, 0, gain, 'Gain on sale', i.cost_center)
                create_gl_entry(designated_fund_account, current_worth_of_asset, 0, 'Sold Item', i.cost_center)
                create_gl_entry(unrestricted_fund_account, 0, current_worth_of_asset, 'Sold Item', i.cost_center)
                if depreciation_charged != 0.0:
                    # frappe.msgprint("Gain Depreciation is zero")
                    create_gl_entry(accumulated_depreciation_account, depreciation_charged,0,  'Sold Item', i.cost_center)
                frappe.msgprint("GL Entries created successfully")

            elif float(i.rate) < current_worth_of_asset:
                loss = float(current_worth_of_asset) - float(i.rate)
                # frappe.msgprint(f"Loss Entry: Rate: {i.rate}, Loss: {loss}")
                # frappe.msgprint(f"Loss Entry: Rate: {i.rate}, Loss: {loss}")

                create_gl_entry_accounts_receiveabe(accounts_receivable, i.rate, 0, 'Sold Item', i.cost_center)
                create_gl_entry(custom_default_asset_account, 0, asset_purchase, 'Sold Item', i.cost_center)
                create_gl_entry_accounts_receiveabe(loss_account, loss, 0, 'Loss on sale', i.cost_center)
                create_gl_entry(designated_fund_account, current_worth_of_asset, 0, 'Sold Item', i.cost_center)
                create_gl_entry(unrestricted_fund_account, 0, current_worth_of_asset, 'Sold Item', i.cost_center)
                if depreciation_charged != 0.0:
                    # frappe.msgprint("Loss Depreciation is zero")
                    create_gl_entry_accounts_receiveabe(accumulated_depreciation_account, depreciation_charged, 0, 'Sold Item', i.cost_center)
                frappe.msgprint("GL Entries created successfully")
            else: 
                # frappe.msgprint(f"No Gain/Loss")
                # frappe.msgprint("depreciation_charged")
                create_gl_entry_accounts_receiveabe(accounts_receivable, i.rate, 0, 'Sold Item', i.cost_center)
                create_gl_entry(custom_default_asset_account, 0, asset_purchase, 'Sold Item', i.cost_center)
                create_gl_entry(designated_fund_account, i.rate, 0, 'Sold Item', i.cost_center)
                create_gl_entry(unrestricted_fund_account, 0, i.rate, 'Sold Item', i.cost_center)
                # frappe.msgprint(frappe.as_json(depreciation_charged))
                if depreciation_charged != 0.0:
                    # frappe.msgprint("inside depreciation_charged")

                    # create_gl_entry_accounts_receiveabe(accounts_receivable, i.rate, 0, 'Sold Item', i.cost_center)
                    create_gl_entry_accounts_receiveabe(accumulated_depreciation_account, depreciation_charged, 0, 'Sold Item', i.cost_center)
                    # create_gl_entry_accounts_receiveabe(accumulated_depreciation_account, depreciation_charged, 0, 'Sold Item', i.cost_center)
                frappe.msgprint("GL Entries created successfully")

       
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
                        f"Insufficient quantity for item {item.item_code}. "
                        f"Requested quantity: {item.qty}, Available quantity: {di.donated_qty}"
                    )

    def make_additional_gl_entries_for_asset(self):
        fiscal_year = get_fiscal_year(self.posting_date, company=self.company)[0]
        unrestricted_fund_account = frappe.db.get_value("Company", {"name": self.company}, "custom_default_unrestricted_fund_account")
        designated_fund_account = frappe.db.get_value("Company", {"name": self.company}, "custom_default_designated_asset_fund_account")

        # Helper function to avoid repeating GL entry logic
        def create_gl_entry(account, debit, credit, remarks, cost_center):
            gl_entry = frappe.get_doc({
                'doctype': 'GL Entry',
                'posting_date': self.posting_date,
                'transaction_date': self.posting_date,
                'account': account,
                'against_voucher_type': 'Sales Invoice',
                'against_voucher': self.name,
                'cost_center': cost_center,
                'debit': debit,
                'credit': credit,
                'account_currency': 'PKR',
                'debit_in_account_currency': debit,
                'credit_in_account_currency': credit,
                'against': "Sales Invoice",
                'voucher_type': 'Sales Invoice',
                'voucher_no': self.name,
                'remarks': remarks,
                'is_opening': 'No',
                'is_advance': 'No',
                'fiscal_year': fiscal_year,
                'company': self.company,
                'transaction_currency': 'PKR',
                'debit_in_transaction_currency': debit,
                'credit_in_transaction_currency': credit,
                'transaction_exchange_rate': 1,
            })
            gl_entry.insert(ignore_permissions=True)
            gl_entry.submit()
        

        def create_gl_entry_accounts_receiveabe(account, debit, credit, remarks, cost_center):
            gl_entry = frappe.get_doc({
                'doctype': 'GL Entry',
                'posting_date': self.posting_date,
                'transaction_date': self.posting_date,
                'account': account,
                'against_voucher_type': 'Sales Invoice',
                'against_voucher': self.name,
                'cost_center': cost_center,
                'debit': debit,
                'credit': credit,
                'account_currency': 'PKR',
                'debit_in_account_currency': debit,
                'credit_in_account_currency': credit,
                'against': "Sales Invoice",
                'voucher_type': 'Sales Invoice',
                'voucher_no': self.name,
                'remarks': remarks,
                'is_opening': 'No',
                'is_advance': 'No',
                'fiscal_year': fiscal_year,
                'company': self.company,
                'transaction_currency': 'PKR',
                'debit_in_transaction_currency': debit,
                'credit_in_transaction_currency': credit,
                'transaction_exchange_rate': 1,
                'party_type': 'Customer',  
                'party': self.customer,
            })
            gl_entry.insert(ignore_permissions=True)
            gl_entry.submit()

        for i in self.items:
            actual_price_asset = frappe.db.sql("""
                SELECT 
                    gross_purchase_amount AS purchasing_cost,
                    CASE 
                        WHEN calculate_depreciation = 0 THEN 0
                        WHEN calculate_depreciation = 1 AND IFNULL(custom_current_asset_worth, 0) != 0 THEN custom_current_asset_worth
                        ELSE 0
                    END AS depreciation_charged
                FROM `tabAsset`
                WHERE name = %s
            """, (i.asset,), as_dict=True)

            if actual_price_asset:
                asset_purchase = float(actual_price_asset[0]['purchasing_cost'])
                depreciation_charged = float(actual_price_asset[0]['depreciation_charged'])
                
                current_worth_of_asset = asset_purchase - depreciation_charged
                
            else:
                asset_purchase = 0.0
                current_worth_of_asset = 0.0
            
            # frappe.msgprint(frappe.as_json("asset_purchase"))
            # frappe.msgprint(frappe.as_json(asset_purchase))

            # frappe.msgprint(frappe.as_json("depreciation_charged"))
            # frappe.msgprint(frappe.as_json(depreciation_charged))


            # frappe.msgprint(frappe.as_json("current_worth_of_asset"))
            # frappe.msgprint(frappe.as_json(current_worth_of_asset))

            
            if float(i.rate) > current_worth_of_asset:
                gain = float(i.rate) - current_worth_of_asset
                # frappe.msgprint(f"Gain Entry: Rate: {i.rate}, Gain: {gain}")

                # Create the gain GL entries
                # create_gl_entry_accounts_receiveabe(accounts_receivable, i.rate, 0, 'Sold Item', i.cost_center)
                # create_gl_entry(custom_default_asset_account, 0, asset_purchase, 'Sold Item', i.cost_center)
                # create_gl_entry(gain_account, 0, gain, 'Gain on sale', i.cost_center)
                create_gl_entry(designated_fund_account, current_worth_of_asset, 0, 'Sold Item', i.cost_center)
                create_gl_entry(unrestricted_fund_account, 0, current_worth_of_asset, 'Sold Item', i.cost_center)
                # if depreciation_charged != 0.0:
                #     # frappe.msgprint("Gain Depreciation is zero")
                #     create_gl_entry(accumulated_depreciation_account, depreciation_charged,0,  'Sold Item', i.cost_center)
                frappe.msgprint("GL Entries created successfully")

            elif float(i.rate) < current_worth_of_asset:
                loss = float(current_worth_of_asset) - float(i.rate)
                # frappe.msgprint(f"Loss Entry: Rate: {i.rate}, Loss: {loss}")
                # frappe.msgprint(f"Loss Entry: Rate: {i.rate}, Loss: {loss}")

                # create_gl_entry_accounts_receiveabe(accounts_receivable, i.rate, 0, 'Sold Item', i.cost_center)
                # create_gl_entry(custom_default_asset_account, 0, asset_purchase, 'Sold Item', i.cost_center)
                # create_gl_entry_accounts_receiveabe(loss_account, loss, 0, 'Loss on sale', i.cost_center)
                create_gl_entry(designated_fund_account, current_worth_of_asset, 0, 'Sold Item', i.cost_center)
                create_gl_entry(unrestricted_fund_account, 0, current_worth_of_asset, 'Sold Item', i.cost_center)
                # if depreciation_charged != 0.0:
                    # frappe.msgprint("Loss Depreciation is zero")
                    # create_gl_entry_accounts_receiveabe(accumulated_depreciation_account, depreciation_charged, 0, 'Sold Item', i.cost_center)
                frappe.msgprint("GL Entries created successfully")
            else: 
                # frappe.msgprint(f"No Gain/Loss")
                # frappe.msgprint("depreciation_charged")
                # create_gl_entry_accounts_receiveabe(accounts_receivable, i.rate, 0, 'Sold Item', i.cost_center)
                # create_gl_entry(custom_default_asset_account, 0, asset_purchase, 'Sold Item', i.cost_center)
                create_gl_entry(designated_fund_account, i.rate, 0, 'Sold Item', i.cost_center)
                create_gl_entry(unrestricted_fund_account, 0, i.rate, 'Sold Item', i.cost_center)
                # frappe.msgprint(frappe.as_json(depreciation_charged))
                # if depreciation_charged != 0.0:
                    # frappe.msgprint("inside depreciation_charged")

                    # create_gl_entry_accounts_receiveabe(accounts_receivable, i.rate, 0, 'Sold Item', i.cost_center)
                    # create_gl_entry_accounts_receiveabe(accumulated_depreciation_account, depreciation_charged, 0, 'Sold Item', i.cost_center)
                    # create_gl_entry_accounts_receiveabe(accumulated_depreciation_account, depreciation_charged, 0, 'Sold Item', i.cost_center)
                frappe.msgprint("GL Entries created successfully")


        
    def gl_entries_inventory_purchase_disposal_sale_gain(self):
        fiscal_year = get_fiscal_year(self.posting_date, company=self.company)[0]
        inventory_account = frappe.db.get_value("Company", {"name": self.company}, "custom_default_inventory_fund_account")
        unrestricted_fund_account = frappe.db.get_value("Company", {"name": self.company}, "custom_default_unrestricted_fund_account")
        gain_account = frappe.db.get_value("Company", {"name": self.company}, "custom_gain_account")
        loss_account = frappe.db.get_value("Company", {"name": self.company}, "custom_loss_account")
        accounts_receivable = frappe.db.get_value("Company", {"name": self.company}, "default_receivable_account")
        custom_default_asset_account = frappe.db.get_value("Company", {"name": self.company}, "custom_default_asset_account")

        
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

            gl_entry_debtors_account = frappe.get_doc({
                'doctype': 'GL Entry',
                'posting_date': self.posting_date,
                'transaction_date': self.posting_date,
                'account': accounts_receivable,
                'against_voucher_type': 'Sales Invoice',
                'against_voucher': self.name,
                'cost_center': i.cost_center,
                'debit': i.amount,
                'credit': 0.0,
                'account_currency': 'PKR',
                'debit_in_account_currency': i.amount,
                'credit_in_account_currency': 0.0,
                'against': accounts_receivable,
                'voucher_type': 'Sales Invoice',
                'voucher_no': self.name,
                'remarks': 'Sold Item',
                'is_opening': 'No',
                'is_advance': 'No',
                'fiscal_year': fiscal_year,
                'company': self.company,
                'transaction_currency': 'PKR',
                'debit_in_transaction_currency': i.amount,
                'credit_in_transaction_currency': 0.0,
                'transaction_exchange_rate': 1,
                'project': i.project,
                'program': i.program,
                'subservice_area': i.subservice_area,
                'product': i.product,
                'party_type': 'Customer',  
                'party': self.customer,
            })

            gl_entry_asset_account = frappe.get_doc({
                'doctype': 'GL Entry',
                'posting_date': self.posting_date,
                'transaction_date': self.posting_date,
                'account': custom_default_asset_account,
                'against_voucher_type': 'Sales Invoice',
                'against_voucher': self.name,
                'cost_center': i.cost_center,
                'debit': 0.0,
                'credit': i.amount,
                'account_currency': 'PKR',
                'debit_in_account_currency':0.0,
                'credit_in_account_currency':i.amount,
                'against': custom_default_asset_account,
                'voucher_type': 'Sales Invoice',
                'voucher_no': self.name,
                'remarks': 'Sold Item',
                'is_opening': 'No',
                'is_advance': 'No',
                'fiscal_year': fiscal_year,
                'company': self.company,
                'transaction_currency': 'PKR',
                'debit_in_transaction_currency': 0.0,
                'credit_in_transaction_currency': i.amount,
                'transaction_exchange_rate': 1,
                'project': i.project,
                'program': i.program,
                'subservice_area': i.subservice_area,
                'product': i.product,
                'party_type': 'Customer',  
                'party': self.customer,
            })

            gl_entry_inventory_account = frappe.get_doc({
                'doctype': 'GL Entry',
                'posting_date': self.posting_date,
                'transaction_date': self.posting_date,
                'account': inventory_account,
                'against_voucher_type': 'Sales Invoice',
                'against_voucher': self.name,
                'cost_center': i.cost_center,
                'debit': i.amount,
                'credit': 0.0,
                'account_currency': 'PKR',
                'debit_in_account_currency': i.amount,
                'credit_in_account_currency': 0.0,
                'against': inventory_account,
                'voucher_type': 'Sales Invoice',
                'voucher_no': self.name,
                'remarks': 'Sold Item',
                'is_opening': 'No',
                'is_advance': 'No',
                'fiscal_year': fiscal_year,
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
                'credit': i.amount,
                'account_currency': 'PKR',
                'debit_in_account_currency': 0.0,
                'credit_in_account_currency': i.amount,
                'against': unrestricted_fund_account,
                'voucher_type': 'Sales Invoice',
                'voucher_no': self.name,
                'remarks': 'Sold Item',
                'is_opening': 'No',
                'is_advance': 'No',
                'fiscal_year': fiscal_year,
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
                    gain = float(i.rate - valuation_rate)
                    frappe.msgprint(frappe.as_json(f"Gain {gain}"))

                    gl_entry_gain_account = frappe.get_doc({
                        'doctype': 'GL Entry',
                        'posting_date': self.posting_date,
                        'transaction_date': self.posting_date,
                        'account': gain_account,
                        'against_voucher_type': 'Sales Invoice',
                        'against_voucher': self.name,
                        'cost_center': i.cost_center,
                        'debit': 0.0,
                        'credit': i.amount - valuation_rate,
                        'account_currency': 'PKR',
                        'debit_in_account_currency': 0.0,
                        'credit_in_account_currency': i.amount - valuation_rate,
                        'against': gain_account,
                        'voucher_type': 'Sales Invoice',
                        'voucher_no': self.name,
                        'remarks': 'Gain on Sale',
                        'is_opening': 'No',
                        'is_advance': 'No',
                        'fiscal_year': fiscal_year,
                        'company': self.company,
                        'transaction_currency': 'PKR',
                        'debit_in_transaction_currency': 0.0,
                        'credit_in_transaction_currency': i.amount - valuation_rate,
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
                    frappe.msgprint(f"Loss for item {i.item_code}: Valuation Rate: {valuation_rate}, Sale Rate: {i.rate}")
                    loss = float(valuation_rate) - float(i.rate)
                    frappe.msgprint(frappe.as_json(f"Loss {loss}"))
                 

                    gl_entry_loss_account = frappe.get_doc({
                        'doctype': 'GL Entry',
                        'posting_date': self.posting_date,
                        'transaction_date': self.posting_date,
                        'account': loss_account,
                        'against_voucher_type': 'Sales Invoice',
                        'against_voucher': self.name,
                        'cost_center': i.cost_center,
                        'debit': valuation_rate - i.amount,
                        'credit': 0.0,
                        'account_currency': 'PKR',
                        'debit_in_account_currency': valuation_rate - i.amount,
                        'credit_in_account_currency': 0.0,
                        'against': loss_account,
                        'voucher_type': 'Sales Invoice',
                        'voucher_no': self.name,
                        'remarks': 'Loss on Sale',
                        'is_opening': 'No',
                        'is_advance': 'No',
                        'fiscal_year': fiscal_year,
                        'company': self.company,
                        'transaction_currency': 'PKR',
                        'debit_in_transaction_currency': valuation_rate - i.amount,
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
                    
                    frappe.msgprint(f"No gain or loss for item {i.item_code}: Valuation Rate: {valuation_rate}, Sale Rate: {i.rate}")
            else:
                
                frappe.msgprint(f"No valuation rate found for item {i.item_code}")

            gl_entry_inventory_account.insert(ignore_permissions=True)
            gl_entry_inventory_account.submit()
            gl_entry_unrestricted_fund_account.insert(ignore_permissions=True)
            gl_entry_unrestricted_fund_account.submit()
            gl_entry_debtors_account.insert(ignore_permissions=True)
            gl_entry_debtors_account.submit()
            gl_entry_asset_account.insert(ignore_permissions=True)
            gl_entry_asset_account.submit()
