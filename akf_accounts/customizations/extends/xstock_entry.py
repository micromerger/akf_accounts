import frappe
import json
from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry


class XStockEntry(StockEntry):
    def validate(self):
        super(XStockEntry, self).validate()
        self.validate_difference_account()
        self.validate_warehouse_cost_centers()

    def on_submit(self):
        super(XStockEntry, self).on_submit()
        self.calculate_per_installed_for_delivery_note()
        self.set_material_request_status_per_outgoing_stock_entry()
        self.update_stock_ledger_entry()
        self.create_gl_entries_for_stock_entry()

    def calculate_per_installed_for_delivery_note(self):
        if not self.custom_delivery_note:
            return
        total_received_qty = 0.0
        total_actual_qty = 0.0
        for row in self.items:
            received_qty = self.get_receive_lost_qty(row)
            if received_qty:
                total_received_qty += received_qty[0][0]
                actual_qty = self.get_actual_qty(row)
                if actual_qty:
                    total_actual_qty += actual_qty[0][0]

        return self.set_percent_delivery_note_material_request_status(
            total_received_qty, total_actual_qty
        )

    def get_receive_lost_qty(self, row):
        return frappe.db.sql(
            f""" 
            select ifnull(sum(-1 * actual_qty),0) as qty
            from `tabStock Ledger Entry` 
            where 
                docstatus=1
                and item_code = "{row.item_code}"
                and warehouse = "{row.s_warehouse}" 
                and voucher_no in (select name as qty
                    from `tabStock Entry` 
                    where docstatus=1 and stock_entry_type = "{self.stock_entry_type}" and custom_delivery_note ="{self.custom_delivery_note}")
        """
        )

    def get_actual_qty(self, row):
        return frappe.db.sql(
            f"""  
                Select ifnull(sum(actual_qty),0) as actual_qty
                From `tabStock Ledger Entry`
                Where
                    docstatus<2
                    and item_code = "{row.item_code}"
                    and voucher_no = '{self.custom_delivery_note}'
                    and warehouse = '{row.s_warehouse}'
            """
        )

    def set_percent_delivery_note_material_request_status(
        self, total_received_qty, total_actual_qty
    ):
        per_installed = (
            (total_received_qty / total_actual_qty) * 100
            if (total_actual_qty > 0)
            else 0.0
        )

        if self.stock_entry_type == "Material Transfer":
            frappe.db.sql(
                f""" 
                update `tabDelivery Note`
                set per_installed = {per_installed}, per_billed = {per_installed}
                where name = '{self.custom_delivery_note}'
            """
            )
        elif self.stock_entry_type == "Lost / Wastage":
            frappe.db.set_value(
                "Delivery Note",
                self.custom_delivery_note,
                "custom_lost_wastage",
                per_installed,
            )

        self.update_status_delivery_note_and_material_request()

        return per_installed

    def update_status_delivery_note_and_material_request(self):

        total_percent = frappe.db.sql(
            f""" 
            Select ifnull((per_installed + custom_lost_wastage),0) as total_percent
            From `tabDelivery Note`
            where name = '{self.custom_delivery_note}'
        """,
            as_dict=0,
        )

        if total_percent:
            percent = total_percent[0][0]

            d_status = "To Receive"
            transfer_status = "In Transit"
            m_status = "Partially Received"

            if percent == 100:
                d_status = "Completed"
                transfer_status = "Completed"
                m_status = "Received"

            # Delivery Note
            frappe.db.sql(
                f""" 
                    update `tabDelivery Note`
                    set status="{d_status}"
                    where docstatus =1 
                        and name ="{self.custom_delivery_note}"
                """
            )

            # Material Request
            frappe.db.sql(
                f""" 
                    update `tabMaterial Request`
                    set transfer_status ="{transfer_status}" ,status="{m_status}", per_ordered =  {percent}
                    where name in (select custom_reference_name from `tabDelivery Note` where name="{self.custom_delivery_note}")
                """
            )

    def set_material_request_status_per_outgoing_stock_entry(self):
        if not self.outgoing_stock_entry:
            return
        actual_qty = 0.0
        received_qty = 0.0
        for row in self.items:
            _actual_qty = frappe.db.sql(
                f""" Select sum(actual_qty) as qty
                        From `tabStock Ledger Entry`
                        Where docstatus=1
                        and item_code = '{row.item_code}'
                        and warehouse = '{row.s_warehouse}' 
                        and voucher_no = '{self.outgoing_stock_entry}' """
            )

            if _actual_qty:
                actual_qty += _actual_qty[0][0]

            _received_qty = frappe.db.sql(
                f""" 
                    select ifnull(sum(actual_qty),0) as qty
                    from `tabStock Ledger Entry` 
                    where 
                        docstatus=1
                        and item_code = "{row.item_code}"
                        and warehouse = "{row.s_warehouse}" 
                        and voucher_no in (select name as qty
                            from `tabStock Entry` 
                            where docstatus=1 and outgoing_stock_entry ="{self.outgoing_stock_entry}")
                """
            )

            if _received_qty:
                _received_qty = _received_qty[0][0]
                received_qty += (
                    (-1 * _received_qty) if (_received_qty < 0) else _received_qty
                )

        if actual_qty > 0:
            per_ordered = (received_qty / actual_qty) * 100.0
            status = "Completed" if (per_ordered == 100) else "In Transit"
            frappe.db.sql(
                f""" 
                        Update `tabMaterial Request`
                        set transfer_status = "{status}",status = "{status}", per_ordered = {per_ordered}
                        Where name in (Select material_request 
                        From `tabStock Entry Detail` 
                        Where docstatus=1 and parent="{self.outgoing_stock_entry}" )"""
            )

    def update_stock_ledger_entry(self):
        for row in self.items:
            if frappe.db.exists(
                "Stock Ledger Entry",
                {
                    "docstatus": 1,
                    "voucher_no": self.name,
                },
            ):
                frappe.db.sql(
                    f""" 
                        update `tabStock Ledger Entry`
                        set custom_new = {row.custom_new}, custom_used = {row.custom_used}, program='{row.program}', subservice_area='{row.subservice_area}', product='{row.product}', project='{row.project}', inventory_flag='{row.inventory_flag}', inventory_scenario='{row.inventory_scenario}'
                        where docstatus=1 
                            and voucher_detail_no = '{row.name}'
                            and voucher_no = '{self.name}'
                    """
                )

        if self.custom_donor_ids:
            # Initialize an empty list to store child values
            child_values = []

            # Fetch child table records for the current parent document
            child_records = frappe.get_all(
                "Donor List",
                filters={"parent": self.name},
                fields=["donor"],
            )

            # Loop through each child record and process the values
            for child in child_records:
                child_values.append(child.donor)

            if frappe.db.exists(
                "Stock Ledger Entry",
                {
                    "docstatus": 1,
                    "voucher_no": self.name,
                },
            ):
                child_values_as_string = json.dumps(child_values)
                frappe.db.sql(
                    f""" 
                            update 
                                `tabStock Ledger Entry`
                            set 
                                custom_donor_list = '{child_values_as_string}'
                            where 
                                docstatus=1 
                                and voucher_no = '{self.name}'
                        """
                )

    def on_trash(self):
        self.cancel_linked_records()
        self.reset_delivery_note_percent()

    def on_cancel(self):
        super(XStockEntry, self).on_cancel()
        self.cancel_linked_records()
        self.reset_delivery_note_percent()

    def cancel_linked_records(self):
        if frappe.db.exists("Stock Ledger Entry", {"voucher_no": self.name}):
            frappe.db.sql(
                f""" 
                delete from `tabStock Ledger Entry` where voucher_no = '{self.name}'
            """
            )
        if frappe.db.exists("GL Entry", {"voucher_no": self.name}):
            frappe.db.sql(
                f""" 
                delete from `tabGL Entry` where voucher_no = '{self.name}'
            """
            )

    def reset_delivery_note_percent(self):
        if not self.custom_delivery_note:
            return

        per_installed = self.calculate_per_installed_for_delivery_note()
        if self.stock_entry_type == "Lost / Wastage":
            frappe.db.sql(
                f""" 
                update `tabDelivery Note`
                set custom_lost_wastage = custom_lost_wastage - {per_installed}
                where name = '{self.custom_delivery_note}'
            """
            )
        else:
            frappe.db.sql(
                f""" 
                update `tabDelivery Note`
                set per_installed = per_installed - {per_installed}
                where name = '{self.custom_delivery_note}'
            """
            )

    def validate_difference_account(self):
        company = frappe.get_doc("Company", self.company)
        for d in self.get("items"):
            d.expense_account = company.custom_default_inventory_fund_account

    def validate_qty(self):
        if (
            self.stock_entry_type == "Donated Inventory Consumption - Restricted"
            or self.stock_entry_type == "Donated Inventory Transfer - Restricted"
        ):
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
                        f"(warehouse = '{item.s_warehouse}' OR (warehouse IS NULL AND '{item.s_warehouse}' = '') OR warehouse = '')"
                        if item.s_warehouse
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
                except Exception as e:
                    frappe.throw(f"Error executing query: {e}")

                for di in donated_invetory:
                    if di.donated_qty > item.qty:
                        pass
                    else:
                        frappe.throw(
                            f"{item.item_code} quantity doesn't exist against condtions {condition}"
                        )
        else:
            super(XStockEntry, self).validate_qty()

    def create_gl_entries_for_stock_entry(self):
        debit_account, credit_account = "", ""

        company = frappe.get_doc("Company", self.company)
        if self.stock_entry_type == "Donated Inventory Receive - Restricted":
            pass

        elif self.stock_entry_type == "Donated Inventory Consumption - Restricted":
            debit_account = company.custom_default_inventory_expense_account
            credit_account = company.default_income_account

            if not debit_account or not credit_account:
                frappe.throw("Required accounts not found in the company")

            # Create the GL entry for the debit account and update
            debit_entry = self.get_gl_entry_dict()
            debit_entry.update(
                {
                    "account": debit_account,
                    "debit": self.total_outgoing_value,
                    "credit": 0,
                    "debit_in_account_currency": self.total_outgoing_value,
                    "credit_in_account_currency": 0,
                }
            )
            debit_gl = frappe.get_doc(debit_entry)
            debit_gl.flags.ignore_permissions = True
            debit_gl.insert()
            debit_gl.submit()

            credit_entry = self.get_gl_entry_dict()
            credit_entry.update(
                {
                    "account": credit_account,
                    "debit": 0,
                    "credit": self.total_outgoing_value,
                    "debit_in_account_currency": 0,
                    "credit_in_account_currency": self.total_outgoing_value,
                }
            )
            credit_gl = frappe.get_doc(credit_entry)
            credit_gl.flags.ignore_permissions = True
            credit_gl.insert()
            credit_gl.submit()

        elif self.stock_entry_type == "Donated Inventory Transfer - Restricted":
            debit_account = company.default_inventory_account
            credit_account = company.custom_default_inventory_fund_account

            source_cost_center, target_cost_center = "", ""
            for item in self.items:
                source_warehouse = item.s_warehouse
                source_cost_center = frappe.db.get_value(
                    "Warehouse", source_warehouse, "custom_cost_center"
                )

                target_warehouse = item.t_warehouse
                target_cost_center = frappe.db.get_value(
                    "Warehouse", target_warehouse, "custom_cost_center"
                )

            if not debit_account or not credit_account:
                frappe.throw("Required accounts not found in the company")
            # Create the GL entry for the debit account and update
            debit_entry = self.get_gl_entry_dict()
            debit_entry.update(
                {
                    "account": debit_account,
                    "debit": self.total_incoming_value,
                    "cost_center": source_cost_center,
                    "credit": 0,
                    "debit_in_account_currency": self.total_incoming_value,
                    "credit_in_account_currency": 0,
                }
            )
            debit_gl = frappe.get_doc(debit_entry)
            debit_gl.flags.ignore_permissions = True
            debit_gl.insert()
            debit_gl.submit()

            credit_entry = self.get_gl_entry_dict()
            credit_entry.update(
                {
                    "account": credit_account,
                    "debit": 0,
                    "cost_center": target_cost_center,
                    "credit": self.total_incoming_value,
                    "debit_in_account_currency": 0,
                    "credit_in_account_currency": self.total_incoming_value,
                }
            )
            credit_gl = frappe.get_doc(credit_entry)
            credit_gl.flags.ignore_permissions = True
            credit_gl.insert()
            credit_gl.submit()

            debit_account = company.custom_default_inventory_fund_account
            credit_account = company.default_inventory_account

            if not debit_account or not credit_account:
                frappe.throw("Required accounts not found in the company")
            # Create the GL entry for the debit account and update
            debit_entry = self.get_gl_entry_dict()
            debit_entry.update(
                {
                    "account": debit_account,
                    "debit": self.total_incoming_value,
                    "cost_center": source_cost_center,
                    "credit": 0,
                    "debit_in_account_currency": self.total_incoming_value,
                    "credit_in_account_currency": 0,
                }
            )
            debit_gl = frappe.get_doc(debit_entry)
            debit_gl.flags.ignore_permissions = True
            debit_gl.insert()
            debit_gl.submit()

            credit_entry = self.get_gl_entry_dict()
            credit_entry.update(
                {
                    "account": credit_account,
                    "debit": 0,
                    "cost_center": target_cost_center,
                    "credit": self.total_incoming_value,
                    "debit_in_account_currency": 0,
                    "credit_in_account_currency": self.total_incoming_value,
                }
            )
            credit_gl = frappe.get_doc(credit_entry)
            credit_gl.flags.ignore_permissions = True
            credit_gl.insert()
            credit_gl.submit()

    def get_gl_entry_dict(self):
        cost_center = ""
        for item in self.items:
            cost_center = item.cost_center
        return frappe._dict(
            {
                "doctype": "GL Entry",
                "posting_date": self.posting_date,
                "transaction_date": self.posting_date,
                "party_type": "Donor",
                "party": self.donor,
                "cost_center": cost_center,
                "against": f"Stock Entry: {self.name}",
                "against_voucher_type": "Stock Entry",
                "against_voucher": self.name,
                "voucher_type": "Stock Entry",
                "voucher_subtype": self.stock_entry_type,
                "voucher_no": self.name,
                "project": self.project,
                "company": self.company,
                "program": self.program,
            }
        )

    def validate_warehouse_cost_centers(self):
        for item in self.items:
            source_cost_center, target_cost_center = "", ""
            if self.stock_entry_type == "Donated Inventory Receive - Restricted":
                target_warehouse = item.t_warehouse
                target_cost_center = frappe.db.get_value(
                    "Warehouse", target_warehouse, "custom_cost_center"
                )
                item.cost_center = target_cost_center
            elif self.stock_entry_type == "Donated Inventory Consumption - Restricted":
                source_warehouse = item.s_warehouse
                source_cost_center = frappe.db.get_value(
                    "Warehouse", source_warehouse, "custom_cost_center"
                )
                item.cost_center = source_cost_center
