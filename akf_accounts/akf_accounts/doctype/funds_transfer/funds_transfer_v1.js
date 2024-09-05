frappe.ui.form.on("Funds Transfer", {
    onload_post_render: function(frm) {
        frm.get_field("funds_transfer_from").grid.set_multiple_add("ff_service_area");
        frm.refresh_field('funds_transfer_from');

        frm.get_field("funds_transfer_to").grid.set_multiple_add("ft_service_area");
        frm.refresh_field('funds_transfer_to');
    },

    refresh: function(frm) {
        set_query_service_area_transfer_from(frm);
        set_query_service_area_transfer_to(frm);
        set_queries_funds_transfer_to(frm);
        set_queries_funds_transfer_from(frm);
        console.log(!frm.is_new());
        console.log(!frm.doc.__islocal);
        if (!frm.is_new() && !frm.doc.__islocal) {
            get_html(frm);
        }

        if (frm.doc.docstatus === 1) {  
            set_custom_btns(frm);
        }
    },

    onload: function(frm) {
        $("#table_render").empty();
        $("#total_balance").empty();
        $("#previous").empty();
        $("#next").empty();
    },
});

frappe.ui.form.on('Funds Transfer From', {
    ff_company: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        let company = row.ff_company;

        frappe.model.set_value(cdt, cdn, 'ff_account', '');
        frappe.model.set_value(cdt, cdn, 'ff_cost_center', '');
        frappe.model.set_value(cdt, cdn, 'ff_service_area', '');
        frappe.model.set_value(cdt, cdn, 'ff_subservice_area', '');
        frappe.model.set_value(cdt, cdn, 'ff_product', '');
        frappe.model.set_value(cdt, cdn, 'ff_project', '');
       

        frappe.call({
            method: "akf_accounts.akf_accounts.doctype.funds_transfer.funds_transfer.get_service_areas",
            args: {
                doc: frm.doc
            },
            callback: function(r) {
                console.log("SERVICE AREA QUERY!!!");
                console.log(r.message);  

                frm.fields_dict['funds_transfer_from'].grid.get_field('ff_service_area').get_query = function(doc, cdt, cdn) {
                    var row = locals[cdt][cdn];
                    var company = row.ff_company;

                    if (!company) {
                        return {
                            filters: {
                                service_area: ["!=", ""]
                            }
                        };
                    }

                    return {
                        filters: {
                            company: company,
                            service_area: ["in", r.message]  
                        }
                    };
                };

                frm.refresh_field('funds_transfer_from'); // Corrected method call
            }
        });
    }
});

function set_query_service_area_transfer_from(frm) {
    frm.fields_dict['funds_transfer_from'].grid.get_field('ff_service_area').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        var company = row.ff_company;

        if (!company) {
            return {
                filters: {
                    service_area: ["!=", ""]
                }
            };
        }

        return {
            filters: {
                company: company
            }
        };
    };
}

frappe.ui.form.on('Funds Transfer To', {
    ft_company: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        let company = row.ft_company;

        frappe.model.set_value(cdt, cdn, 'ft_account', '');
        frappe.model.set_value(cdt, cdn, 'ft_cost_center', '');
        frappe.model.set_value(cdt, cdn, 'ft_service_area', '');
        frappe.model.set_value(cdt, cdn, 'ft_subservice_area', '');
        frappe.model.set_value(cdt, cdn, 'ft_product', '');
        frappe.model.set_value(cdt, cdn, 'ft_project', '');


        frappe.call({
            method: "akf_accounts.akf_accounts.doctype.funds_transfer.funds_transfer.get_service_areas",
            args: {
                doc: frm.doc
            },
            callback: function(r) {
                console.log("SERVICE AREA QUERY!!!");
                console.log(r.message);  

                frm.fields_dict['funds_transfer_to'].grid.get_field('ft_service_area').get_query = function(doc, cdt, cdn) {
                    var row = locals[cdt][cdn];
                    var company = row.ft_company;

                    if (!company) {
                        return {
                            filters: {
                                service_area: ["!=", ""]
                            }
                        };
                    }

                    return {
                        filters: {
                            company: company,
                            service_area: ["in", r.message]  
                        }
                    };
                };

                frm.fields_dict['funds_transfer_from'].grid.refresh_field('ff_service_area');
            }
        });
    }
});

function set_query_service_area_transfer_to(frm) {
    frm.fields_dict['funds_transfer_to'].grid.get_field('ft_service_area').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        var company = row.ft_company;

        if (!company) {
            return {
                filters: {
                    service_area: ["!=", ""]
                }
            };
        }

        return {
            filters: {
                company: company
            }
        };
    };
}


function set_custom_btns(frm) {
    frm.add_custom_button(__('Accounting Ledger'), function () {
        frappe.set_route("query-report", "General Ledger", {"voucher_no": frm.doc.name,"group_by": ""});
    }, __("View"));
}

function set_queries_funds_transfer_from(frm) {
    set_query_cost_center_transfer_from(frm);
    set_query_subservice_area_transfer_from(frm);
    set_query_product_transfer_from(frm);
    set_query_project_transfer_from(frm);
    set_query_account_transfer_from(frm);
}

function set_query_cost_center_transfer_from(frm) {
    frm.fields_dict['funds_transfer_from'].grid.get_field('ff_cost_center').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                is_group: 0,
                disabled: 0,
                company: row.ff_company
            }
        };
    };
}

function set_query_subservice_area_transfer_from(frm){
    frm.fields_dict['funds_transfer_from'].grid.get_field('ff_subservice_area').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        let ffilters = row.ff_service_area === undefined
        ? { service_area: ["!=", undefined] }
        : { service_area: row.ff_service_area };

        return {
            filters: ffilters
        };
        };
    };



    
    




function set_query_product_transfer_from(frm) {
    frm.fields_dict['funds_transfer_from'].grid.get_field('ff_product').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        let ffilters = row.ff_subservice_area === undefined
            ? { subservice_area: ["!=", undefined] }
            : { subservice_area: row.ff_subservice_area };

        return {
            filters: ffilters
        };
    };
}

function set_query_project_transfer_from(frm){
    frm.fields_dict['funds_transfer_from'].grid.get_field('ff_project').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                // company: frm.doc.company,
                custom_program: ["!=", ""],
                custom_program: row.ff_service_area,
                
            }
        };
    };
}


function set_query_account_transfer_from(frm){
    frm.fields_dict['funds_transfer_from'].grid.get_field('ff_account').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                company: row.ff_company,
                
                
            }
        };
    };
}
function set_queries_funds_transfer_to(frm){
    set_query_cost_center(frm);
    set_query_subservice_area(frm);
    set_query_product(frm);
    set_query_project(frm);
    set_query_account(frm);
 
}
function set_query_cost_center(frm){
    frm.fields_dict['funds_transfer_to'].grid.get_field('ft_cost_center').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                is_group: 0,
                disabled: 0,
                company: row.ft_company

            }
        };
    };
}


function set_query_service_area(frm){
    frm.fields_dict['funds_transfer_to'].grid.get_field('service_area').get_query = function(doc, cdt, cdn) {
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
    frm.fields_dict['funds_transfer_to'].grid.get_field('ft_subservice_area').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        let ffilters = row.ft_service_area === undefined
        ? { service_area: ["!=", undefined] }
        : { service_area: row.ft_service_area };

        return {
            filters: ffilters
        };
        };
    };

function set_query_product(frm){
    frm.fields_dict['funds_transfer_to'].grid.get_field('ft_product').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                subservice_area: ["!=", ""],
                subservice_area: row.ft_subservice_area,
            }
        };
    };
}

function set_query_project(frm){
    frm.fields_dict['funds_transfer_to'].grid.get_field('ft_project').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                // company: frm.doc.company,
                custom_program: ["!=", ""],
                custom_program: row.ft_service_area,
                
            }
        };
    };
}

function set_query_account(frm){
    frm.fields_dict['funds_transfer_to'].grid.get_field('ft_account').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                company: row.ft_company,
                
                
            }
        };
    };
}

function get_html(frm) {
    // $("#table_render").empty();

    frappe.call({
        method: "akf_accounts.akf_accounts.doctype.funds_transfer.funds_transfer.donor_list_data",
        args: {
            doc: frm.doc,
        },
        callback: function(r) {
            console.log("DONOR LISTTTT");
            console.log(r.message);

            if (r.message) {
                console.log("Function Triggered from JS side Donor List");
                console.log(r.message);

                var donorList = r.message.donor_list;
                var totalBalance = r.message.total_balance || 0;
                var docstatus = frm.doc.docstatus;

                if (!donorList || donorList.length === 0) {
                    console.log("donorList000", donorList);
                    $("#table_render").empty();
                    $("#total_balance").empty();
                    $("#previous").empty();
                    $("#next").empty();
                    frm.set_df_property('donor_list_html', 'options', 'No donor records found.');
                } else if (donorList && donorList.length > 0) {
                    console.log("donorList111", donorList);

                    var currentPage = 1;
                    var recordsPerPage = 5;
                    var totalPages = Math.ceil(donorList.length / recordsPerPage);

                    function displayPage(page) {
                        var start = (page - 1) * recordsPerPage;
                        var end = start + recordsPerPage;
                        var paginatedDonorList = donorList.slice(start, end);

                        var tableHeader = `
                            <table class="table table-bordered" style="border: 2px solid black;" id="table_render">
                                <thead style="background-color: #015aab; color: white; text-align: left;">
                                    <tr>
                                        <th class="text-left" style="border: 1px solid black;">Donor ID</th>
                                        <th class="text-left" style="border: 1px solid black;">Cost Center</th>
                                        <th class="text-left" style="border: 1px solid black;">Product</th>
                                        ${docstatus == 1 ? '<th class="text-left" style="border: 1px solid black;">Transferred Amount</th>' : '<th class="text-left" style="border: 1px solid black;">Balance</th>'}
                                    </tr>
                                </thead>
                                <tbody>
                        `;

                        var donorListRows = "";
                        paginatedDonorList.forEach(function(d) {
                            var donorId = d.donor || '-';
                            var costCenter = d.cost_center || '-';
                            var product = d.product || '-';
                            var balance = d.balance || '0';
                            var usedAmount = d.used_amount || '0';

                            var backgroundColor = (parseFloat(balance) < 0 || parseFloat(usedAmount) < 0) ? '#EE4B2B' : '#d1d1d1'; 

                            var row = `
                                <tr style="background-color: ${backgroundColor}; color: black; text-align: left;">
                                    <td class="text-left" style="border: 1px solid black;">${donorId}</td>
                                    <td class="text-left" style="border: 1px solid black;">${costCenter}</td>
                                    <td class="text-left" style="border: 1px solid black;">${product}</td>
                                    ${docstatus == 1 ? `<td class="text-left" style="border: 1px solid black;">Rs.${usedAmount}</td>` : `<td class="text-left" style="border: 1px solid black;">Rs.${balance}</td>`}
                                </tr>
                            `;
                            donorListRows += row;
                        });

                        var completeTable = tableHeader + donorListRows + "</tbody></table><br>";

                        if (docstatus != 1 && totalBalance !== 0) {
                            completeTable += `
                                <h5 style="text-align: right;" id="total_balance"><strong>Total Balance: Rs.${totalBalance}</strong></h5>
                            `;
                        }

                        if (totalPages > 1) {
                            completeTable += generatePaginationControls();
                            console.log("Completeee Tableee")
                            console.log(completeTable)
                        }

                        frm.set_df_property('donor_list_html', 'options', completeTable);
                    }

                    function generatePaginationControls() {
                        var controls = `<div style="text-align: center; margin-top: 10px;">`;

                        if (currentPage > 1) {
                            controls += `<button onclick="changePage(${currentPage - 1})" style="text-align: right;" id="previous">Previous</button>`;
                        }

                        controls += ` Page ${currentPage} of ${totalPages} `;

                        if (currentPage < totalPages) {
                            controls += `<button onclick="changePage(${currentPage + 1})" style="text-align: right;" id="next">Next</button>`;
                        }

                        controls += `</div>`;
                        return controls;
                    }

                    window.changePage = function(page) {
                        if (page >= 1 && page <= totalPages) {
                            currentPage = page;
                            displayPage(currentPage);
                        }
                    };

                    displayPage(currentPage);
                }
            } else {
                $("#table_render").empty();
                $("#total_balance").empty();
                $("#previous").empty();
                $("#next").empty();
                frm.set_df_property('donor_list_html', 'options', '');
                frappe.msgprint("No data received.");
            }
        }
    });
}






  // frappe.call({
        //     method: "akf_accounts.akf_accounts.doctype.funds_transfer.funds_transfer.get_service_area",
        //     args: {
        //         doc: frm.doc,
        //     },
        //     callback: function(r) {
        //         console.log("SERVICE AREA QUERYYY!!!");
        //         console.log(r.message);
        //     }
        // });
    
// function set_query_service_area_transfer_from(frm){
//     frm.fields_dict['funds_transfer_from'].grid.get_field('ff_service_area').get_query = function(doc, cdt, cdn) {
//         var row = locals[cdt][cdn];
//         return {
//             filters: {
//                 company: ["!=", ""],
//                 // company: row.ff_company,
//             }
//         };
//     };
// }


// function set_query_service_area_transfer_from(frm){
//     frm.fields_dict['funds_transfer_from'].grid.get_field('ff_service_area').get_query = function(doc, cdt, cdn) {
//         var row = locals[cdt][cdn];
//         console.log("Queryyyyyyyyyyy");
        
//         console.log("Query: akf_accounts.akf_accounts.doctype.funds_transfer.funds_transfer.get_service_area");
//         console.log("Company filter:", row.ff_company);
//         return {
//             query: "akf_accounts.akf_accounts.doctype.funds_transfer.funds_transfer.get_service_area",
//             filters: {
//                 company: row.ff_company
//             }
//         };
//     };
// }
