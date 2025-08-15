function get_funds(frm, transfer_to = "Project") {
    /*if(!["", undefined].includes(frm.doc.from_cost_center)){
        frm.doc.cost_center = frm.doc.from_cost_center;
    }
    if(["", undefined].includes(frm.doc.cost_center)){
        frappe.throw("Please select cost-center to proceed.");
        return;
    }*/

    let fields = [
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
        {
            label: __(""),
            fieldname: "col_break",
            fieldtype: "Column Break",
        },
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
        {
            label: __(""),
            fieldname: "col_break",
            fieldtype: "Column Break",
        },
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
        {
            label: __(""),
            fieldname: "col_break",
            fieldtype: "Column Break",
        },
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
        {
            label: __("Company"),
            fieldname: "company",
            fieldtype: "Link",
            options: "Company",
            reqd: 1,
            default: "Alkhidmat Foundation Pakistan"
        },
        {
            label: __(""),
            fieldname: "section_donor_balance1",
            fieldtype: "Section Break",
        },
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
        {
            label: __(""),
            fieldname: "col_break",
            fieldtype: "Column Break",
        },
        {
            label: __("Donor Desk"),
            fieldname: "donor_desk",
            fieldtype: "Link",
            options: "Donor Desk",
            reqd: 0,
            /*get_query(){
                let company = d.fields_dict.company.value;
                return{
                    filters:{
                        company: company
                    }
                }
            }*/
        },
        {
            label: __(""),
            fieldname: "col_break",
            fieldtype: "Column Break",
        },
        {
            label: __("Intention"),
            fieldname: "donation_type",
            fieldtype: "Link",
            options: "Donation Type",
            reqd: 0,
            /*get_query(){
                let company = d.fields_dict.company.value;
                return{
                    filters:{
                        company: company
                    }
                }
            }*/
        },
        {
            label: __(""),
            fieldname: "col_break",
            fieldtype: "Column Break",
        }, {
            label: __("Transfer Funds Cost"),
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
        {
            label: __(""),
            fieldname: "col_break2",
            fieldtype: "Column Break",
        }
    ];

    // Insert either Project or Fund Class field
    if (transfer_to === "Project") {
        fields.push({
            label: __("Project"),
            fieldname: "custom_project",
            fieldtype: "Link",
            options: "Project",
            reqd: 1,
            get_query: function () {
                return {
                    filters: {
                        fund_class: frm.doc.name,
                        status: ["!=", "Completed"]
                    }
                }
            }
        });
    } else {
        fields.push({
            label: __("Fund Class"),
            fieldname: "target_fund_class",
            fieldtype: "Link",
            options: "Fund Class",
            reqd: 1,
            get_query: function () {
                return {
                    filters: {
                        name: ["!=", frm.doc.name]
                    }
                }
            }
        });
    }

    // ... then add the rest of your fields (Get Balance, donor_balance, html_message, etc.) ...
    fields = fields.concat([
        {
            label: __("Get Balance"),
            fieldname: "get_balance",
            fieldtype: "Button",
            hidden: 0,
            options: ``,
            click() {
                const filters = {
                    "fund_class": d.fields_dict.fund_class.value,
                    "service_area": d.fields_dict.service_area.value,
                    "subservice_area": d.fields_dict.subservice_area.value,
                    "product": d.fields_dict.product.value,
                    "cost_center": d.fields_dict.cost_center.value,
                    "donor_desk": d.fields_dict.donor_desk.value,
                    "donation_type": d.fields_dict.donation_type.value,
                    "company": d.fields_dict.company.value,
                    "doctype": frm.doc.doctype,
                    "amount": d.fields_dict.estimated_costing.value
                    // "amount": get_consuming_amount(frm.doc)
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
    ]);

    // Now create the dialog with the correct fields
    const d = new frappe.ui.Dialog({
        title: __("Transfer Funds"),
        fields: fields,
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

                    details.push({
                        "pd_cost_center": row.cost_center,
                        "pd_account": row.account,
                        "pd_service_area": values.service_area,
                        "pd_subservice_area": values.subservice_area,
                        "pd_product": values.product,
                        "pd_donor": row.donor,
                        "donor_desk": values.donor_desk,
                        "donation_type": values.donation_type,
                        "pd_fund_class": frm.doc.name,
                        "actual_balance": row.balance,
                        "amount": values.estimated_costing,
                        "is_transferred": values.estimated_costing,
                        "encumbrance_project_account": row.encumbrance_project_account,
                        "encumbrance_material_request_account": row.encumbrance_material_request_account,
                        "encumbrance_purchase_order_account": row.encumbrance_purchase_order_account,
                        "amortise_designated_asset_fund_account": row.amortise_designated_asset_fund_account,
                        "amortise_inventory_fund_account": row.amortise_inventory_fund_account,
                    });
                }
            });

            // Check if estimated cost is greater than total budget
            if (parseFloat(values.estimated_costing) > total_budget) {
                d.fields_dict.html_message.df.options = `<b style="color: red;">Estimated Cost (${values.estimated_costing}) cannot be greater than total budget (${total_budget})</b>`;
                d.fields_dict.html_message.refresh();
                return;
            }

            if (transfer_to === "Fund Class") {
                // Set custom_project to empty string to avoid backend error
                values.custom_project = "";

                if (!values.target_fund_class) {
                    d.fields_dict.html_message.df.options = `<b style="color: red;">Please select a Fund Class to transfer funds.</b>`;
                    d.fields_dict.html_message.refresh();
                    return;
                }
                // Call backend with Fund Class as target
                frappe.call({
                    method: "akf_accounts.utils.encumbrance.enc_project.make_transfer_funds_gl_entries",
                    args: {
                        doc: values,
                        donor_balance: details,
                        transfer_to: "Fund Class"
                    },
                    callback: function (r) {
                        d.hide();
                        frm.reload_doc();
                    }
                });
            } else {
                if (!values.custom_project) {
                    d.fields_dict.html_message.df.options = `<b style="color: red;">Please select a Project to transfer funds.</b>`;
                    d.fields_dict.html_message.refresh();
                    return;
                }
                // Existing Project transfer logic
                frappe.call({
                    method: "akf_accounts.utils.encumbrance.enc_project.make_transfer_funds_gl_entries",
                    args: {
                        doc: values,
                        donor_balance: details,
                        transfer_to: "Project"
                    },
                    callback: function (r) {
                        d.hide();
                    }
                });
            }
        },
        primary_action_label: __("Submit"),
    });

    d.set_value('expected_start_date', frappe.datetime.get_today());
    d.show();
}
