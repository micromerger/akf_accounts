frappe.provide("erpnext.accounts");

const DI_LIST = ["Unknown", "Merchant"];

frappe.ui.form.on('Donation', {
    onload_post_render: function (frm) {
        frm.get_field("payment_detail").grid.set_multiple_add("pay_service_area");
        frm.refresh_field('payment_detail');
    },
    onload: function (frm) {
        erpnext.accounts.dimensions.setup_dimension_filters(frm, frm.doctype);
        // frm.refresh_field('payment_detail');
    },
    refresh: function (frm) {
        set_queries(frm);
        set_query_subservice_area(frm);
        set_custom_btns(frm);
        set_labels(frm);
        set_exchange_rate_msg(frm);
        toggleModeOfPaymentRowWise(frm);
    },
    donor_identity: function (frm) {
        if (frm.doc.donor_identity == "Unknown" || frm.doc.donor_identity == "Merchant - Unknown" || frm.doc.donor_identity == "Merchant - Known") {
            frm.set_value("contribution_type", "Donation");
            frm.set_df_property("contribution_type", "read_only", 1)
        } else {
            frm.set_value("contribution_type", "");
            frm.set_value("mode_of_payment", null);
            frm.set_value("account_paid_to", null);
            frm.set_df_property("contribution_type", "read_only", 0)
        }
    },
    contribution_type: function (frm) {
        frm.call("set_deduction_breakeven");
        toggleModeOfPaymentRowWise(frm);
    },
    donation_type: function (frm) {
        // frm.call("set_deduction_breakeven");
    },
    company: function (frm) {
        // erpnext.accounts.dimensions.update_dimension(frm, frm.doctype);
        // frm.set_value('service_area', '');
        // frm.clear_table('deduction_breakeven');
    },
    subservice_area: function (frm) {
    },
    currency: function (frm) {
        frappe.call({
            method: "erpnext.setup.utils.get_exchange_rate",
            args: {
                transaction_date: frm.doc.posting_date,
                from_currency: frm.doc.currency,
                to_currency: frm.doc.to_currency,
            },
            freeze: true,
            freeze_message: __("Fetching exchange rates ..."),
            callback: function (r) {
                const rate = r.message;
                frm.set_value("exchange_rate", rate);
                set_exchange_rate_msg(frm);
            }
        });
    },
    exchange_rate: function (frm) {
        frm.call("set_deduction_breakeven");
    },
    // In parent donation-table
    mode_of_payment: function (frm) {
        const mode_of_payment = frm.doc.mode_of_payment;
        if (mode_of_payment == undefined || mode_of_payment == '') {
            frm.set_value('account_paid_to', null);
        } else {
            erpnext.accounts.pos.get_payment_mode_account(frm, mode_of_payment, function (account) {
                frm.set_value('account_paid_to', account);
            });
        }
    },
});

frappe.ui.form.on('Payment Detail', {
    donor_id: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        row.donor = row.donor_id;
        // frm.call("set_deduction_breakeven");        
    },
    donation_type: function (frm) {
        if (frm.doc.is_return) {
            frm.call("update_deduction_breakeven");
        } else {
            frm.call("set_deduction_breakeven");
        }
    },
    pay_service_area: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        row.service_area = row.pay_service_area;
        frm.call("set_deduction_breakeven");  // nabeel saleem
    },
    pay_subservice_area: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        row.subservice_area = row.pay_subservice_area;
        set_query_product(frm);
    },
    pay_product: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        row.product = row.pay_product;
        frm.refresh_field("payment_detail")
    },
    project_id: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        row.project = row.project_id;

        if (row.pay_service_area != undefined || row.pay_service_area != "") {
            if (frm.doc.is_return) {
                frm.call("update_deduction_breakeven");
            } else {
                frm.call("set_deduction_breakeven");
            }
        }
    },
    // In child Payment Detail table
    mode_of_payment: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.mode_of_payment == undefined || row.mode_of_payment == '') {
            row.transaction_no_cheque_no = '';
            row.reference_date = null;
            row.account_paid_to = null;
            frm.fields_dict['payment_detail'].grid.grid_rows_by_docname[cdn].refresh_field('reference_date');

        } else {
            row.transaction_no_cheque_no = '';
            erpnext.accounts.pos.get_payment_mode_account(frm, row.mode_of_payment, function (account) {
                row.account_paid_to = account;
                frm.fields_dict['payment_detail'].grid.grid_rows_by_docname[cdn].refresh_field('account_paid_to');
                frm.fields_dict['payment_detail'].grid.grid_rows_by_docname[cdn].refresh_field('transaction_no_cheque_no');
            });
        }
        frm.refresh_field("payment_detail");
    },
    donation_amount: function (frm, cdt, cdn) {
        // if(frm.doc.is_return){
        // frm.call("update_deduction_breakeven");
        // }else{
        frm.call("set_deduction_breakeven");
        // frm.call("just_breakeven", {row: row});
        // }
    },
    /* payment_detail_add: function(frm, cdt ,cdn){
        let row = locals[cdt][cdn];
        if(frm.doc.donor_identity == "Unknown" || frm.doc.donor_identity == "Merchant"){
            row.donor_id = "DONOR-2024-00004";
        }else {
            row.donor_id = null;
        }
        frm.refresh_field("payment_detail");
    }, */
    payment_detail_add: function (frm, cdt, cdn) {
        if (frm.doc.is_return) { return; }
        let row = locals[cdt][cdn];
        row.random_id = Math.floor((1000 + row.idx) + (Math.random() * 9000));
        // toggleModeOfPaymentRowWise(frm);
        showHideModeOfPaymentForSingleRow(frm, row);
        fill_mode_of_payment_and_account(frm, row);
        frm.refresh_field("payment_detail");
        // if(frm.doc.is_return){
        //     frm.call("update_deduction_breakeven");
        // }else{
        //     frm.call("set_deduction_breakeven");
        // }
    },
    payment_detail_remove: function (frm) {
        // if(frm.doc.is_return){
        // frm.call("update_deduction_breakeven");
        // }else{
        // frm.call("set_deduction_breakeven");
        // }

    },
});

frappe.ui.form.on('Deduction Breakeven', {
    percentage: function (frm, cdt, cdn) {
        // if(frm.doc.is_return){
        // frm.call("update_deduction_breakeven");
        // }else{
        frm.call("set_deduction_breakeven");
        // }
    },
    amount: function (frm, cdt, cdn) {
        // frm.call("calculate_percentage");
    },
    deduction_breakeven_remove: function (frm) {
        // frm.call("calculate_percentage");
        frm.call("set_deduction_breakeven");
    }
});

/* CUSTOM BUTTONS ON TOP OF DOCTYPE */
function set_custom_btns(frm) {

    function doubtful_debtors() {
        if(frm.doc.status != "Paid" && frm.doc.contribution_type == "Pledge") {
            frm.add_custom_button(__('Written Off Debt'), function () {
                doubtful_debtors_dialog(frm, "Written Off", "Record Written Off", false, true);
            });
            frm.add_custom_button(__('Doubtful Debt'), function () {
                doubtful_debtors_dialog(frm, "Doubtful Debt", "Record Doubtful Debt", true, false);
            });
        }
    }
    function unknonw_to_known() {
        function get_idx_list() {
            let idx_list;
            frappe.call({
                method: "akf_accounts.akf_accounts.doctype.donation.donation.get_idx_list_unknown",
                async: false,
                args: {
                    donation_id: frm.doc.name,
                },
                callback: function (r) {
                    let data = r.message;
                    idx_list = data;
                }
            });
            return idx_list;
        }
        function get_dialog(title, idx_list) {
            let d = new frappe.ui.Dialog({
                title: title,
                fields: [
                    {
                        label: 'Donor (Known)',
                        fieldname: 'donor',
                        fieldtype: 'Link',
                        options: "Donor",
                        reqd: 1,
                        get_query() {
                            return {
                                filters: {
                                    donor_name: ["not in", ["Unknown Donor", "Merchant Known"]]
                                }
                            }
                        }
                    },
                    {
                        label: 'Payment Detail Serial No',
                        fieldname: 'serial_no',
                        fieldtype: 'Select',
                        options: idx_list,
                        reqd: 1
                    }
                ],
                size: 'small', // small, large, extra-large 
                primary_action_label: 'Submit',
                primary_action(values) {
                    // console.log(values);
                    if (values) {
                        /* frappe.call({
                            method: "akf_accounts.akf_accounts.doctype.donation.donation.set_unknown_to_known",
                            args: {
                                name: frm.doc.name,
                                values: values
                            },
                            callback: function (r) {
                                d.hide();
                                frm.reload_doc()
                            }
                        }); */
                        // frm.add_custom_button(__('Reverse Donor'), function () {
                            frappe.model.open_mapped_doc({
                            method:"akf_accounts.akf_accounts.doctype.donation.unknown_to_known.convert_unknown_to_known",
                                frm: cur_frm,
                                args: values
                            });
                        // });
                    }
                }
            });
            d.show();
        }
        if (frm.doc.donor_identity == "Unknown" && frm.doc.contribution_type === "Donation") {
            let idx_list = get_idx_list();
            if(idx_list.length>0){
                frm.add_custom_button(__('Reverse Donor'), function () {
                    const title = "Unknown to Known donor";
                    get_dialog(title, idx_list);
                });
            }
        }
    }
    function accounting_ledger() {
        frm.add_custom_button(__('Accounting Ledger'), function () {
            frappe.set_route("query-report", "General Ledger", { "voucher_no": frm.doc.name });
        }, __("View"));
    }
    function payment_entry() {
        if (frm.doc.status != "Paid") {
            if (frm.doc.contribution_type == "Pledge") {
                frm.add_custom_button(__('Payment Entry'), function () {
                    pledge_payment_entry(frm);
                }, __("Create"));
            } else if (frm.doc.status == 'Return') {
                // return_payment_entry(frm);
            } else if (frm.doc.status == "Partly Return") {
                credit_note_return(frm);
            }
        } else if (frm.doc.status == "Paid") {
            credit_note_return(frm);
        }
    }
    if (frm.doc.docstatus == 1) {
        unknonw_to_known();
        doubtful_debtors();
        accounting_ledger();
        payment_entry();
    }
}
/* END CUSTOM BUTTONS ON TOP OF DOCTYPE */

function set_labels(frm){
    function reverse_against_label(){
        if(frm.doc.unknown_to_known){
            frm.set_df_property('return_against', 'label', 'Reverse Against');
        }
    }
    reverse_against_label();
}
/* APPLYING SET QUERIES */
function set_queries(frm) {

    frm.set_query('cash_received_by_finance', function () {
        return {
            filters: {
                company: frm.doc.company,
                department: ['like', 'Finance - AKFP']
            }
        };
    });

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

    frm.set_query('donation_cost_center', function () {
        return {
            filters: {
                is_group: 0,
                disabled: 0,
                company: frm.doc.company,
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
    set_queries_payment_details(frm);
}

function set_queries_payment_details(frm) {
    set_query_donor_id(frm);
    set_query_subservice_area(frm);
    set_query_product(frm);
    set_query_account(frm);
    set_query_project(frm);
    set_query_equity_account(frm);
    set_query_receivable_account(frm);
    set_query_account_paid_to(frm);
    set_query_mode_of_payment(frm);
}

function set_query_donor_id(frm) {
    frm.fields_dict['payment_detail'].grid.get_field('donor_id').get_query = function (doc, cdt, cdn) {
        // var row = locals[cdt][cdn];
        return {
            filters: {
                status: "Active",
                donor_identity: frm.doc.donor_identity,
                default_currency: frm.doc.currency,
            }
        };
        // if (frm.doc.donor_identity == "Unknown" || frm.doc.donor_identity == "Merchant") {
        //     let dlist = frm.doc.unknonw_to_known == undefined ? ["in", "Unknown Donor"] : ["not in", "Unknown Donor"];
        //     return {
        //         filters: {
        //             donor_name: dlist,
        //             status: "Active",
        //         }
        //     };
        // } else if (frm.doc.donor_identity == "Known") {
        //     let dlist = ["not in", "Unknown Donor"];
        //     return {
        //         filters: {
        //             donor_name: dlist,
        //             status: "Active",
        //         }
        //     };
        // }
        // else if (frm.doc.donor_identity == "Merchant - Known") {
        //     let dlist = ["not in", "Unknown Donor"];
        //     return {
        //         filters: {
        //             donor_name: dlist,
        //             status: "Active",
        //         }
        //     };
        // }
        // else if (frm.doc.donor_identity == "Merchant - Unknown") {
        //     let dlist = ["not in", "known Donor"];
        //     return {
        //         filters: {
        //             donor_name: dlist,
        //             status: "Active",
        //         }
        //     };
        // }

    };
}

function set_query_subservice_area(frm) {
    frm.fields_dict['payment_detail'].grid.get_field('pay_subservice_area').get_query = function (doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        let ffilters = row.pay_service_area == undefined ? { service_area: ["!=", undefined] } : { service_area: row.pay_service_area };
        return {
            filters: ffilters
        };
        // return {
        //     filters: {
        //         service_area: ["!=", ""],
        //         service_area: row.pay_service_area,
        //     }
        // };
    };
}
// Payment Detail
function set_query_product(frm) {
    frm.fields_dict['payment_detail'].grid.get_field('pay_product').get_query = function (doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        let ffilters = row.pay_subservice_area == undefined ? { subservice_area: ["!=", undefined] } : { subservice_area: row.pay_subservice_area };
        return {
            filters: ffilters
        };
    };
}
// Payment Detail
function set_query_account(frm) {
    frm.fields_dict['payment_detail'].grid.get_field('account').get_query = function (doc, cdt, cdn) {
        // var row = locals[cdt][cdn];
        return {
            filters: {
                is_group: 0,
                company: ["!=", ""],
                company: frm.doc.company,
                root_type: "Equity",

            }
        };
    };
}
// Payment Detail
function set_query_project(frm) {
    frm.fields_dict['payment_detail'].grid.get_field('project_id').get_query = function (doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        let service_area = row.pay_service_area == undefined ? ["!=", undefined] : row.pay_service_area;
        return {
            filters: {
                company: frm.doc.company,
                custom_service_area: service_area,
                custom_allocation_check: 0
            }
        };
    };
}

function set_query_equity_account(frm) {
    frm.fields_dict['payment_detail'].grid.get_field('equity_account').get_query = function (doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                company: ["!=", ""],
                company: frm.doc.company,
                root_type: "Equity",
                // account_currency: frm.doc.currency,
            }
        };
    };
}

function set_query_receivable_account(frm) {
    frm.fields_dict['payment_detail'].grid.get_field('receivable_account').get_query = function (doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                company: ["!=", ""],
                company: frm.doc.company,
                account_type: "Receivable",
            }
        };
    };
}

function set_query_account_paid_to(frm) {
    frm.fields_dict['payment_detail'].grid.get_field('account_paid_to').get_query = function (doc, cdt, cdn) {
        var account_types = in_list(["Receive", "Internal Transfer"], "Receive") ?
            ["Bank", "Cash"] : [frappe.boot.party_account_types["Donor"]];
        return {
            filters: {
                "account_type": ["in", account_types],
                "is_group": 0,
                "company": frm.doc.company
            }
        }
    };
}
function set_query_mode_of_payment(frm) {
    frm.fields_dict['payment_detail'].grid.get_field('mode_of_payment').get_query = function (doc, cdt, cdn) {
        return {
            filters: {
                enabled: 1,
            }
        };
    };
}
/* END APPLYING SET QUERIES */
function set_exchange_rate_msg(frm) {
    if (frm.doc.currency == "") {
        frm.set_value("currency", frm.doc.to_currency);
    }
    frm.set_df_property("exchange_rate", "description", `1 ${(frm.doc.currency == "") ? frm.doc.to_currency : frm.doc.currency} = [?] ${frm.doc.to_currency}`);
}

/* Dialog for payment entry */
function doubtful_debtors_dialog(frm, title, action_label, is_doubtful_debt, is_written_off) {
    let donors_list = []
    let idx_list;

    frappe.call({
        method: "akf_accounts.akf_accounts.doctype.donation.donation.get_donors_list",
        async: false,
        args: {
            donation_id: frm.doc.name,
            is_doubtful_debt: is_doubtful_debt,
            is_written_off: is_written_off,
            is_payment_entry: false
        },
        callback: function (r) {
            let data = r.message;
            // console.log(data);
            donors_list = data['donors_list'];
            idx_list = data['idx_list'];
        }
    });

    let d = new frappe.ui.Dialog({
        title: `${title} Details`,
        fields: [
            {
                label: '',
                fieldname: 'donor_section',
                fieldtype: 'Section Break',
                options: "",
                reqd: 0
            },
            {
                label: 'Donor ID',
                fieldname: 'donor_id',
                fieldtype: 'Link',
                options: "Donor",
                reqd: 1,
                get_query() {
                    return {
                        filters: {
                            name: ["in", donors_list],
                        }
                    }
                },
                onchange: function (val) {
                    let donor_id = d.fields_dict.donor_id.value;

                    if (donor_id in idx_list) {
                        d.fields_dict.serial_no.df.options = idx_list[donor_id];
                        d.fields_dict.serial_no.refresh();
                    }
                }
            },
            {
                label: 'Donation Amount.',
                fieldname: 'donation_amount',
                fieldtype: 'Currency',
                options: `currency`,
                default: 0,
                reqd: 0,
                read_only: 1,
                onchange: function (val) {
                    // let donor_id = d.fields_dict.donor_id.value;
                    // console.log(donor_id)
                }
            },
            {
                label: '',
                fieldname: 'col_break',
                fieldtype: 'Column Break',
                options: "",
                reqd: 0
            },
            {
                label: 'Serial No.',
                fieldname: 'serial_no',
                fieldtype: 'Select',
                options: "",
                reqd: 1,
                onchange: function (val) {
                    let donor_id = d.fields_dict.donor_id.value;
                    let serial_no = d.fields_dict.serial_no.value;
                    if (donor_id != null && serial_no != null) {
                        frappe.call({
                            method: "akf_accounts.akf_accounts.doctype.donation.donation.get_donation_details",
                            args: {
                                filters: { "name": frm.doc.name, "donor_id": donor_id, "idx": serial_no },
                            },
                            callback: function (r) {
                                const data = r.message;
                                // console.log(data);
                                d.fields_dict.donation_amount.value = data.outstanding_amount;
                                d.fields_dict.donation_amount.refresh();
                                d.fields_dict.doubtful_amount.value = data.doubtful_debt_amount;
                                d.fields_dict.doubtful_amount.refresh();
                                d.fields_dict.bad_debt_expense.value = data.bad_debt_expense;
                                d.fields_dict.bad_debt_expense.refresh();
                                d.fields_dict.provision_doubtful_debt.value = data.provision_doubtful_debt;
                                d.fields_dict.provision_doubtful_debt.refresh();

                            }
                        })
                    }
                }
            },

            {
                label: 'Doubtful Amount',
                fieldname: 'doubtful_amount',
                fieldtype: 'Currency',
                options: `currency`,
                default: 0,
                reqd: 1,
                onchange: function (val) {
                    let donation_amount = d.fields_dict.donation_amount.value;
                    let doubtful_amount = d.fields_dict.doubtful_amount.value;
                    
                    description_msg = ""
                    if(doubtful_amount > donation_amount){
                        description_msg = "<small style='color: red;'>Doubtful amount should be less than Donation Amount.<small>"
                    }else if(doubtful_amount<=0){
                        description_msg = "<small style='color: red;'>Doubtful amount should be greater than zero.<small>" 
                    }
                    d.fields_dict.doubtful_amount.df.description = description_msg
                    d.fields_dict.doubtful_amount.refresh();
                }
            },
            {
                label: 'Accounts Detail',
                fieldname: 'accounts_section',
                fieldtype: 'Section Break',
                options: "",
                reqd: 0,
            },
            {
                label: 'Bad Debt Expense',
                fieldname: 'bad_debt_expense',
                fieldtype: 'Link',
                options: "Account",
                reqd: 1,
                get_query() {
                    // let mode_of_payment = d.fields_dict.mode_of_payment.value;
                    return {
                        filters: {
                            disabled: 0,
                            is_group: 0,
                            account_type: "Receivable",
                            account_name: ["like", "%Bad%"],
                            company: frm.doc.company,
                            account_currency: frm.doc.currency
                        }
                    }
                }
            },
            {
                label: '',
                fieldname: 'col_break',
                fieldtype: 'Column Break',
                options: "",
                reqd: 0
            },
            {
                label: 'Provision Doubtful Debt',
                fieldname: 'provision_doubtful_debt',
                fieldtype: 'Link',
                options: "Account",
                reqd: 1,
                get_query() {
                    // let mode_of_payment = d.fields_dict.mode_of_payment.value;
                    return {
                        filters: {
                            disabled: 0,
                            is_group: 0,
                            account_type: "Receivable",
                            account_name: ["like", "%Doubt%"],
                            company: frm.doc.company,
                            account_currency: frm.doc.currency
                        }
                    }
                }
            },
        ],
        size: 'small', // small, large, extra-large 
        primary_action_label: action_label,
        primary_action(values) {
            console.log(values);
            if (values.doubtful_amount>0 && values.doubtful_amount <= values.donation_amount) {
                const method = is_doubtful_debt?"provision_doubtful_debt": "bad_debt_written_off";
                frm.call(method, { values: values }).then((r)=>{
                    d.hide();
                    frm.refresh();
                });
            }
        }
    });
    d.show();
}

/* Dialog for payment entry */
function pledge_payment_entry(frm) {
    let donors_list = []
    let idx_list;
    frappe.call({
        method: "akf_accounts.akf_accounts.doctype.donation.donation.get_donors_list",
        async: false,
        args: {
            donation_id: frm.doc.name,
            is_doubtful_debt: false, 
            is_written_off:false,
            is_payment_entry: true
        },
        callback: function (r) {
            let data = r.message;
            // console.log(data);
            donors_list = data['donors_list'];
            idx_list = data['idx_list'];
        }
    });
    
    let d = new frappe.ui.Dialog({
        title: 'Payment Details',
        fields: [
            {
                label: '',
                fieldname: 'donor_section',
                fieldtype: 'Section Break',
                options: "",
                reqd: 0
            },
            {
                label: 'Donor ID',
                fieldname: 'donor_id',
                fieldtype: 'Link',
                options: "Donor",
                reqd: 1,
                get_query() {
                    return {
                        filters: {
                            name: ["in", donors_list],
                        }
                    }
                },
                onchange: function (val) {
                    let donor_id = d.fields_dict.donor_id.value;

                    if (donor_id in idx_list) {
                        d.fields_dict.serial_no.df.options = idx_list[donor_id];
                        d.fields_dict.serial_no.refresh();
                    }
                }
            },
            {
                label: 'Outstanding Amount.',
                fieldname: 'outstanding_amount',
                fieldtype: 'Currency',
                options: "currency",
                default: 0,
                reqd: 0,
                read_only: 1,
                onchange: function (val) {
                    // let donor_id = d.fields_dict.donor_id.value;
                    // console.log(donor_id)
                }
            },
            {
                label: 'Doubtful Debt Amount.',
                fieldname: 'doubtful_debt_amount',
                fieldtype: 'Currency',
                options: "currency",
                default: 0,
                reqd: 0,
                read_only: 1,
                onchange: function (val) {
                    // let donor_id = d.fields_dict.donor_id.value;
                    // console.log(donor_id)
                }
            },
            {
                label: 'Remaining Amount.',
                fieldname: 'remaining_amount',
                fieldtype: 'Currency',
                options: "currency",
                default: 0,
                reqd: 0,
                read_only: 1,
                onchange: function (val) {
                    // let donor_id = d.fields_dict.donor_id.value;
                    // console.log(donor_id)
                }
            },
            {
                label: '',
                fieldname: 'col_break',
                fieldtype: 'Column Break',
                options: "",
                reqd: 0
            },
            {
                label: 'Serial No.',
                fieldname: 'serial_no',
                fieldtype: 'Select',
                options: "",
                reqd: 1,
                onchange: function (val) {
                    let donor_id = d.fields_dict.donor_id.value;
                    let serial_no = d.fields_dict.serial_no.value;
                    if (donor_id != null && serial_no != null) {
                        frappe.call({
                            method: "akf_accounts.akf_accounts.doctype.donation.donation.get_outstanding",
                            args: {
                                filters: { "name": frm.doc.name, "donor_id": donor_id, "idx": serial_no },
                            },
                            callback: function (r) {
                                const data = r.message;
                                d.fields_dict.outstanding_amount.value = data.outstanding_amount;
                                d.fields_dict.outstanding_amount.refresh();

                                d.fields_dict.doubtful_debt_amount.value = data.doubtful_debt_amount;
                                d.fields_dict.doubtful_debt_amount.refresh();

                                d.fields_dict.remaining_amount.value = data.remaining_amount;
                                d.fields_dict.remaining_amount.refresh();
                                

                            }
                        })
                    }
                }
            },

            {
                label: 'Paid Amount',
                fieldname: 'paid_amount',
                fieldtype: 'Currency',
                options: "currency",
                default: 0,
                reqd: 1,
                onchange: function (val) {
                    let remaining_amount = d.fields_dict.remaining_amount.value;
                    let paid_amount = d.fields_dict.paid_amount.value;
                    if (paid_amount > remaining_amount) {
                        // frappe.msgprint("Paid amount must be less than or equal to remaining amount!");
                        d.fields_dict.paid_amount.df.options = `<b style="color: red;">Paid amount is exceeding remaining amount.<b>`;
                        d.fields_dict.paid_amount.refresh();
                    }
                }
            },
            {
                label: 'Accounts Detail',
                fieldname: 'accounts_section',
                fieldtype: 'Section Break',
                options: "",
                reqd: 0,
            },
            {
                label: 'Mode of Payment',
                fieldname: 'mode_of_payment',
                fieldtype: 'Link',
                options: "Mode of Payment",
                reqd: 1,
                onchange: function (value) {
                    // console.log(d.fields_dict)
                    d.fields_dict.cheque_reference_no.refresh();
                    let mode_of_payment = d.fields_dict.mode_of_payment.value;
                    if (mode_of_payment == "Cash") {
                        d.fields_dict.cheque_reference_no.value = ""
                        d.fields_dict.cheque_reference_date.value = ""
                        d.fields_dict.cheque_reference_no.df.value = "";
                        d.fields_dict.cheque_reference_date.df.value = "";
                        d.fields_dict.cheque_reference_no.df.read_only = 1;
                        d.fields_dict.cheque_reference_date.df.read_only = 1;
                        d.fields_dict.cheque_reference_no.df.reqd = 0;
                        d.fields_dict.cheque_reference_date.df.reqd = 0;
                    } else {
                        d.fields_dict.cheque_reference_no.df.read_only = 0;
                        d.fields_dict.cheque_reference_date.df.read_only = 0;
                        d.fields_dict.cheque_reference_no.df.reqd = 1;
                        d.fields_dict.cheque_reference_date.df.reqd = 1;
                    }
                    erpnext.accounts.pos.get_payment_mode_account(frm, mode_of_payment, function (account) {
                        d.fields_dict.account_paid_to.value = account

                    });

                    d.fields_dict.account_paid_to.refresh();
                    d.fields_dict.cheque_reference_no.refresh();
                    d.fields_dict.cheque_reference_date.refresh();

                    if (mode_of_payment == "") {
                        d.fields_dict.account_paid_to.value = null;
                        d.fields_dict.account_paid_to.refresh();
                    }
                }
            },
            {
                label: 'Account Paid To',
                fieldname: 'account_paid_to',
                fieldtype: 'Link',
                options: "Account",
                reqd: 1,
                get_query() {
                    let mode_of_payment = d.fields_dict.mode_of_payment.value;
                    let account_type = mode_of_payment == "Cash" ? "Cash" : "Bank";
                    return {
                        filters: {
                            is_group: 0,
                            company: frm.doc.company,
                            account_type: account_type
                        }
                    }
                }
            },

            {
                label: 'Transaction Detail',
                fieldname: 'transaction_section',
                fieldtype: 'Section Break',
                options: "",
            },
            {
                label: 'Cheque/Reference No',
                fieldname: 'cheque_reference_no',
                fieldtype: 'Data',
                options: "",
                reqd: 1,
            },
            {
                label: 'Cheque/Reference Date',
                fieldname: 'cheque_reference_date',
                fieldtype: 'Date',
                options: "",
                default: "",
                reqd: 1,
            },
        ],
        size: 'small', // small, large, extra-large 
        primary_action_label: 'Create Payment Entry',
        primary_action(values) {
            if (values.paid_amount > values.remaining_amount) {
                d.fields_dict.paid_amount.df.options = `<b style="color: red;">Paid amount is exceeding remaining amount.<b>`;
                d.fields_dict.paid_amount.refresh();
            }
            else if (values) {
                let paid = values.paid_amount == values.outstanding_amount ? 1 : 0;
                let outstanding_amount = values.paid_amount <= values.outstanding_amount ? (values.outstanding_amount - values.paid_amount) : 0;
                values['paid'] = paid;
                values['outstanding_amount'] = outstanding_amount;
                frappe.call({
                    method: "akf_accounts.akf_accounts.doctype.donation.donation.pledge_payment_entry",
                    args: {
                        doc: frm.doc,
                        values: values
                    },
                    callback: function (r) {
                        d.hide();
                        // frm.refresh_field("payment_detail");
                        frm.reload_doc();
                        // frappe.set_route("Form", "Payment Entry", r.message);
                    }
                });
            }
        }
    });
    d.show();
}

function credit_note_return(frm) {
    if (frm.doc.is_return) { return };
    frappe.call({
        method: "akf_accounts.akf_accounts.doctype.donation.donation.get_total_donors_return",
        args: {
            'return_against': frm.doc.name
        },
        callback: function (r) {
            if (r.message == frm.doc.total_donors) {
                // pass
            } else {
                frm.add_custom_button(__('Return / Credit Note'), function () {
                    // make_sales_return() {
                    frappe.model.open_mapped_doc({
                        method: "akf_accounts.akf_accounts.doctype.donation.donation.make_donation_return",
                        frm: cur_frm
                    });
                    // }
                }, __("Create"));
                frm.page.set_inner_btn_group_as_primary(__('Create'));
            }
        }
    });
}

function return_payment_entry(frm) {
    frappe.call({
        method: "akf_accounts.akf_accounts.doctype.donation.donation.verify_payment_entry",
        args: {
            'doctype': 'Payment Entry Reference',
            'reference_name': frm.doc.name,
            'fieldname': 'name'
        },
        callback: function (r) {
            if (Object.keys(r.message).length == 0) {
                // code snippet
                frm.add_custom_button(__('Payment Entry'), function () {
                    frappe.call({
                        method: "akf_accounts.akf_accounts.doctype.donation.donation.return_payment_entry",
                        args: {
                            doc: frm.doc,
                        },
                        callback: function (r) {
                            frm.reload_doc();
                            // frappe.set_route("Form", "Payment Entry", r.message);
                        }
                    });
                }, __("Create"));
                frm.page.set_inner_btn_group_as_primary(__('Create'));
            }
        }
    });
}

function showHideModeOfPaymentForSingleRow(frm, row) {
    const flag = frm.doc.contribution_type == 'Pledge' ? 1 : 0;
    // console.log("flag: ", flag);
    frm.set_df_property('payment_detail', 'read_only', flag, frm.doc.name, 'mode_of_payment', row.name);
}

function fill_mode_of_payment_and_account(frm, row) {

    const donor_identity = frm.doc.donor_identity;

    function validate_mode_of_payment_and_account_paid_to() {
        const mode_of_payment = frm.doc.mode_of_payment;
        const account_paid_to = frm.doc.account_paid_to;
        if (mode_of_payment == "" || mode_of_payment == undefined) {
            frappe.throw(`Please select mode of payment`);
        }
        if (account_paid_to == "" || account_paid_to == undefined) {
            frappe.throw(`Please select account paid to`);
        }
    }
    let readOnly = 0;
    if (donor_identity == "Merchant - Unknown" || donor_identity == "Merchant - Known") {
        validate_mode_of_payment_and_account_paid_to();
        row.mode_of_payment = frm.doc.mode_of_payment;
        row.account_paid_to = frm.doc.account_paid_to;
        readOnly = 1;
    }
    frm.set_df_property('payment_detail', 'read_only', readOnly, frm.doc.name, 'mode_of_payment', row.name);
    frm.set_df_property('payment_detail', 'read_only', readOnly, frm.doc.name, 'account_paid_to', row.name);
}

function toggleModeOfPaymentRowWise(frm) {
    // Iterate through each row in the child table
    if (frm.doc.docstatus > 0) { return }
    frm.doc.payment_detail.forEach((row) => {
        if (frm.doc.contribution_type == 'Pledge') { // Replace with your condition
            frm.set_df_property('payment_detail', 'read_only', 1, frm.doc.name, 'mode_of_payment', row.name);
        } else {
            frm.set_df_property('payment_detail', 'read_only', 0, frm.doc.name, 'mode_of_payment', row.name);
        }
    });
    // Refresh the child table to apply the changes
    frm.refresh_field('payment_detail');
}

// new changes