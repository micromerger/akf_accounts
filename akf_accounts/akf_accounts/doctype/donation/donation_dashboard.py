from frappe import _


def get_data():
	return {
		'fieldname': 'donation',
		'non_standard_fieldnames': {
			'Payment Entry': 'reference_name',
			"Donation": "return_against",
		},
		'transactions': [
			{
				'label': _('Payment'),
				'items': ['Payment Entry']
			},
			{
				"label": _("Returns"), 
				"items": ["Donation"]
			},
		]
	}

