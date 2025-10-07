// function make_dimensions_modal(frm){
//     /*frappe.db.get_value('Company', frm.doc.company, 'custom_enable_accounting_dimensions_dialog')
//     .then(r => {
//         const enable_accounting_dimensions = r.message.custom_enable_accounting_dimensions_dialog; // Open
//         if (enable_accounting_dimensions && frm.doc.docstatus == 0) {
//             frm.add_custom_button(__('Donation'), () => get_donations(frm),
//                 __("Get Balances"));
//         }
//     });*/
//     frm.add_custom_button(__('Donation'), () => get_donations(frm), __("Get Balances"));
// };

// events.get_donationsp
function get_donations(frm) {
    /*if(!["", undefined].includes(frm.doc.from_cost_center)){
        frm.doc.cost_center = frm.doc.from_cost_center;
    }
    if(["", undefined].includes(frm.doc.cost_center)){
        frappe.throw("Please select cost-center to proceed.");
        return;
    }*/

    const d = new frappe.ui.Dialog({
        title: __("Accounting Dimensions"),
        fields: [
            {
                label: __("Company"),
                fieldname: "company",
                fieldtype: "Link",
                options: "Company",
                reqd: 1,
                read_only: 1,
                default: frappe.boot.sysdefaults.company
                // default: "Alkhidmat Foundation Pakistan"
            },
            {
                label: __("Fund Class"),
                fieldname: "fund_class",
                fieldtype: "Link",
                options: "Fund Class",
                default: frm.doc.name,
                reqd: 1,
                read_only: 1,
                onchange: function () {
                    // Clear cost center when company changes
                    // d.set_value('cost_center', '');
                }
                /* read_only: ["", undefined].includes(frm.doc.project)?0:1,
                get_query(){
                    let service_area = d.fields_dict.service_area.value;
                    return{
                        filters:{
                            company: frm.doc.company,
                            custom_service_area: service_area
                        }
                    }
                }*/
            },
            // {
            //     label: __(""),
            //     fieldname: "col_break",
            //     fieldtype: "Column Break",
            // },
            {
                label: __("Service Area"),
                fieldname: "service_area",
                fieldtype: "Link",
                options: "Service Area",
                default: frm.doc.service_area,
                reqd: 1,
                read_only: 1
                /*get_query(){
                    return{
                        filters:{
                            disabled: 0
                        }
                    }
                }*/
            },
            // {
            //     label: __(""),
            //     fieldname: "col_break",
            //     fieldtype: "Column Break",
            // },
            {
                label: __("Subservice Area"),
                fieldname: "subservice_area",
                fieldtype: "Link",
                options: "Subservice Area",
                default: frm.doc.subservice_area,
                reqd: 1,
                read_only: 1
                /*get_query(){
                    let service_area = d.fields_dict.service_area.value;
                    return{
                        filters:{
                            service_area: service_area
                        }
                    }
                }*/
            },
            // {
            //     label: __(""),
            //     fieldname: "col_break",
            //     fieldtype: "Column Break",
            // },
            {
                label: __("Product"),
                fieldname: "product",
                fieldtype: "Link",
                options: "Product",
                default: frm.doc.product,
                reqd: 1,
                read_only: 1,
                /*get_query(){
                    let subservice_area = d.fields_dict.subservice_area.value;
                    return{
                        filters:{
                            subservice_area: subservice_area
                        }
                    }
                }*/
            },

            {
                label: __(""),
                fieldname: "col_break",
                fieldtype: "Column Break",
            },

            // {
            //     label: __(""),
            //     fieldname: "section_donor_balance1",
            //     fieldtype: "Section Break",
            // },  
            {
                label: __("Cost Center"),
                fieldname: "cost_center",
                fieldtype: "Link",
                options: "Cost Center",
                reqd: 1,
                get_query() {
                    let company = d.fields_dict.company.value;
                    return {
                        filters: {
                            company: company
                        }
                    }
                }
            },
            // {
            //     label: __(""),
            //     fieldname: "col_break",
            //     fieldtype: "Column Break",
            // },
            {
                label: __("Donor Type"),
                fieldname: "donor_type",
                fieldtype: "Link",
                options: "Donor Type",
                reqd: 0,
            },
            // {
            //     label: __(""),
            //     fieldname: "col_break",
            //     fieldtype: "Column Break",
            // },
            {
                label: __("Donor Desk"),
                fieldname: "donor_desk",
                fieldtype: "Link",
                options: "Donor Desk",
                reqd: 0
            },
            // {
            //     label: __(""),
            //     fieldname: "col_break",
            //     fieldtype: "Column Break",
            // },
            {
                label: __("Intention"),
                fieldname: "intention",
                fieldtype: "Link",
                options: "Donation Type",
                reqd: 0
            },
            // {
            //     label: __(""),
            //     fieldname: "col_break",
            //     fieldtype: "Column Break",
            // },
            {
                label: __("Transaction Type"),
                fieldname: "transaction_type",
                fieldtype: "Link",
                options: "Transaction Type",
                reqd: 0
            },
            {
                label: __(""),
                fieldname: "col_break",
                fieldtype: "Column Break",
            },
            {
                label: __("Estimated Cost"),
                fieldname: "estimated_costing",
                fieldtype: "Currency",
                reqd: 1,
                onchange: function () {
                    const amount = d.get_value('estimated_costing');
                    if (amount) {
                        // Find and select the donor balance that matches the amount
                        const donorBalance = d.fields_dict.donor_balance.df.data;
                        if (donorBalance && donorBalance.length > 0) {
                            donorBalance.forEach(row => {
                                row.__checked = (row.balance == amount);
                            });
                            d.fields_dict.donor_balance.grid.refresh();
                        }
                    }
                }
            },
            // {
            //     label: __(""),
            //     fieldname: "col_break2",
            //     fieldtype: "Column Break",
            // },
            {
                label: __("Expected Start Date"),
                fieldname: "expected_start_date",
                fieldtype: "Date",
                reqd: 1,
                default: frappe.datetime.get_today()
            },

            {
                label: __("Get Balance"),
                fieldname: "get_balance",
                fieldtype: "Button",
                hidden: 0,
                options: ``,
                click() {
                    const filters = {
                        "company": d.fields_dict.company.value,
                        "fund_class": d.fields_dict.fund_class.value,
                        "service_area": d.fields_dict.service_area.value,
                        "subservice_area": d.fields_dict.subservice_area.value,
                        "product": d.fields_dict.product.value,
                        "cost_center": d.fields_dict.cost_center.value,
                        "doctype": frm.doc.doctype,
                        "amount": d.fields_dict.estimated_costing.value
                    }
                    let msg = "<p></p>";
                    let data = [];

                    // Check if estimated cost is zero
                    if (parseFloat(d.fields_dict.estimated_costing.value) === 0) {
                        msg = `<b style="color: red;">Estimated Cost cannot be zero</b>`;
                        d.fields_dict.html_message.df.options = msg;
                        d.fields_dict.html_message.refresh();
                        return;
                    }

                    const nofilters = get_validate_filters(filters);

                    if (!["", null].includes(d.fields_dict.donor_type.value)) filters.donor_type = d.fields_dict.donor_type.value;
                    if (!["", null].includes(d.fields_dict.donor_desk.value)) filters.donor_desk = d.fields_dict.donor_desk.value;
                    if (!["", null].includes(d.fields_dict.intention.value)) filters.intention = d.fields_dict.intention.value;
                    if (!["", null].includes(d.fields_dict.transaction_type.value)) filters.transaction_type = d.fields_dict.transaction_type.value;

                    if (nofilters.notFound) {
                        // Special message for Estimated Cost field
                        if (nofilters.fieldname === "amount") {
                            msg = `<b style="color: red;">Please enter amount in Estimated Cost</b>`;
                        } else {
                            msg = `<b style="color: red;">Please select ${nofilters.fieldname}</b>`;
                        }
                    } else {
                        const response = get_financial_stats(filters);

                        if (response.length > 0) {
                            data = response;
                        } else {
                            data = [];
                            msg = `<b style="color: red;">No balance found against these dimension.</b>`;
                        }
                    }
                    d.fields_dict.donor_balance.df.data = data;
                    d.fields_dict.donor_balance.grid.refresh();

                    d.fields_dict.html_message.df.options = msg;
                    d.fields_dict.html_message.refresh();
                }
            },
            {
                label: __(""),
                fieldname: "section_donor_balance1",
                fieldtype: "Section Break",
            },
            {
                fieldname: "donor_balance",
                fieldtype: "Table",
                label: __("Donor Balance"),
                cannot_add_rows: true,
                in_place_edit: false,
                // data: [{'donation': 1, 'donor': 2, 'balance': 1000}],
                reqd: 1,
                fields: [
                    {
                        fieldname: "cost_center",
                        label: __("Cost Center"),
                        fieldtype: "Link",
                        options: "Cost Center",
                        in_list_view: 1,
                        read_only: 1,
                    },
                    {
                        fieldname: "account",
                        label: __("Account"),
                        fieldtype: "Link",
                        options: "Account",
                        in_list_view: 1,
                        read_only: 1,
                    },
                    {
                        fieldname: "donor",
                        label: __("Donor"),
                        fieldtype: "Link",
                        options: "Donor",
                        in_list_view: 1,
                        read_only: 1,
                    },
                    {
                        fieldname: "donor_name",
                        label: __("Donor Name"),
                        fieldtype: "Data",
                        options: "",
                        in_list_view: 1,
                        read_only: 1,
                    },
                    {
                        fieldname: "temporary_account",
                        label: __("Temporary Account"),
                        fieldtype: "Link",
                        options: "Account",
                        in_list_view: 0,
                        read_only: 1,
                    },
                    {
                        fieldname: "balance",
                        label: __("Balance"),
                        fieldtype: "Currency",
                        in_list_view: 1,
                        read_only: 1,
                    }
                ],
                /* on_add_row: (idx) => {
                  // idx = visible idx of the row starting from 1
                  // eg. set `log_type` as alternating IN/OUT in the table on row addition
                    let data_id = idx - 1;
                    let logs = dialog.fields_dict.logs;
                    let log_type = (data_id % 2) == 0 ? "IN" : "OUT";
      
                    logs.df.data[data_id].log_type = log_type;
                    logs.grid.refresh();
                }, */
            },

            {
                label: __(""),
                fieldname: "html_message",
                fieldtype: "HTML",
            },
        ],
        size: 'extra-large',
        primary_action: (values) => {
            // Check if estimated cost is zero
            if (parseFloat(values.estimated_costing) === 0) {
                d.fields_dict.html_message.df.options = `<b style="color: red;">Estimated Cost cannot be zero to initiate project</b>`;
                d.fields_dict.html_message.refresh();
                return;
            }

            const array = values.donor_balance;
            let details = [];

            let total_budget = 0;

            array.forEach(row => {
                if (row.__checked) {
                    // Add to total budget
                    total_budget += parseFloat(row.balance) || 0;
                    console.log(total_budget);

                    details.push({
                        "pd_account": row.account,

                        "pd_cost_center": row.cost_center,
                        "pd_fund_class": frm.doc.name,
                        "pd_service_area": values.service_area,
                        "pd_subservice_area": values.subservice_area,
                        "pd_product": values.product,
                        "pd_donor": row.donor,
                        "pd_donor_type": values.donor_type,
                        "pd_donor_desk": values.donor_desk,
                        "pd_intention": values.intention,
                        "pd_transaction_type": values.transaction_type,

                        "actual_balance": row.balance,
                        "custom_transfer_funds": values.estimated_costing,
                        "custom_funds_transfer": 0,
                        "encumbrance_project_account": row.encumbrance_project_account,
                        "encumbrance_material_request_account": row.encumbrance_material_request_account,
                        "encumbrance_purchase_order_account": row.encumbrance_purchase_order_account,
                        "amortise_designated_asset_fund_account": row.amortise_designated_asset_fund_account,
                        "amortise_inventory_fund_account": row.amortise_inventory_fund_account,
                    });
                }
            });
            // console.log(values.estimated_costing);
            // console.log(total_budget);
            // Check if estimated cost is greater than total budget
            if (parseFloat(values.estimated_costing) > total_budget) {
                d.fields_dict.html_message.df.options = `<b style="color: red;">Estimated Cost (${values.estimated_costing}) cannot be greater than total budget (${total_budget})</b>`;
                d.fields_dict.html_message.refresh();
                return;
            }

            if (details.length > 0) {
                // Create new project
                frappe.new_doc("Project", {
                    company: values.company,
                    project_name: values.fund_class,
                    fund_class: values.fund_class,
                    custom_service_area: values.service_area,
                    custom_subservice_area: values.subservice_area,
                    custom_product: values.product,
                    custom_donor_type: values.donor_type,
                    custom_donor_desk: values.donor_desk,
                    custom_donation_type: values.intention,
                    custom_transaction_type: values.transaction_type,
                    cost_center: values.cost_center,
                    // custom_program_details: details
                }, (doc) => {
                    // Log the created document
                    console.log("Created Project Document:", doc);
                    doc.expected_start_date = values.expected_start_date
                    doc.estimated_costing = values.estimated_costing
                    console.log("Project Document:", doc);

                    // Add program details to the document
                    doc.custom_program_details = details;
                    // Log after adding program details
                    console.log("Document after adding program details:", doc);
                    // // Save the document
                    // doc.save()
                    // Close the dialog
                    d.hide();
                    // Force a fresh form load
                    frappe.model.sync(doc);
                    // Show the project form
                    frappe.set_route("Form", "Project", doc.name);

                })
            } else {
                d.fields_dict.html_message.df.options = `<b style="color: red;">Please select a record to proceed.</b>`;
                d.fields_dict.html_message.refresh();
            }
        },
        primary_action_label: __("Initiate Project"),
    });
    // Set default date when dialog opens
    d.set_value('expected_start_date', frappe.datetime.get_today());
    d.show();

}

function get_validate_filters(filters) {
    var noFilters = false;
    var fieldname = '';
    for (const key in filters) {
        noFilters = ['', null].includes(filters[key]);
        if (noFilters) {
            fieldname = key;
            break;
        }
    }

    return {
        "notFound": noFilters,
        "fieldname": fieldname
    }
}

function get_financial_stats(filters) {
    let data = [];
    frappe.call({
        method: "akf_accounts.utils.fund_class_donor_balances.get_donor_balances",
        async: false,
        args: {
            filters: filters
        },
        callback: function (r) {
            data = r.message;
            console.log(data);
        }
    });
    return data
}


function accounting_ledger(frm) {
    if (!frm.is_new()) {
        frm.add_custom_button(__('Accounting Ledger'), function () {
            frappe.set_route("query-report", "General Ledger", { "fund_class": frm.doc.name });
        }, __("View"));
    }
}

function donor_balance_set_queries(frm) {
    const childkey = ("custom_program_details" in frm.doc) ? "custom_program_details" : "custom_program_details";
    frm.fields_dict[childkey].grid.get_field('pd_service_area').get_query = function (doc, cdt, cdn) {
        return {
            filters: {
                disabled: 0,
            }
        };
    }

    frm.fields_dict[childkey].grid.get_field('pd_subservice_area').get_query = function (doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        let ffilters = row.pd_service_area == undefined ? { service_area: ["!=", undefined] } : { service_area: row.pd_service_area };
        return {
            filters: ffilters
        };
    }

    frm.fields_dict[childkey].grid.get_field('pd_product').get_query = function (doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        let ffilters = row.pd_subservice_area == undefined ? { subservice_area: ["!=", undefined] } : { subservice_area: row.pd_subservice_area };
        return {
            filters: ffilters
        };
    };

    frm.fields_dict[childkey].grid.get_field('pd_project').get_query = function (doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        let service_area = row.pd_service_area == undefined ? ["!=", undefined] : row.pd_service_area;
        return {
            filters: {
                // company: frm.doc.company,
                custom_service_area: service_area,
                custom_allocation_check: 0
            }
        };
    };

    frm.fields_dict[childkey].grid.get_field('pd_donor').get_query = function (doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                status: "Active",
                default_currency: row.currency,
            }
        };
    };
}
