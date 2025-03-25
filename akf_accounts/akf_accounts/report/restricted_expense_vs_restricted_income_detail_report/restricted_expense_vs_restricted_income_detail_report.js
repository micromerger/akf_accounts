// Copyright (c) 2024, Nabeel Saleem and contributors
// For license information, please see license.txt

frappe.query_reports["Restricted Expense Vs Restricted Income Detail Report"] = {
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
			"fieldname":"branch",
			"label": __("Branch"),
			"fieldtype": "Link",
			"options": "Cost Center",
			get_query: () => {
				var company = frappe.query_report.get_filter_value("company");
				return {
					filters: {
						company: company,
					},
				};
			},
		},
		{
			"fieldname":"fund",
			"label": __("Fund Class"),
			"fieldtype": "Link",
			"options": "Project",
			// "reqd":1,
			get_query: () => {
				var company = frappe.query_report.get_filter_value("company");
				return {
					filters: {
						company: company,
					},
				};
			},
		},
	]
};
