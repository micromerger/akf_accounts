// Copyright (c) 2024, Mubarrim Iqbal
// For license information, please see license.txt

frappe.ui.form.on("Cheque Book", {
  refresh(frm) {
    frm.set_value(
      "last_cheque_no",
      frm.doc.first_cheque_no + (frm.doc.number_of_leafs - 1)
    );
    frm.add_custom_button(
      __("New Cheque Book"),
      function () {
        frappe.call({
          method:
            "akf_accounts.cheque_management.doctype.cheque_book.cheque_book.create_cheque_leaf",
          args: {
            company: frm.doc.company,
            cheque_book: frm.doc.cheque_book,
            bank_account: frm.doc.bank_account,
            account_number: frm.doc.account_number,
            bank_name: frm.doc.bank_name,
            branch: frm.doc.branch,
            issue_date: frm.doc.issue_date,
            first_cheque_no: frm.doc.first_cheque_no,
            last_cheque_no: frm.doc.last_cheque_no,
          },
          callback: function (r) {
            frappe.msgprint(
              __(
                "Total " +
                  frm.doc.number_of_leafs +
                  " Cheque Leafs have been created!"
              )
            );
          },
        });
      },
      __("Create")
    );
    frm.trigger("set_reports_to_query");
  },

  company: function (frm) {
    if (frm.doc.company==undefined || frm.doc.company=="") {
      frm.set_value("bank_account", "");
    }
    frm.trigger("set_reports_to_query");
  },
  set_reports_to_query: function (frm) {
    var company = frm.doc.company;
    frm.set_query("bank_account", function () {
      return {
        filters: {
          company: company,
        },
      };
    });
  },
});
