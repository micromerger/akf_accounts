frappe.ui.form.on('Stock Entry', {
    stock_entry_type: function (frm) {
        // set_inventory_flag(frm);

        // if (frm.doc.stock_entry_type == "Donated Inventory Receive - Restricted" || frm.doc.stock_entry_type == "Donated Inventory Disposal - Restricted") {
        //     (frm.doc.items || []).forEach((item) => {
        //         frappe.model.set_value(
        //             "Stock Entry Detail",
        //             item.name,
        //             "inventory_flag",
        //             "Donated"
        //         );

        //         frappe.model.set_value(
        //             "Stock Entry Detail",
        //             item.name,
        //             "inventory_scenario",
        //             "Restricted"
        //         );
        //     });
        //     frm.get_field("items").grid.toggle_display("inventory_flag", false);
        //     frm.get_field("items").grid.toggle_display("inventory_scenario", false);
        // } else {
        //     frm.get_field("items").grid.toggle_display("inventory_flag", true);
        //     frm.get_field("items").grid.toggle_display("inventory_scenario", true);
        // }
    },
});

frappe.ui.form.on("Stock Entry Detail", {
    project: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        // multiple values
        frappe.db.get_value('Project', row.project, ['fund_class', 'custom_service_area', 'custom_subservice_area', 'custom_product'])
            .then(r => {
                let values = r.message;
                // console.log(values)
                row.fund_class = values.fund_class;
                row.service_area = values.custom_service_area;
                row.subservice_area = values.custom_subservice_area;
                row.product = values.custom_product;
                frm.refresh_field('items');
            });
        
    },
});

function set_queries(frm) {
    frm.fields_dict["items"].grid.get_field("subservice_area").get_query =
        function (doc, cdt, cdn) {
            let row = locals[cdt][cdn];
            return {
                filters: {
                    service_area: row.service_area,
                },
            };
        };

    frm.fields_dict["items"].grid.get_field("product").get_query = function (
        doc,
        cdt,
        cdn
    ) {
        let row = locals[cdt][cdn];
        return {
            filters: {
                subservice_area: row.subservice_area,
            },
        };
    };

    frm.fields_dict["items"].grid.get_field("project").get_query = function (
        doc,
        cdt,
        cdn
    ) {
        let row = locals[cdt][cdn];
        return {
            filters: {
                custom_service_area: row.service_area,
            },
        };
    };
}

function set_inventory_flag(frm) {
    if ((frm.doc.stock_entry_type == "Donated Inventory Receive - Restricted") || (frm.doc.stock_entry_type == "Donated Inventory Disposal - Restricted")) {
        (frm.doc.items || []).forEach((item) => {
            frappe.model.set_value(
                "Stock Entry Detail",
                item.name,
                "inventory_flag",
                "Donated"
            );

            frappe.model.set_value(
                "Stock Entry Detail",
                item.name,
                "inventory_scenario",
                "Restricted"
            );
        });
        frm.get_field("items").grid.toggle_display("inventory_flag", false);
        frm.get_field("items").grid.toggle_display("inventory_scenario", false);
    } else {
        frm.get_field("items").grid.toggle_display("inventory_flag", true);
        frm.get_field("items").grid.toggle_display("inventory_scenario", true);
    }

    if (frm.doc.purpose != "Material Issue") {
        frm.get_field("items").grid.toggle_display("custom_target_project", true);
    }
    else {
        frm.get_field("items").grid.toggle_display("custom_target_project", false);
    }
}
