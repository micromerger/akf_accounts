// Copyright (c) 2024, Nabeel Saleem and contributors
// For license information, please see license.txt

frappe.query_reports["Inter Branch Transfer Report"] = {
	"filters": [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			options: "",
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			options: "",
		},
		{
			fieldname: "voucher_no",
			label: __("Voucher No"),
			fieldtype: "Link",
			options: "Funds Transfer",
		},
		{
			fieldname: "donor",
			label: __("Donor"),
			fieldtype: "Link",
			options: "Donor",
		},
		{
			fieldname: "branch",
			label: __("Branch"),
			fieldtype: "Link",
			options: "Cost Center",
		},
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
		},
	]
};
