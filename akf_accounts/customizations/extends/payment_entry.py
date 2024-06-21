import frappe
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry


class XPaymentEntry(PaymentEntry):
    def validate(self):
        self.update_leaf()

    def update_leaf(self):
        if self.docstatus == 0:
            frappe.db.set_value(
                "Cheque Leaf", self.custom_cheque_leaf, "status", "Issued"
            )
            frappe.db.set_value(
                "Cheque Leaf", self.custom_cheque_leaf, "voucher_type", "Payment Entry"
            )
            frappe.db.set_value(
                "Cheque Leaf", self.custom_cheque_leaf, "voucher_no", self.name
            )
            frappe.db.set_value(
                "Cheque Leaf", self.custom_cheque_leaf, "voucher_status", "Draft"
            )
            frappe.db.set_value(
                "Cheque Leaf", self.custom_cheque_leaf, "party_type", self.party_type
            )
            frappe.db.set_value(
                "Cheque Leaf", self.custom_cheque_leaf, "party", self.party
            )
            frappe.db.set_value(
                "Cheque Leaf",
                self.custom_cheque_leaf,
                "cheque_date",
                self.clearance_date,
            )
            frappe.db.set_value(
                "Cheque Leaf", self.custom_cheque_leaf, "amount", self.paid_amount
            )
            frappe.db.set_value(
                "Cheque Leaf", self.custom_cheque_leaf, "remarks", self.remarks
            )

    def on_submit(self):
        super().on_submit()
        frappe.db.set_value("Cheque Leaf", self.custom_cheque_leaf, "status", "Cleared")
        frappe.db.set_value(
            "Cheque Leaf", self.custom_cheque_leaf, "voucher_type", "Payment Entry"
        )
        frappe.db.set_value(
            "Cheque Leaf", self.custom_cheque_leaf, "voucher_no", self.name
        )
        frappe.db.set_value(
            "Cheque Leaf", self.custom_cheque_leaf, "voucher_status", "Submitted"
        )

    def on_cancel(self):
        super().on_cancel()
        frappe.db.set_value(
            "Cheque Leaf", self.custom_cheque_leaf, "status", "Cancelled"
        )


@frappe.whitelist()
def check_dublicate(cheque_no):
    if frappe.db.exists("Cheque Leaf", cheque_no):
        pass
        # frappe.throw(
        #     f"An Payment Entry already exists against Cheque Leaf: {cheque_no}"
        # )
