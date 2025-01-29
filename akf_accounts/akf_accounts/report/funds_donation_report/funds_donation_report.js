// Copyright (c) 2024, Nabeel Saleem and contributors
// For license information, please see license.txt

frappe.query_reports["Funds Donation Report"] = {
  filters: [
    {
      fieldname: "from_date",
      label: __("From Date"),
      fieldtype: "Date",
      default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
      reqd: 1,
      options: "",
    },
    {
      fieldname: "to_date",
      label: __("To Date"),
      fieldtype: "Date",
      default: frappe.datetime.get_today(),
      reqd: 1,
      options: "",
    },
    {
      fieldname: "donor",
      label: __("Donor"),
      fieldtype: "Link",
      options: "Donor",
    },
    {
      fieldname: "program",
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
      fieldname: "product",
      label: __("Product"),
      fieldtype: "Link",
      options: "Product",
    },
    {
      fieldname: "project",
      label: __("Fund/Class"),
      fieldtype: "Link",
      options: "Project",
    },
    {
      "fieldname": "group_by_branches",
      "label": __("Group by Branches"),
      "fieldtype": "Check"
    },
  ],
};
