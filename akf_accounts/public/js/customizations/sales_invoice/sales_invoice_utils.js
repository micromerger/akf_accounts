frappe.ui.form.on('Sales Invoice', {
    onload: function (frm) {
        frm.set_query('custom_fund_account_for_disposal', 'items', function (doc, cdt, cdn) {
            // var d = locals[cdt][cdn];
            return {
                "filters": {
                    "account_type": "Equity",
                    "root_type": "Equity",
                    "is_group": 0,
                    "company": frm.doc.company
                }
            };
        });
    }
});