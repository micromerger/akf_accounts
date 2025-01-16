// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

// render
frappe.listview_settings['Donation'] = {
	add_fields: ["donor", "donor_name", "status", "outstanding_amount", "is_return", "unknown_to_known"],
	get_indicator: function(doc) {
		const status_colors = {
			"Draft": "grey",
			"Unpaid": "orange",
			"Paid": "green",
			"Partly Return": "yellow",
			"Return": "gray",
			"Credit Note Issued": "gray",
			"Unpaid and Discounted": "orange",
			"Partly Paid and Discounted": "yellow",
			"Overdue and Discounted": "red",
			"Overdue": "red",
			"Partly Paid": "yellow",
			"Internal Transfer": "darkgrey",
			"Unknown To Known": "green"
		};
		// console.log(doc.unknown_to_known);
		// console.log(doc.status);
		if(doc.unknown_to_known || doc.status=="Unknown To Known"){
			return [__("Unknown To Known"), status_colors["Unknown To Known"], "status,=,"+"Unknown To Known"];
		}
		else if((doc.status=="Paid" || doc.outstanding_amount==0) && (!doc.is_return) ){
			return [__("Paid"), status_colors["Paid"], "status,=,"+"Paid"];
		}
		else if(doc.is_return || doc.status=="Return"){
			return [__("Return"), status_colors["Return"], "status,=,"+"Paid"];
		}else{
			return [__(doc.status), status_colors[doc.status], "status,=,"+doc.status];
		}
		
	},
	right_column: "net_total",
};

frappe.listview_settings['Donation'].formatters = {
	// donor_name(value){
	// 	console.log(typeof(value), value);
	// 	// return `<b style='font-weight: 400px; color: blue !important;'>${value}</b>`
	// }
}
