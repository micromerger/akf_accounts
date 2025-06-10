function make_change_donor_dialog(frm){
    if (frm.doc.docstatus == 1 && frm.doc.custom_program_details.length>0) {
        frm.add_custom_button(__("Change Donor"),
            () =>{
                let fieldsObj = {};
                let donorslist = [];
                const program_details = frm.doc.custom_program_details;
                program_details.forEach(row =>{
                    fieldsObj = {
                        "name": frm.doc.name,
                        "posting_date": frm.doc.posting_date,
                        "service_area": row.pd_service_area,
                        "subservice_area": row.pd_subservice_area,
                        "product": row.pd_product,
                        "project": row.pd_project,
                        "cost_center": row.pd_cost_center,
                        "company": frm.doc.company,
                        "doctype": frm.doc.doctype,
                        "amount": 0,

                    };
                    donorslist.push(row.pd_donor)
                    // return;
                });
                const linkDocs = get_link_records_func(fieldsObj);
                let d = new frappe.ui.Dialog({
                    title: 'Change Donor',
                    fields: [
                        {
                            label: __("Service Area"),
                            fieldname: "service_area",
                            fieldtype: "Link",
                            options: "Service Area",
                            default: fieldsObj.service_area,
                            reqd: 1,
                            read_only: 1,
                            get_query(){
                                return{
                                    filters:{
                                        disabled: 0
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
                            label: __("Subservice Area"),
                            fieldname: "subservice_area",
                            fieldtype: "Link",
                            options: "Subservice Area",
                            default: fieldsObj.subservice_area,
                            reqd: 1,
                            read_only: 1,
                            get_query(){
                                let service_area = d.fields_dict.service_area.value;
                                return{
                                    filters:{
                                        service_area: service_area
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
                            label: __("Product"),
                            fieldname: "product",
                            fieldtype: "Link",
                            options: "Product",
                            default: fieldsObj.product,
                            reqd: 1,
                            read_only: 1,
                            get_query(){
                                let subservice_area = d.fields_dict.subservice_area.value;
                                return{
                                    filters:{
                                        subservice_area: subservice_area
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
                            label: __("Project"),
                            fieldname: "project",
                            fieldtype: "Link",
                            options: "Project",
                            default: fieldsObj.project,
                            // default: ("project" in frm.doc)? frm.doc.project: "",
                            reqd: 1,
                            read_only: 1,
                            // read_only: ["", undefined].includes(frm.doc.project)?0:1,
                            // get_query(){
                            // 	let service_area = d.fields_dict.service_area.value;
                            // 	return{
                            // 		filters:{
                            // 			company: frm.doc.company,
                            // 			custom_service_area: service_area
                            // 		}
                            // 	}
                            // }
                        },
                        {
                            label: __(""),
                            fieldname: "col_break",
                            fieldtype: "Column Break",
                        },
                        {
                            label: __("Cost Center"),
                            fieldname: "cost_center",
                            fieldtype: "Link",
                            options: "Cost Center",
                            read_only: 1,
                            default: fieldsObj.cost_center,
                        },
                        
                        // {
                        // 	label: __(""),
                        // 	fieldname: "col_break",
                        // 	fieldtype: "Column Break",
                        // },          
                        // {
                        // 	label: __("Get Balance"),
                        // 	fieldname: "get_balance",
                        // 	fieldtype: "Button",
                        // 	options: ``,
                        // 	click(){
                        // 		const filters = {
                        // 			"service_area": d.fields_dict.service_area.value,
                        // 			"subservice_area": d.fields_dict.subservice_area.value,
                        // 			"product": d.fields_dict.product.value,
                        // 			"project": d.fields_dict.project.value,
                        // 			"cost_center": d.fields_dict.cost_center.value,
                        // 			"company": frm.doc.company,
                        // 			"doctype": frm.doc.doctype,
                        // 		}
                        // 		let msg = "<p></p>";
                        // 		let data = [];
                        // 		const nofilters = get_validate_filters(filters);
                        // 		if(nofilters.notFound){
                        // 			msg = `<b style="color: red;">Please select ${nofilters.fieldname}<b>`;
                        // 		}else{
                        // 			const response = get_financial_stats(filters);
                                    
                        // 			if(response.length>0){
                        // 				// Update the donor_balance table's data
                        // 				data = response;
                        // 				// Refresh the child table grid to reflect the new data
                                        
                        // 			}else{
                        // 				data = [];
                        // 				msg = `<b style="color: red;">No balance found against these dimension.<b>`;
                        // 			}
                                    
                        // 		}
                        // 		d.fields_dict.donor_balance.df.data = data;
                        // 		d.fields_dict.donor_balance.grid.refresh();
            
                        // 		d.fields_dict.html_message.df.options = msg;
                        // 		d.fields_dict.html_message.refresh();
                        // 	}
                        // },
                        {
                            label: __(""),
                            fieldname: "section_donor_balance1",
                            fieldtype: "Section Break",
                        },
                        {
                            label: __("Existing Donor"),
                            fieldname: "existing_donor",
                            fieldtype: "Link",
                            options: "Donor",
                            reqd: 1,
                            get_query(){
                                return{
                                    filters:{
                                        status: "Active",
                                        donor_identity: "Known",
                                        default_currency: "PKR",
                                        name: ["in", donorslist]
                                    }
                                }
                            },
                            onchange(){
                                let actual_balance = program_details
                                .filter(row => row.pd_donor === d.fields_dict.existing_donor.value)
                                .map(row => row.actual_balance);
                                if(actual_balance.length>0){
                                    actual_balance = actual_balance[0];
                                }else{
                                    actual_balance = 0;
                                }
                                d.fields_dict.existing_balance.value = actual_balance;
                                d.fields_dict.existing_balance.refresh();
                            }
                        }, 
                        {
                            label: __("Existing Balance"),
                            fieldname: "existing_balance",
                            fieldtype: "Currency",
                            options: "",
                            reqd: 1,
                            read_only: 1,
                        }, 
                        {
                            label: __(""),
                            fieldname: "col_break",
                            fieldtype: "Column Break",
                        }, 
                        {
                            label: __("New Donor"),
                            fieldname: "new_donor",
                            fieldtype: "Link",
                            options: "Donor",
                            reqd: 1,
                            get_query(){
                                return{
                                    filters:{
                                        status: "Active",
                                        donor_identity: "Known",
                                        default_currency: "PKR",
                                        name: ["not in", donorslist]
                                    }
                                }
                            },
                            onchange(){
                                const new_donor = d.fields_dict.new_donor.value;
                                let amount = 0.0;
                                if(new_donor==""? false:true){
                                    fieldsObj["donor"] = new_donor;
                                    frappe.call({
                                        method: "akf_accounts.utils.dimensional_donor_balance.get_donor_balance",
                                        async: false,
                                        args: {
                                            filters: fieldsObj 
                                        },
                                        callback: function(r){
                                            let data = r.message;
                                            const amountlist = data
                                            .filter(row => row.balance >0.0)
                                            .map(row => row.balance);
                                            
                                            amountlist.forEach(num=>{
                                                amount += num;
                                            });
                                        }
                                    });
                                }
                                d.fields_dict.new_balance.value = amount;
                                d.fields_dict.new_balance.refresh();
                            }
                        }, 
                        {
                            label: __("New Balance"),
                            fieldname: "new_balance",
                            fieldtype: "Currency",
                            options: "",
                            reqd: 1,
                            read_only: 1,
                        },
                        {
                            label: __("Link Records"),
                            fieldname: "section_donor_balance1",
                            fieldtype: "Section Break",
                        },
                        {
                            label: __("Payment Entry"),
                            fieldname: "payment_entry",
                            fieldtype: "Small Text",
                            options: "",
                            default: JSON.stringify(linkDocs.payment_entry),
                            read_only: 1,
                        },
                        {
                            label: __(""),
                            fieldname: "col_break",
                            fieldtype: "Column Break",
                        },
                        {
                            label: __("Purchase Invoice"),
                            fieldname: "purchase_invoice",
                            fieldtype: "Link",
                            options: "Purchase Invoice",
                            default: frm.doc.name,
                            read_only: 1,
                        },
                        {
                            label: __(""),
                            fieldname: "col_break",
                            fieldtype: "Column Break",
                        }, 
                        {
                            label: __("Purchase Receipt"),
                            fieldname: "purchase_receipt",
                            fieldtype: "Link",
                            options: "Purchase Receipt",
                            default: linkDocs.purchase_receipt,
                            read_only: 1,

                        },
                        {
                            label: __(""),
                            fieldname: "col_break",
                            fieldtype: "Column Break",
                        }, 
                        {
                            label: __("Material Request"),
                            fieldname: "material_request",
                            fieldtype: "Link",
                            options: "Material Request",
                            default: linkDocs.material_request,
                            read_only: 1,
                        },
                        {
                            label: __(""),
                            fieldname: "col_break",
                            fieldtype: "Column Break",
                        }, 
                        {
                            label: __("Budget"),
                            fieldname: "budget",
                            fieldtype: "Link",
                            options: "Budget",
                            default: linkDocs.budget,
                            read_only: 1,
                        },
                        {
                            label: __(""),
                            fieldname: "section_donor_balance1",
                            fieldtype: "Section Break",
                        },
                        {
                            label: __(""),
                            fieldname: "error_message",
                            fieldtype: "HTML",
                        },
                        
                    ],

                    size: 'extra-large', // small, large, extra-large 
                    primary_action_label: 'Update Transactions',
                    primary_action(values) {
                        if(values.new_balance>=values.existing_balance){
                            update_link_records_of_donor_func(values)
                        }else{
                            d.fields_dict.error_message.df.options = `<b style="color: red;">New-Balance must be greater than Existing-Balance.<b>`;
                            d.fields_dict.error_message.refresh();
                        }
                        d.hide();
                    }
                });
                d.show();
            }
        );
    }
}

function get_link_records_func(filters){
    let data;
    frappe.call({
        method: "akf_accounts.utils.dimensional_donor_balance.get_link_records",
        async: false,
        args: {
            filters: filters
        }, 
        callback: function(r){
            data = r.message;
            console.log(data);
        }
    });
    return data;
}

function update_link_records_of_donor_func(values){
    let data;
    frappe.call({
        method: "akf_accounts.utils.change_donor.update_link_records_of_donor",
        async: false,
        args: {
            values: values
        }, 
        callback: function(r){
            data = r.message;
            // console.log(data);
        }
    });
    return data;
}
