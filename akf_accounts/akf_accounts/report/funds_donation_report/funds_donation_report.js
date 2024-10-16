// Copyright (c) 2024, Nabeel Saleem and contributors
// For license information, please see license.txt

frappe.query_reports["Funds Donation Report"] = {
  filters: [
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
      fieldname: "donor",
      label: __("Donor"),
      fieldtype: "Link",
      options: "Donor",
    },
    {
      fieldname: "project",
      label: __("Fund/Class"),
      fieldtype: "Link",
      options: "Project",
    },
  ],
};
