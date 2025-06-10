frappe.ui.form.on('Purchase Invoice', {
    onload_post_render: function(frm) {
      
        set_query_for_item_code(frm);
        
    },
    refresh: function(frm) {
        // toggle_custom_fields(frm);
        set_queries_payment_details(frm);
        // Check if the form is not new, not local, and custom_type_of_transaction is "Inventory Purchase Restricted"
        if (!frm.is_new() && !frm.doc.__islocal && ["Inventory Purchase Restricted", "Asset Purchase Restricted"].includes(frm.doc.custom_type_of_transaction)) {
            // Check if any item has an empty purchase_receipt
            let empty_receipt = false;
            frm.doc.items.forEach(function(item) {
                if (!item.purchase_receipt) {
                    empty_receipt = true;
                }
            });

            // if (empty_receipt) {
            //     get_html(frm);
            // }
        }
    },
    

    //olddd
    // refresh: function(frm) {
    //     // toggle_custom_fields(frm);
    //     set_queries_payment_details(frm);
    //     console.log("Refresh triggered");
    //     if (!frm.is_new() && !frm.doc.__islocal && frm.doc.custom_type_of_transaction == "Inventory Purchase Restricted") {
    //         get_html(frm);
    //     }
    // },

    onload: function(frm) {
        if (frm.doc.__islocal) {
            console.log("On load");
            frm.doc.items.forEach(function(item) {
                if (item.purchase_receipt) {
                    frm.set_df_property("custom_program_details", "hidden", 1);
                    frm.set_df_property("custom_donor_list_html", "hidden", 1);
                    frm.set_df_property("update_stock", "hidden", 1);
                }
            });
        }

        $("#table_render").empty();
        $("#total_amount").empty();
        $("#previous").empty();
        $("#next").empty();
    },
});


// frappe.ui.form.on("Program Details", {
//     pd_donor: function(frm, cdt, cdn) {
//         // Trigger the get_html function whenever ff_donor is updated
//         get_html(frm);
//     }
// });


function set_query_for_item_code(frm) {
    frm.fields_dict['items'].grid.get_field('item_code').get_query = function(doc, cdt, cdn) {
        var asset_filters = {
            disabled: 0,
            has_variants: 0,
            is_fixed_asset: 1 
        };
        var inventory_filters = {
            disabled: 0,
            has_variants: 0,
            is_stock_item: 1
        };
        var normal_filters = {
            disabled: 0
        };
        console.log("custom_type_of_transaction", frm.doc.custom_type_of_transaction)
        console.log("inventory_filters" , inventory_filters);
        console.log("asset_filters" , asset_filters);
        console.log("normal_filters" , normal_filters);
        
        if (frm.doc.custom_type_of_transaction === "Asset Purchase Restricted") {
            console.log("Inside Asset Purchase");
            
            return {
                filters: asset_filters
            };
        } 
        else if (frm.doc.custom_type_of_transaction === "Inventory Purchase Restricted") {
            console.log("Inside Inventory Purchase Restricted");
            console.log();
            
            return {
                filters: inventory_filters
            };
        } 
        else {
            console.log("Inside Else");
            return {
                filters: normal_filters
            };
        }
    };

}



function toggle_custom_fields(frm) {
    let hide_fields = true;

    // Loop through each row in the child table
    frm.doc.items.forEach(row => {
        if (row.purchase_receipt) {
            hide_fields = false;
        }
    });

    frm.set_df_property('custom_program_details', 'hidden', hide_fields ? 1 : 0);
    frm.set_df_property('custom_donor_list_html', 'hidden', hide_fields ? 1 : 0);
   

}
// function get_html(frm) {
//     $("#table_render").empty();

//     frappe.call({
//         method: "akf_accounts.customizations.extends.xpurchase_invoice.donor_list_data",
//         args: {
//             doc: frm.doc,
//         },
//         callback: function(r) {
//             console.log("DONOR LISTTTT");
//             console.log(r.message);

//             if (r.message) {
//                 console.log("Function Triggered from JS side Donor List");
//                 console.log(r.message);

//                 var donorList = r.message.donor_list;
//                 var totalBalance = r.message.total_balance || 0;
//                 var docstatus = frm.doc.docstatus;

//                 if (!donorList || donorList.length === 0) {
//                     console.log("donorList000", donorList);
//                     $("#table_render").empty();
//                     $("#total_balance").empty();
//                     $("#previous").empty();
//                     $("#next").empty();
//                     frm.set_df_property('custom_donor_list_html', 'options', 'No donor records found.');

//                     frappe.throw("No such entry exists for donor with provided details.");
//                 } else if (donorList && donorList.length > 0) {
//                     console.log("donorList111", donorList);

//                     var currentPage = 1;
//                     var recordsPerPage = 5;
//                     var totalPages = Math.ceil(donorList.length / recordsPerPage);

//                     function displayPage(page) {
//                         var start = (page - 1) * recordsPerPage;
//                         var end = start + recordsPerPage;
//                         var paginatedDonorList = donorList.slice(start, end);

//                         var tableHeader = `
//                             <table class="table table-bordered" style="border: 2px solid black;" id="table_render">
//                                 <thead style="background-color: #015aab; color: white; text-align: left;">
//                                     <tr>
//                                         <th class="text-left" style="border: 1px solid black;">Donor ID</th>
//                                         <th class="text-left" style="border: 1px solid black;">Cost Center</th>
//                                         <th class="text-left" style="border: 1px solid black;">Product</th>
//                                         ${docstatus == 1 ? '<th class="text-left" style="border: 1px solid black;">Donated Amount</th>' : '<th class="text-left" style="border: 1px solid black;">Balance</th>'}
//                                     </tr>
//                                 </thead>
//                                 <tbody>
//                         `;

//                         var donorListRows = "";
//                         paginatedDonorList.forEach(function(d) {
//                             var donorId = d.donor || '-';
//                             var costCenter = d.cost_center || '-';
//                             var product = d.product || '-';
//                             var balance = d.balance || '0';
//                             var usedAmount = d.used_amount || '0';

//                             var backgroundColor = (parseFloat(balance) < 0 || parseFloat(usedAmount) < 0) ? '#EE4B2B' : '#d1d1d1'; 

//                             var row = `
//                                 <tr style="background-color: ${backgroundColor}; color: black; text-align: left;">
//                                     <td class="text-left" style="border: 1px solid black;">${donorId}</td>
//                                     <td class="text-left" style="border: 1px solid black;">${costCenter}</td>
//                                     <td class="text-left" style="border: 1px solid black;">${product}</td>
//                                     ${docstatus == 1 ? `<td class="text-left" style="border: 1px solid black;">Rs.${usedAmount}</td>` : `<td class="text-left" style="border: 1px solid black;">Rs.${balance}</td>`}
//                                 </tr>
//                             `;
//                             donorListRows += row;
//                         });

//                         var completeTable = tableHeader + donorListRows + "</tbody></table><br>";

//                         if (docstatus != 1 && totalBalance !== 0) {
//                             completeTable += `
//                                 <h5 style="text-align: right;" id="total_balance"><strong>Total Balance: Rs.${totalBalance}</strong></h5>
//                             `;
//                         }

//                         if (totalPages > 1) {
//                             completeTable += generatePaginationControls();
//                         }

//                         frm.set_df_property('custom_donor_list_html', 'options', completeTable);
//                     }

//                     function generatePaginationControls() {
//                         var controls = `<div style="text-align: center; margin-top: 10px;">`;

//                         if (currentPage > 1) {
//                             controls += `<button onclick="changePage(${currentPage - 1})" style="text-align: right;" id="previous">Previous</button>`;
//                         }

//                         controls += ` Page ${currentPage} of ${totalPages} `;

//                         if (currentPage < totalPages) {
//                             controls += `<button onclick="changePage(${currentPage + 1})" style="text-align: right;" id="next">Next</button>`;
//                         }

//                         controls += `</div>`;
//                         return controls;
//                     }

//                     window.changePage = function(page) {
//                         if (page >= 1 && page <= totalPages) {
//                             currentPage = page;
//                             displayPage(currentPage);
//                         }
//                     };

//                     displayPage(currentPage);
//                 }
//             } else {
//                 $("#table_render").empty();
//                 $("#total_balance").empty();
//                 $("#previous").empty();
//                 $("#next").empty();
//                 frm.set_df_property('custom_donor_list_html', 'options', '');
//                 frappe.msgprint("No data received.");
//             }
//         }
//     });
// }



function set_queries_payment_details(frm){
    set_query_subservice_area(frm);
    set_query_cost_center(frm);
    set_query_product(frm);
    set_query_project(frm);
    set_query_donor(frm);
    
}

function set_query_service_area(frm){
    frm.fields_dict['custom_program_details'].grid.get_field('service_area').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                subservice_area: ["!=", ""],
                subservice_area: row.subservice_area,
            }
        };
    };
}

function set_query_subservice_area(frm){
    frm.fields_dict['custom_program_details'].grid.get_field('pd_subservice_area').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                service_area: ["!=", ""],
                service_area: row.pd_service_area,
            }
        };
    };
}

function set_query_cost_center(frm){
    frm.fields_dict['custom_program_details'].grid.get_field('pd_cost_center').get_query = function(doc, cdt, cdn) {
        return {
            filters: {
                is_group: 0,
                disabled: 0,
                company: frm.doc.company,
            }
        };
    };
}

// function set_query_product(frm){
//     frm.fields_dict['custom_program_details'].grid.get_field('pd_product').get_query = function(doc, cdt, cdn) {
//         var row = locals[cdt][cdn];
//         return {
//             filters: {
//                 subservice_area: ["!=", ""],
//                 subservice_area: row.pd_subservice_area,
//             }
//         };
//     };
// }


function set_query_product(frm) {
    frm.fields_dict['custom_program_details'].grid.get_field('pd_product').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        console.log("pd_subservice_area:", row.pd_subservice_area);

        let ffilters = row.pd_subservice_area === undefined
            ? { subservice_area: ["!=", undefined] }
            : { subservice_area: row.pd_subservice_area };

        return {
            filters: ffilters
        };
    };
}
function set_query_project(frm){
    frm.fields_dict['custom_program_details'].grid.get_field('pd_project').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                company: frm.doc.company,
                custom_program: ["!=", ""],
                custom_program: row.pd_service_area,
                
            }
        };
    };
}

function set_query_donor(frm){
    frm.fields_dict['custom_program_details'].grid.get_field('pd_donor').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                status: "Active"
            }
        };
    };
}

frappe.ui.form.on("Purchase Receipt Item", {
    custom_new: function(frm, cdt, cdn){
        let row = locals[cdt][cdn];
        if(row.custom_new){
            row.custom_used = 0;
        }
        frm.refresh_field("items")
    },
    custom_used: function(frm, cdt, cdn){
        let row = locals[cdt][cdn];
        if(row.custom_used){
            row.custom_new = 0;
        }
        frm.refresh_field("items")
    }

    
});


frappe.ui.form.on("Purchase Invoice Item", {
    custom_new: function(frm, cdt, cdn){
        let row = locals[cdt][cdn];
        if(row.custom_new){
            row.custom_used = 0;
        }
        frm.refresh_field("items")
    },
    custom_used: function(frm, cdt, cdn){
        let row = locals[cdt][cdn];
        if(row.custom_used){
            row.custom_new = 0;
        }
        frm.refresh_field("items")
    }

    
});
