# Copyright (c) 2024, Mubarrim Iqbal
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ChequeBook(Document):
    pass


@frappe.whitelist()
def create_cheque_leaf(
    company,
    cheque_book,
    bank_account,
    account_number,
    bank_name,
    branch,
    issue_date,
    first_cheque_no,
    last_cheque_no,
):
    args = {
        "doctype": "Cheque Leaf",
        "company": company,
        "cheque_book_no": cheque_book,
        "bank_account": bank_account,
        "account_number": account_number,
        "bank_name": bank_name,
        "branch": branch,
        "issue_date": issue_date,
        "first_cheque_no": first_cheque_no,
        "status": "On Hand",
    }
    cheque_no = first_cheque_no
    for cheque_no in range(int(first_cheque_no), int(last_cheque_no) + 1):
        args.update({"cheque_no": cheque_no})
        frappe.get_doc(args).save(ignore_permissions=True)
