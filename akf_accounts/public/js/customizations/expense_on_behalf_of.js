frappe.ui.form.on('Purchase Invoice', {
    refresh: function (frm) {
        expenseForSetQueries(frm)
    },
    custom_on_behalf_of:  function (frm){
        if(!frm.doc.custom_on_behalf_of){
            const array = ["custom_purchasing_branch", "custom_purchasing_supplier", "custom_purchasing_customer", "custom_receiving_branch",
                "custom_receiving_supplier", "custom_receiving_customer", "custom_expense_account", "custom_equity_account", "custom_income_account",
                "custom_inter_branch_receivable_account_of_customer", "custom_inter_branch_payable_account_of_supplier"
            ]
            array.forEach(element => {
                frm.set_value(element, "");
            });
        }
    }
});

function make_expense_on_behalf_of(frm) {
    expenseForSetQueries(frm);
}

function expenseForSetQueries(frm) {
    frm.set_query("custom_purchasing_branch", function () {
        return {
            filters: {
                company: frm.doc.company,
                is_group: 0,
                disabled: 0,
                custom_on_behalf_of: 1,
                name: ["!=", frm.doc.custom_receiving_branch]
            }
        };
    });
    frm.set_query("custom_purchasing_supplier", function () {
        return {
            filters: {
                disabled: 0,
                on_hold: 0,
                custom_on_behalf_of: 1,
                cost_center: frm.doc.custom_purchasing_branch
            }
        };
    });

    frm.set_query("custom_purchasing_customer", function () {
        return {
            filters: {
                disabled: 0,
                custom_on_behalf_of: 1,
                cost_center: frm.doc.custom_purchasing_branch
            }
        };
    });

    frm.set_query("custom_receiving_branch", function () {
        return {
            filters: {
                company: frm.doc.company,
                is_group: 0,
                disabled: 0,
                custom_on_behalf_of: 1,
                name: ["!=", frm.doc.custom_purchasing_branch]
            }
        };
    });

    frm.set_query("custom_receiving_supplier", function () {
        return {
            filters: {
                disabled: 0,
                on_hold: 0,
                custom_on_behalf_of: 1,
                cost_center: frm.doc.custom_receiving_branch
            }
        };
    });

    frm.set_query("custom_receiving_customer", function () {
        return {
            filters: {
                disabled: 0,
                custom_on_behalf_of: 1,
                cost_center: frm.doc.custom_receiving_branch
            }
        };
    });

    frm.set_query("custom_expense_account", function () {
        return {
            filters: {
                is_group: 0,
                disabled: 0,
                company: frm.doc.company,
                root_type: "Expense"
            }
        };
    });

    frm.set_query("custom_equity_account", function () {
        return {
            filters: {
                is_group: 0,
                disabled: 0,
                company: frm.doc.company,
                root_type: "Equity"
            }
        };
    });

    frm.set_query("custom_income_account", function () {
        return {
            filters: {
                is_group: 0,
                disabled: 0,
                company: frm.doc.company,
                root_type: "Income"
            }
        };
    });

    frm.set_query("custom_inter_branch_receivable_account_of_customer", function () {
        return {
            filters: {
                is_group: 0,
                disabled: 0,
                company: frm.doc.company,
                root_type: "Asset",
                account_type: "Receivable"
            }
        };
    });

    frm.set_query("custom_inter_branch_payable_account_of_supplier", function () {
        return {
            filters: {
                is_group: 0,
                disabled: 0,
                company: frm.doc.company,
                root_type: "Liability",
                account_type: "Payable",
            }
        };
    });
}