// Copyright (c) 2024, Nabeel Saleem and contributors
// For license information, please see license.txt

frappe.query_reports["Fund Balance Report"] = {
	"filters": [
		{
			fieldname: "branch",
			label: __("Branch"),
			fieldtype: "Link",
			options: "Cost Center",
		},
		{
			fieldname: "service_area",
			label: __("Service Area"),
			fieldtype: "Link",
			options: "Program",
		},
		{
			fieldname: "subservice_area",
			label: __("Subservice Area"),
			fieldtype: "Link",
			options: "Subservice Area",
		},
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
		},
	]
};
