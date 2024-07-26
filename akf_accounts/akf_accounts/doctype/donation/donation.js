frappe.provide("erpnext.accounts");

const DI_LIST = ["Unknown", "Merchant"];

frappe.ui.form.on('Donation', {
    onload_post_render: function(frm) {
        frm.get_field("payment_detail").grid.set_multiple_add("pay_service_area");
        frm.refresh_field('payment_detail');
    },
    onload: function(frm) {
        erpnext.accounts.dimensions.setup_dimension_filters(frm, frm.doctype);
    },
    refresh: function (frm) {
        set_queries(frm);
        set_query_subservice_area(frm);
        set_custom_btns(frm);
    },
    donor_identity: function(frm){
        if(frm.doc.donor_identity=="Unknown" || frm.doc.donor_identity=="Merchant" || frm.doc.donor_identity=="Merchant - Known"){
            frm.set_value("contribution_type", "Donation");
            frm.set_df_property("contribution_type", "read_only", 1)
        }else{
            frm.set_value("contribution_type", "");
            frm.set_df_property("contribution_type", "read_only", 0)
        }
    },
    contribution_type: function(frm){
        frm.call("set_deduction_breakeven");
    },
    donation_type: function(frm){
        frm.call("set_deduction_breakeven");
    },
    company: function (frm) {
        // erpnext.accounts.dimensions.update_dimension(frm, frm.doctype);
        // frm.set_value('service_area', '');
        // frm.clear_table('deduction_breakeven');
    },
    subservice_area: function(frm){
    }
});

frappe.ui.form.on('Payment Detail', {
    donor_id: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        row.donor =  row.donor_id;
        // frm.call("set_deduction_breakeven");        
    },
    pay_service_area: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        row.program = row.pay_service_area;
        // frm.call("set_deduction_breakeven");        
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
    project: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if(row.pay_service_area!=undefined || row.pay_service_area!=""){
            frm.call("set_deduction_breakeven");
        }
    },
    mode_of_payment: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        // console.log(frm.doc.mode_of_payment);
        // console.log(frm.doc.mode_of_payment!=undefined);
        if(frm.doc.mode_of_payment!=undefined){
            erpnext.accounts.pos.get_payment_mode_account(frm, row.mode_of_payment, function(account){
                row.account_paid_to = account;
            });
        }else{
            row.transaction_no_cheque_no = '';
            row.account_paid_to = null;
        }
        frm.refresh_field("payment_detail");
	},
    donation_amount: function (frm, cdt, cdn) {
        frm.call("set_deduction_breakeven");
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
    payment_detail_remove: function(frm){
        frm.call("set_deduction_breakeven");
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

/* CUSTOM BUTTONS ON TOP OF DOCTYPE */
function set_custom_btns(frm) {

    if(frm.doc.docstatus==1){ 
        if(frm.doc.donor_identity == "Unknown" && frm.doc.contribution_type==="Donation"){
            frm.add_custom_button(__('Reverse Donor'), function () {
                let d = new frappe.ui.Dialog({
                    title: 'Known donor detail',
                    fields: [
                        {
                            label: 'Donor',
                            fieldname: 'donor',
                            fieldtype: 'Link',
                            options: "Donor",
                            reqd: 1,
                            get_query(){
                                return{
                                    filters:{
                                        donor_name: ["not in", ["Unknown Donor", "Merchant Known"]]
                                    }
                                }
                            }
                        },
                        {
                            label: 'Transaction No/ Cheque No',
                            fieldname: 'transaction_no_cheque_no',
                            fieldtype: 'Data',
                            options: "",
                            reqd: 1
                        }
                    ],
                    size: 'small', // small, large, extra-large 
                    primary_action_label: 'Submit',
                    primary_action(values) {
                        // console.log(values);
                        if(values){
                            frappe.call({
                                method: "akf_accounts.akf_accounts.doctype.donation.donation.set_unknown_to_known",
                                args:{
                                    name: frm.doc.name,
                                    values: values
                                },
                                callback: function(r){
                                    d.hide();
                                    frm.reload_doc()
                                }
                            });
                        }
                    }
                });
                d.show();
            });
        }
        frm.add_custom_button(__('Accounting Ledger'), function () {
            frappe.set_route("query-report", "General Ledger", {"voucher_no": frm.doc.name});
        }, __("View"));
        if(frm.doc.status!="Paid"){
            if(frm.doc.contribution_type == "Pledge"){
                frm.add_custom_button(__('Payment Entry'), function () {
                    let donors_list = []
                    let idx_list;
                    frappe.call({
                        method: "akf_accounts.akf_accounts.doctype.donation.donation.get_donors_list",
                        async: false,
                        args:{
                            donation_id: frm.doc.name,
                        },
                        callback: function(r){
                            /* 
                                return {
                                    "donors_list": donors_list,
                                    "idx_list": idx_list,
                                }
                            */
                            let data = r.message;
                            console.log(data);
                            donors_list = data['donors_list'];
                            idx_list = data['idx_list'];
                        }
                    });

                    let d = new frappe.ui.Dialog({
                        title: 'Payment Details',
                        fields: [
                            {
                                label: 'Donor ID',
                                fieldname: 'donor_id',
                                fieldtype: 'Link',
                                options: "Donor",
                                reqd: 1,
                                get_query(){
                                    // let mode_of_payment = d.fields_dict.mode_of_payment.value;
                                    // let account_type = mode_of_payment=="Cash"? "Cash": "Bank";
                                    return{
                                        filters: {
                                            name: ["in", donors_list],
                                        }
                                    }
                                },
                                onchange: function(val){
                                    let donor_id = d.fields_dict.donor_id.value;
                                    
                                    if(donor_id in idx_list){
                                        d.fields_dict.serial_no.df.options = idx_list[donor_id];
                                        d.fields_dict.serial_no.refresh();
                                    }
                                    let serial_no = d.fields_dict.serial_no.value;
                                    /* console.log(serial_no)
                                    if(serial_no!=null){
                                        frappe.call({
                                            method: "akf_accounts.akf_accounts.doctype.donation.donation.get_outstanding",
                                            args: {
                                                filters: {"name": frm.doc.name, "donor_id": donor_id, "idx": serial_no},
                                            },
                                            callback: function(r){
                                                console.log(r.message);
                                                d.fields_dict.outstanding_amount.value = r.message;
                                                d.fields_dict.outstanding_amount.refresh();
                                            }
                                        })
                                    } */
                                    
                                
                                }
                            },
                            {
                                label: 'Outstanding Amount.',
                                fieldname: 'outstanding_amount',
                                fieldtype: 'Currency',
                                options: "",
                                default: 0,
                                reqd: 0,
                                read_only: 1,
                                onchange: function(val){
                                    let donor_id = d.fields_dict.donor_id.value;
                                    console.log(donor_id)
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
                                onchange: function(val){
                                    let donor_id = d.fields_dict.donor_id.value;
                                    let serial_no = d.fields_dict.serial_no.value;
                                    if(donor_id!=null && serial_no!=null){
                                        frappe.call({
                                            method: "akf_accounts.akf_accounts.doctype.donation.donation.get_outstanding",
                                            args: {
                                                filters: {"name": frm.doc.name, "donor_id": donor_id, "idx": serial_no},
                                            },
                                            callback: function(r){
                                                console.log(r.message);
                                                d.fields_dict.outstanding_amount.value = r.message;
                                                d.fields_dict.outstanding_amount.refresh();
                                            }
                                        })
                                    }
                                }
                            },
                            
                            {
                                label: 'Paid Amount',
                                fieldname: 'paid_amount',
                                fieldtype: 'Currency',
                                options: "",
                                default: 0,
                                reqd: 1,
                                onchange: function(val){
                                    let outstanding_amount = d.fields_dict.outstanding_amount.value;
                                    let paid_amount = d.fields_dict.paid_amount.value;
                                    if(paid_amount>outstanding_amount){
                                        frappe.msgprint("Paid amount must be less than or equal to outstanding amount!")
                                    }
                                }
                            },
                            {
                                label: 'Accounts Detail',
                                fieldname: 'accounts_section',
                                fieldtype: 'Section Break',
                                options: "",
                                reqd: 0
                            },
                            {
                                label: 'Mode of Payment',
                                fieldname: 'mode_of_payment',
                                fieldtype: 'Link',
                                options: "Mode of Payment",
                                reqd: 1,
                                onchange: function(value){
                                    // console.log(d.fields_dict)
                                    d.fields_dict.cheque_reference_no.refresh();
                                    let mode_of_payment = d.fields_dict.mode_of_payment.value;
                                    if(mode_of_payment=="Cash"){
                                        d.fields_dict.cheque_reference_no.value = ""
                                        d.fields_dict.cheque_reference_date.value = ""
                                        d.fields_dict.cheque_reference_no.df.reqd = 0;
                                        d.fields_dict.cheque_reference_date.df.reqd = 0;
                                    }else{
                                        d.fields_dict.cheque_reference_no.df.reqd = 1;
                                        d.fields_dict.cheque_reference_date.df.reqd = 1;
                                    }
                                    
                                    d.fields_dict.cheque_reference_no.refresh();
                                    d.fields_dict.cheque_reference_date.refresh();

                                    if(mode_of_payment==""){
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
                                get_query(){
                                    let mode_of_payment = d.fields_dict.mode_of_payment.value;
                                    let account_type = mode_of_payment=="Cash"? "Cash": "Bank";
                                    return{
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
                                reqd: 0
                            },
                            {
                                label: 'Cheque/Reference No',
                                fieldname: 'cheque_reference_no',
                                fieldtype: 'Data',
                                options: "",
                                reqd: 1
                            },
                            {
                                label: 'Cheque/Reference Date',
                                fieldname: 'cheque_reference_date',
                                fieldtype: 'Date',
                                options: "",
                                default: "",
                                reqd: 1
                            },
                        ],
                        size: 'small', // small, large, extra-large 
                        primary_action_label: 'Create Payment Entry',
                        primary_action(values) {
                            if(values.paid_amount>values.outstanding_amount){
                                frappe.msgprint("Paid amount must be less than or equal to outstanding amount!")
                            }
                            else if(values){
                                let paid = values.paid_amount==values.outstanding_amount?1: 0;
                                let outstanding_amount = values.paid_amount<=values.outstanding_amount? (values.outstanding_amount-values.paid_amount): 0;
                                values['paid'] = paid;
                                values['outstanding_amount'] = outstanding_amount;
                                frappe.call({
                                    method: "akf_accounts.akf_accounts.doctype.donation.donation.pledge_payment_entry",
                                    args:{
                                        doc: frm.doc,
                                        values: values
                                    },
                                    callback: function(r){
                                        d.hide();
                                        frm.refresh_field("payment_detail");
                                        // frappe.set_route("Form", "Payment Entry", r.message);
                                    }
                                });
                            }
                        }
                    });
                    d.show();

                }, __("Create"));
            }
        }
    }
}
/* END CUSTOM BUTTONS ON TOP OF DOCTYPE */

/* APPLYING SET QUERIES */
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

function set_queries_payment_details(frm){
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
function set_query_donor_id(frm){
    frm.fields_dict['payment_detail'].grid.get_field('donor_id').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        
        if(frm.doc.donor_identity=="Unknown" || frm.doc.donor_identity=="Merchant"){
            let dlist = ["in", "Unknown Donor"];
            return {
                filters: {
                    donor_name: dlist,
                }
            };
        }else if(frm.doc.donor_identity=="Known"){
            let dlist = ["not in", "Unknown Donor"];
            return {
                filters: {
                    donor_name: dlist,
                }
            };
        }else if(frm.doc.donor_identity == "Merchant - Known"){
            let dlist = ["in", "Merchant Known"];
            return {
                filters: {
                    donor_name: dlist,
                }
            };
        }
        
    };
}
function set_query_subservice_area(frm){
    frm.fields_dict['payment_detail'].grid.get_field('pay_subservice_area').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                service_area: ["!=", ""],
                service_area: row.pay_service_area,
            }
        };
    };
}
// Payment Detail
function set_query_product(frm){
    frm.fields_dict['payment_detail'].grid.get_field('pay_product').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                subservice_area: ["!=", ""],
                subservice_area: row.pay_subservice_area,
            }
        };
    };
}
// Payment Detail
function set_query_account(frm){
    frm.fields_dict['payment_detail'].grid.get_field('account').get_query = function(doc, cdt, cdn) {
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
function set_query_project(frm){
    frm.fields_dict['payment_detail'].grid.get_field('project').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                company: frm.doc.company,
                custom_program: ["!=", ""],
                custom_program: row.pay_service_area,
                
            }
        };
    };
}

function set_query_equity_account(frm){
    frm.fields_dict['payment_detail'].grid.get_field('equity_account').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                company: ["!=", ""],
                company: frm.doc.company,
                root_type: "Equity",
            }
        };
    };
}

function set_query_receivable_account(frm){
    frm.fields_dict['payment_detail'].grid.get_field('receivable_account').get_query = function(doc, cdt, cdn) {
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

function set_query_account_paid_to(frm){
    frm.fields_dict['payment_detail'].grid.get_field('account_paid_to').get_query = function(doc, cdt, cdn) {
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
function set_query_mode_of_payment(frm){
    frm.fields_dict['payment_detail'].grid.get_field('mode_of_payment').get_query = function(doc, cdt, cdn) {
        return {
            filters: {
                enabled: 1,
            }
        };
    };
}
/* END APPLYING SET QUERIES */


 // if (frm.doc.custom_payment_status === "Paid") {
    //     frm.page.set_indicator('Paid', 'green');
    // } else {
    //     frm.page.set_indicator('Unpaid', 'red');
    // }