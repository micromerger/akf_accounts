frappe.ui.form.on('Asset', {
    refresh: function (frm) {

        
        if (frm.doc.docstatus==1){
        frm.add_custom_button(__('Accounting Ledger'), function () {
            frappe.set_route('query-report', 'General Ledger',
                { against_voucher_type: 'Asset', against_voucher: frm.doc.name, voucher_no: frm.doc.name });
        }, __("View"));

    }
        if(frm.doc.purchase_receipt){
            console.log("Insideeee total_accumulated_depreciation")
        frm.call({
            method: 'akf_accounts.customizations.extends.XAsset.total_accumulated_depreciation',
            args: {
                asset_name: frm.doc.name,
                gross_purchase_amount : frm.doc.gross_purchase_amount
            },
            callback: function (r) {
                // frm.refresh();
                // frm.refresh_field("custom_current_asset_worth")
            }
        });

    }
    },
    custom_source_of_asset_acquistion: function(frm) {
		if(frm.doc.custom_source_of_asset_acquistion == 'In Kind'){
		frm.trigger("toggle_reference_doc");
		frm.set_df_property('purchase_receipt', 'read_only', 1);
		frm.set_df_property('purchase_invoice', 'read_only', 1);
		frm.set_value('is_existing_asset', 1);
		}
		else{
			frm.set_df_property('purchase_receipt', 'read_only', 0);
			frm.set_df_property('purchase_invoice', 'read_only', 0);
			frm.set_value('is_existing_asset', 0);
		}
		frm.refresh_field('purchase_receipt');
		frm.refresh_field('purchase_invoice');
	},
});



// frappe.ui.form.on('Asset', {
//     refresh: function (frm) {
//         var total_asset_cost = frm.doc.total_asset_cost
//         console.log(total_asset_cost);

//             frm.call({
//                 method: 'akf_accounts.customizations.extends.XAsset.total_accumulated_depreciation',
//                 args: {
//                     name: frm.doc.name
//                 },
//                 callback: function (response) {
//                     if (response.message) {
//                         console.log("ASSET JSSSSSSS!!!!");
//                         console.log(response);
//                         console.log("total_asset_cost");
//                         console.log(total_asset_cost);
//                         var current_worth = total_asset_cost - response.message
//                         console.log("current_worth");
//                         console.log(current_worth);
//                         frm.set_value('custom_total_accumulated_depreciation', response.message);
//                         frm.set_value('custom_asset_worth', current_worth);
//                         frm.save();
                    
//                     }
//                 }
//             });
//         },
//     });
