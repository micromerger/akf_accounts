let phone_regix=null;
frappe.treeview_settings["Donor"] = {
    get_tree_nodes: 'akf_accounts.akf_accounts.doctype.donor.donor_tree.get_children',
    add_tree_node: 'akf_accounts.akf_accounts.doctype.donor.donor_tree.add_node',
    filters: [
        {
            fieldname: "donor",
            fieldtype: "Link",
            options: "Donor",
            label: __("Donor"),
            get_query: function () {
                return {
                    filters: [["Donor", 'is_group', '=', 1]]
                };
            }
        },
    ],
    breadcrumb: "Setup",
    title: __("Chart of Donors"),
    root_label: "All Donors",
    get_tree_root: true,
    menu_items: [
        {
            label: __("New Donor"),
            action: function () {
                frappe.new_doc("Donor", true);
            },
            // condition: 'frappe.boot.user.can_create.indexOf("Company") !== -1'
        }
    ],
    ignore_fields: ["parent_donor", "naming_series"],
    fields: [
        {
            fieldtype: 'Check',
            fieldname: 'is_group',
            label: __('Is Group'),
            reqd: false,
        },
        {
            fieldtype: 'Column Break',
            fieldname: 'column_break_01',
            label: __(''),
        },
        {
            fieldtype: 'Link',
            fieldname: 'donor_type',
            label: __('Donor Type'),
            options: "Donor Type",
            reqd: true,
        },
        {
            fieldtype: 'Column Break',
            fieldname: 'column_break_01',
            label: __(''),
        },
        {
            fieldtype: 'Data',
            fieldname: 'donor_name',
            label: __('Donor Name'),
            reqd: true,
        },
        {
            fieldtype: 'Section Break',
            fieldname: 'column_break_01',
            label: __(''),
        },
        {
            fieldtype: 'Data',
            fieldname: 'email',
            label: __('Email'),
            options: "email",
            reqd: true,
        },
        {
            fieldtype: 'Column Break',
            fieldname: 'column_break_02',
            label: __(''),
        },
        {
            fieldtype: 'Link',
            fieldname: 'country',
            label: __('Country'),
            options: "Country",
            reqd: true,
            onchange: function () {
                let country = this.get_value();
                if (!country) return
                frappe.call({
                    method: "frappe.client.get_value",
                    async: false,
                    args: {
                        doctype: 'Country',
                        fieldname: ['custom_dial_code', 'custom_phone_mask', 'custom_phone_regex'],
                        filters: { 'name': country }
                    },
                    callback: function (r2) {
                        let data = r2.message;
                        phone_regix = data.custom_phone_regex;
                        // Apply input mask to contact_no field
                        const _mask_ = `${data.custom_dial_code}${data.custom_phone_mask}`
                        setTimeout(() => {
                            $('input[data-fieldname="contact_no"]').inputmask(_mask_);
                        }, 100);
                    }
                });
            }
        },
        {
            fieldtype: 'Data',
            fieldname: 'contact_no',
            label: __('Contact No'),
            options: "phone",
            reqd: true,
            onchange: function(){
                let contact_no = this.get_value();
                if(internationalPhoneValidation(contact_no, phone_regix)){
                    console.log('valid number');
                }else{
                    console.log('not valid number');
                }
                
                
            }
        },
    ],
    onload: function (treeview) {
        treeview.make_tree();
    },
    toolbar: [
        // {
        // 	label:__("Add Child"),
        // 	condition: function(node) {
        // 		return frappe.boot.user.can_create.indexOf("Donor") !== -1
        // 			&& (!frappe.treeview_settings['Donor'].treeview.page.fields_dict.root_company.get_value()
        // 			|| frappe.flags.ignore_root_company_validation)
        // 			&& node.expandable && !node.hide_add;
        // 	},
        // 	click: function() {
        // 		var me = frappe.views.trees['Donor'];
        // 		me.new_node();
        // 	},
        // 	btnClass: "hidden-xs"
        // },
        // {
        // 	condition: function(node) {
        // 		return !node.root && frappe.boot.user.can_read.indexOf("GL Entry") !== -1
        // 	},
        // 	label: __("View Ledger"),
        // 	click: function(node, btn) {
        // 		frappe.route_options = {
        // 			"account": node.label,
        // 			"from_date": erpnext.utils.get_fiscal_year(frappe.datetime.get_today(), true)[1],
        // 			"to_date": erpnext.utils.get_fiscal_year(frappe.datetime.get_today(), true)[2],
        // 			"company": frappe.treeview_settings['Account'].treeview.page.fields_dict.company.get_value()
        // 		};
        // 		frappe.set_route("query-report", "General Ledger");
        // 	},
        // 	btnClass: "hidden-xs"
        // }
    ],
    extend_toolbar: true
};

function internationalPhoneValidation(phone, phone_regix) {
    console.log(phone,' ',phone_regix);
    var pattern = new RegExp(phone_regix);
    const matching = phone.match(pattern);
    // if (!(phone.match(pattern)) || phone.length != phone_mask.length) {
    if(matching==null){
		return false;
    } else {
		return true;
    }
}