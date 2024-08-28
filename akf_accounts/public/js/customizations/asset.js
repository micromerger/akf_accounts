frappe.ui.form.on('Asset', {
    refresh: function (frm) {
        if(frm.doc.purchase_recipt)
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
