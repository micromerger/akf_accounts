frappe.ui.form.on('Stock Entry', {
    refresh: function (frm) {
        frm.remove_custom_button('Material Request', __("Get Items From"));
        frm.add_custom_button(__('Material Request'), function () {
            const allowed_request_types = ["", "Material Transfer", "Material Issue", "Customer Provided"];
            const depends_on_condition = "eval:doc.material_request_type==='Customer Provided'";
            const d = erpnext.utils.map_current_doc({
                method: "erpnext.stock.doctype.material_request.material_request.make_stock_entry",
                source_doctype: "Material Request",
                target: frm,
                date_field: "schedule_date",
                setters: [
                    // {
                    //     fieldtype: 'Select',
                    //     label: __('Purpose'),
                    //     options: allowed_request_types.join("\n"),
                    //     fieldname: 'material_request_type',
                    //     default: "",
                    //     mandatory: 1,
                    //     hidden: 1,
                    //     change() {
                    //         if (this.value === 'Customer Provided') {
                    //             d.dialog.get_field("customer").set_focus();
                    //         }
                    //     },
                    // },
                    // {
                    //     fieldtype: 'Link',
                    //     label: __('Customer'),
                    //     options: 'Customer',
                    //     fieldname: 'customer',
                    //     depends_on: depends_on_condition,
                    //     mandatory_depends_on: depends_on_condition,
                    // },
                    {
                        fieldtype: 'Data',
                        label: __('Title'),
                        options: '',
                        fieldname: 'title',
                        hidden: 1
                    },

                ],

                get_query_filters: {
                        docstatus: 1,
                        // material_request_type: ["in", allowed_request_types],
                        status: ["not in", ["Transferred", "Issued", "Cancelled", "Stopped", "Draft"]]
                    }
            })
        }, __("Get Items From"));
    }
});