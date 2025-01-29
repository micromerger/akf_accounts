import frappe

@frappe.whitelist()
def get_children(doctype, parent=None, company=None, is_root=False):
	if parent == None or parent == "All Donors":
		parent = ""

	return frappe.db.sql(
		"""
		select
			name as value,
			is_group as expandable
		from
			`tabDonor` comp
		where
			ifnull(parent_donor, "")={parent}
        order by
            is_group desc
		""".format(
			parent=frappe.db.escape(parent)
		),
		as_dict=1,
	)

@frappe.whitelist()
def add_node():
	from frappe.desk.treeview import make_tree_args

	args = frappe.form_dict
	args = make_tree_args(**args)
    
	if args.parent_donor == "All Donors":
		args.parent_donor = None

	frappe.get_doc(args).insert()
    