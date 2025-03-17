// Copyright (c) 2024, Nabeel Saleem and contributors
// For license information, please see license.txt

frappe.query_reports["Fund Movement Report"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 1
		},		
		{
			"fieldname":"cost_center",
			"label": __("Cost Center"),
			"fieldtype": "Link",
			"options": "Cost Center"
		},
		// {
		// 	"fieldname":"program",
		// 	"label": __("Service Area"),
		// 	"fieldtype": "Link",
		// 	"options": "Program"
		// },
		{
			"fieldname":"project",
			"label": __("Project"),
			"fieldtype": "Link",
			"options": "Project"
		},
		{
			"fieldname":"fiscal_year",
			"label": __("Fiscal Year"),
			"fieldtype": "Link",
			"options": "Fiscal Year",
			"required": 1
		},
		// {
		// 	"fieldname":"from_date",
		// 	"label": __("From Date"),
		// 	"fieldtype": "Date",
		// 	"default": get_default_from_date(),
		// 	"reqd": 1,
		// },
		// {
		// 	"fieldname":"to_date",
		// 	"label": __("To Date"),
		// 	"fieldtype": "Date",
		// 	"default": get_default_to_date(),
		// 	"reqd": 1,
		// }
	]
};


function get_default_from_date() {
	const today = new Date();
	const day = today.getDate();
	const month = today.getMonth();
	const year = today.getFullYear();

	let from_date;

	if (day > 20) {
		from_date = new Date(year, month, 22).toISOString().split("T")[0];
	} else {
		from_date = new Date(year, month - 1, 22).toISOString().split("T")[0];
	}

	console.log("Calculated from_date:", from_date);
	return from_date;
}

function get_default_to_date() {
	const today = new Date();
	const day = today.getDate();
	const month = today.getMonth();
	const year = today.getFullYear();

	let to_date;

	if (day > 20) {
		to_date = new Date(year, month + 1, 21).toISOString().split("T")[0];
	} else {
		to_date = new Date(year, month, 21).toISOString().split("T")[0];
	}

	console.log("Calculated to_date:", to_date);
	return to_date;
}
