// Copyright (c) 2024, Nabeel Saleem and contributors
// For license information, please see license.txt

frappe.query_reports["Voucher Status Report"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": "Company",
			"fieldtype": "Link",
			"options": "Company"
		},
		{
			"fieldname": "cost_center",
			"label": "Branch",
			"fieldtype": "Link",
			"options": "Cost Center"
		},
		{
			"fieldname": "voucher_type",
			"label": "Voucher Type",
			"fieldtype": "Select",
			"options": "Payment Entry\nInter Bank Transfer",
			"default": "Payment Entry"
		},
		{
			"fieldname": "status",
			"label": "Status",
			"fieldtype": "Select",
			"options": "\nOpen\nClose"
		}
	]
};
