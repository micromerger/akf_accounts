// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

// render
frappe.listview_settings['Donation'] = {
	add_fields: ["donor", "donor_name", "status"],
	get_indicator: function(doc) {
		const status_colors = {
			"Draft": "grey",
			"Unpaid": "orange",
			"Paid": "green",
			"Return": "gray",
			"Credit Note Issued": "gray",
			"Unpaid and Discounted": "orange",
			"Partly Paid and Discounted": "yellow",
			"Overdue and Discounted": "red",
			"Overdue": "red",
			"Partly Paid": "yellow",
			"Internal Transfer": "darkgrey"
		};
		return [__(doc.status), status_colors[doc.status], "status,=,"+doc.status];
	},
	right_column: "net_total",
};

frappe.listview_settings['Donation'].formatters = {
	// donor_name(value){
	// 	console.log(typeof(value), value);
	// 	// return `<b style='font-weight: 400px; color: blue !important;'>${value}</b>`
	// }
}
