from frappe import _

def get_data():
	return {
		'fieldname': 'donation',
		'non_standard_fieldnames': {
			'Payment Entry': 'reference_name',
			"Donation": "return_against",
			"Stock Entry": "donation"
		},
		# "internal_links": {
		# 	"Donation": ["payment_detail", "reverse_against"],
		# },
		# "internal_and_external_links": {
        #     "Donation": ["payment_detail", "reverse_against"],
        # },
		'transactions': [
			{
				'label': _('Payment'),
				'items': ['Payment Entry']
			},
			{
				"label": _("Returns | Unknown To Known"), 
				"items": ["Donation"]
			},
			{
				"label": _("In Kind Donation"), 
				"items": ["Stock Entry"]
			},
		]
	}

