frappe.ui.form.on('Purchase Receipt', {
    onload_post_render: function(frm) {
        // frm.get_field("custom_program_details").grid.set_multiple_add("service_area");
        // frm.refresh_field('custom_program_details');
    },
    refresh: function(frm) {
        set_queries_payment_details(frm);
        console.log("Refreshed triggered");
        if (!frm.is_new() && !frm.doc.__islocal) {
            get_html(frm);
        }
        },

	onload: function(frm) {
		$("#table_render").empty();
		$("#total_balance").empty();
		$("#previous").empty();
		$("#next").empty();
    }
});

function get_html(frm) {
    $("#table_render").empty();

    frappe.call({
        method: "akf_accounts.customizations.extends.xpurchase_receipt.donor_list_data",
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
                    frm.set_df_property('custom_donor_list_html', 'options', 'No donor records found.');
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
                                        ${docstatus == 1 ? '<th class="text-left" style="border: 1px solid black;">Donated Amount</th>' : '<th class="text-left" style="border: 1px solid black;">Balance</th>'}
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
                        }

                        frm.set_df_property('custom_donor_list_html', 'options', completeTable);
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
                frm.set_df_property('custom_donor_list_html', 'options', '');
                frappe.msgprint("No data received.");
            }
        }
    });
}



function set_queries_payment_details(frm){
    set_query_subservice_area(frm);
    set_query_cost_center(frm);
    set_query_product(frm);
    set_query_project(frm);
 
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

function set_query_product(frm){
    frm.fields_dict['custom_program_details'].grid.get_field('pd_product').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                subservice_area: ["!=", ""],
                subservice_area: row.pd_subservice_area,
            }
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
