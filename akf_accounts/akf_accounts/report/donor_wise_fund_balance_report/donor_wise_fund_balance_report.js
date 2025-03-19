// Mubashir Bashir 19-03-2025

frappe.query_reports["Donor Wise Fund Balance Report"] = {
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
			fieldname: "donor",
			label: __("Donor"),
			fieldtype: "Link",
			options: "Donor",
		},
		{
			"fieldname":"branch",
			"label": __("Branch"),
			"fieldtype": "MultiSelectList",
			get_data: function(txt) {
				return frappe.db.get_link_options('Cost Center', txt, {
					company: frappe.query_report.get_filter_value("company")
				});
			}
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
