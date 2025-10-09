import frappe
from frappe.utils import getdate
@frappe.whitelist()
def convert_unknown_to_known(source_name, target_doc=None):
	args = frappe._dict(frappe.flags.args) # e.g; {"donor": donor_id, "series_no": 1}
	return make_return_doc("Donation", source_name, target_doc, args)

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
