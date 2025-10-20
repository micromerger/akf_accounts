import frappe
import ast
from frappe.utils import getdate


@frappe.whitelist()
def convert_unknown_to_known(source_name, target_doc=None, args=None, donor=None, serial_no=None):
	"""
	Create a mapped return Donation where an Unknown donor is converted to Known.

	This function can be called from Desk (which sets frappe.flags.args) or via RPC
	where `args` is passed in the form dict. Accept both cases.
	"""
	# Try RPC-provided args first (may be a JSON/string or dict)
	parsed_args = None
	if args:
		try:
			if isinstance(args, str):
				parsed_args = ast.literal_eval(args)
			else:
				parsed_args = args
		except Exception:
			# best-effort fallback
			parsed_args = {}
	# Next, try frappe.flags.args (used by Desk's open_mapped_doc)
	if not parsed_args:
		try:
			parsed_args = frappe.flags.args
		except Exception:
			parsed_args = None
	# Finally, check form dict for args key
	if not parsed_args:
		raw = frappe.form_dict.get("args") or frappe.form_dict.get("values")
		if raw:
			try:
				if isinstance(raw, str):
					parsed_args = ast.literal_eval(raw)
				else:
					parsed_args = raw
			except Exception:
				parsed_args = {}

	# If donor/serial_no passed directly, prefer them (front-end RPCs often pass flat params)
	if donor or serial_no:
		parsed_args = parsed_args or {}
		if donor:
			parsed_args["donor"] = donor
		if serial_no:
			parsed_args["serial_no"] = serial_no

	parsed_args = parsed_args or {}
	parsed_args = frappe._dict(parsed_args)

	return make_return_doc("Donation", source_name, target_doc, parsed_args)

def make_return_doc(
	doctype: str, source_name: str, target_doc=None, args=None, return_against_rejected_qty=False
):
	from frappe.model.mapper import get_mapped_doc
	
	def set_missing_values(source, target):
		doc = frappe.get_doc(target)
		# Parent doctype
		doc.donor_identity = "Known"
		doc.contribution_type = "Donation"
		doc.due_date = getdate()
		doc.status = "Unknown To Known"
		doc.unknown_to_known = 1
		doc.return_against = source.name
		doc.total_donors = 1
		# Parent doctype end

		# Child doctype
		payment_detail = doc.payment_detail
		doc.set("payment_detail", [])
		for d in payment_detail:
			if(int(d.idx)==int(args.serial_no)):
				d.donor = args.donor
				doc.append("payment_detail", d)
				break
	
	def update_payment_detail(source_doc, target_doc, source_parent):
		pass
		# target_doc.donation_amount = -1 * source_doc.donation_amount
		# target_doc.set("payment_detail", [])
		# target_doc.donation_amount = source_doc.donation_amount
		# target_doc.paid = 0
		# target_doc.reverse_against = source_doc.parent

	doclist = get_mapped_doc(
		doctype,
		source_name,
		{
			doctype: {
				"doctype": doctype,
				"validation": {
					"docstatus": ["=", 1],
				},
			},
			# "Payment Detail": {
				# "doctype": "Payment Detail",
				# "field_map": {"*"},
				# "postprocess": update_payment_detail,
			# },
			# "Payment Schedule": {"doctype": "Payment Schedule", "postprocess": update_terms},
		},
		target_doc,
		set_missing_values,
	)

	return doclist
