frappe.ui.form.on('Donation', {
    /* onload: function(frm) {
    }, */
    refresh: function (frm) {
        set_queries(frm);
        set_custom_btns(frm);
    },
    service_area: function (frm) {
        frm.call("set_details");
    },
    donation_amount: function (frm) {
        frm.call("calculate_percentage");
    },
    company: function (frm) {
        // frm.set_value('service_area', '');
        // frm.clear_table('deduction_breakeven');
    }
});

frappe.ui.form.on('Deduction Breakeven', {
    percentage: function (frm, cdt, cdn) {
        frm.call("calculate_percentage");
    },
    amount: function (frm, cdt, cdn) {
        // frm.call("calculate_percentage");
    },
    deduction_breakeven_remove: function (frm) {
        frm.call("calculate_percentage");
    }
});

function set_queries(frm) {
    // set query on Account in `Deduction Breakeven`
    frm.fields_dict['deduction_breakeven'].grid.get_field('account').get_query = function (doc, cdt, cdn) {
        return {
            filters: {
                root_type: 'Income',
                is_group: 0,
                company: frm.doc.company
            }
        };
    };

    frm.set_query('cheque_leaf', function () {
        return {
            filters: {
                status: 'On Hand'
            }
        };
    });

    frm.set_query('receivable_account', function () {
        return {
            filters: {
                account_type: 'Receivable',
                company: frm.doc.company,
                is_group: 0
            }
        };
    });

    frm.set_query('fund_class', function () {
        return {
            filters: {
                root_type: 'Equity',
                is_group: 0,
                company: frm.doc.company
            }
        };
    });

    frm.set_query('cost_center', function () {
        return {
            filters: {
                company: frm.doc.company
            }
        };
    });

    frm.set_query('product', function () {
        if (!frm.doc.subservice_area) {
            frm.set_value('product', '');
        }
        return {
            filters: {
                subservice_area: frm.doc.subservice_area
            }
        };
    });

    frm.set_query('subservice_area', function () {
        if (!frm.doc.service_area) {
            frm.set_value('subservice_area', '');
        }
        return {
            filters: {
                service_area: frm.doc.service_area
            }
        };
    });
}

function set_custom_btns(frm) {
    if(frm.doc.docstatus!=1 || frm.doc.status=="Paid") return
    if(frm.doc.contribution_type == "Pledge"){
        frm.add_custom_button(__('Payment Entry'), function () {
            frappe.model.open_mapped_doc({
                method: "akf_accounts.akf_accounts.doctype.donation.donation._make_payment_entry",
                frm: cur_frm
            })
        }, __("Create"));
    }
    frm.add_custom_button(__('Accounting Ledger'), function () {
        frappe.set_route("query-report", "General Ledger", {"voucher_no": frm.doc.name});
    }, __("View"));
}


 // if (frm.doc.custom_payment_status === "Paid") {
    //     frm.page.set_indicator('Paid', 'green');
    // } else {
    //     frm.page.set_indicator('Unpaid', 'red');
    // }