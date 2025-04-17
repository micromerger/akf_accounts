function make_expense_on_behalf_of(frm){
    expenseForSetQueries(frm);
}

function expenseForSetQueries(frm){
    frm.set_query("purchasing_branch", function() {
        return {
            filters: {
                company: frm.doc.company,
                is_group: 0,
                disabled: 0,
                is_internal_branch: 1,
            }
        };
    });

    frm.set_query("receiving_branch", function() {
        return {
            filters: {
                company: frm.doc.company,
                is_group: 0,
                disabled: 0,
                is_internal_branch: 1,
            }
        };
    });

    frm.set_query("expense_account", function() {
        return {
            filters: {
                is_group: 0,
                disabled: 0,
                company: frm.doc.company,
                root_type: "Expense"
            }
        };
    });

    frm.set_query("equity_account", function() {
        return {
            filters: {
                is_group: 0,
                disabled: 0,
                company: frm.doc.company,
                root_type: "Equity"
            }
        };
    });

    frm.set_query("income_account", function() {
        return {
            filters: {
                is_group: 0,
                disabled: 0,
                company: frm.doc.company,
                root_type: "Income"
            }
        };
    });

    frm.set_query("inter_branch_receivable_account", function() {
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

    frm.set_query("inter_branch_payable_account", function() {
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