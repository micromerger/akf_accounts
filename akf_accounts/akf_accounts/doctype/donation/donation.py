# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import json

import frappe, erpnext

from frappe import _
from frappe.email import sendmail_to_system_managers
from frappe.model.document import Document
from frappe.utils import flt, get_link_to_form, getdate, get_first_day, get_last_day, formatdate

# from non_profit.non_profit.doctype.membership.membership import verify_signature
from erpnext.accounts.general_ledger import make_gl_entries, process_gl_map
from frappe.core.doctype.sms_settings.sms_settings import send_sms

class Donation(Document):
	def validate(self):
		if not self.party or not frappe.db.exists(self.party_type, self.party):
			frappe.throw(_('Please select a Member'))
		self.set_party_name()
		self.payment_amount_range()

	def set_party_name(self):
		self.party_name = frappe.db.get_value(self.party_type, self.party, str(self.party_type).lower()+'_name')

	def payment_amount_range(self):
			if self.amount <100:
				frappe.throw(_('Volunteer can not pay less than 100.'))

	def on_payment_authorized(self, *args, **kwargs):
		self.db_set("paid", 1)
		self.load_from_db()
		self.create_payment_entry()

	def create_payment_entry(self, date=None):
		settings = frappe.get_doc('Non Profit Settings')
		if not settings.automate_donation_payment_entries:
			return

		if not settings.donation_payment_account:
			frappe.throw(_('You need to set <b>Payment Account</b> for Donation in {0}').format(
				get_link_to_form('Non Profit Settings', 'Non Profit Settings')))

		from non_profit.non_profit.custom_doctype.payment_entry import get_donation_payment_entry

		frappe.flags.ignore_account_permission = True
		pe = get_donation_payment_entry(dt=self.doctype, dn=self.name)
		frappe.flags.ignore_account_permission = False
		pe.paid_from = settings.donation_debit_account
		pe.paid_to = settings.donation_payment_account
		pe.posting_date = date or getdate()
		pe.reference_no = self.name
		pe.reference_date = date or getdate()
		pe.flags.ignore_mandatory = True
		pe.insert()
		pe.submit()
	
	def on_submit(self):
		self.make_gl_entries()

	def make_gl_entries(self, cancel=0, adv_adj=0):
		gl_entries = self.build_gl_map()
		gl_entries = process_gl_map(gl_entries)
		make_gl_entries(gl_entries, cancel=cancel, adv_adj=adv_adj)

	def build_gl_map(self):
		gl_entries = []
		self._party_gl_entries(gl_entries)
		return gl_entries
	
	def _party_gl_entries(self, gl_entries):
		donation_account = frappe.db.get_value('Non Profit Settings', None, 'donation_account')
		if donation_account:
			if erpnext.get_party_account_type(self.party_type) == "Receivable":
				cost_center = frappe.db.get_value('Company', self.company, 'cost_center')
				# credit the account: Volunteer Donations - AF
				_party_gle = frappe._dict({
					"posting_date": getdate(),
					"party_type": self.party_type,
					"party": self.party,
					"cost_center": cost_center,
					"account_currency": 'PKR',
					"against": "Received donation from volunteers.",
					"against_voucher_type": self.doctype,
					"against_voucher": self.name,
					"company": self.company,
					"voucher_type": self.doctype,
					"voucher_no": self.name,
					"is_cancelled": 0
				})
				_credit_gle = _party_gle.copy()
				_credit_gle.update({
					"account": donation_account,
					"credit": self.amount,
					"credit_in_account_currency": self.amount, 
					"debit": 0,
					"debit_in_account_currency": 0,
				})
				
				gl_entries.append(_credit_gle)

				# credit the account: Volunteer Donations - AF
				default_receivable_account = frappe.db.get_value('Company', self.company, 'default_receivable_account')
				if default_receivable_account:
					_debit_gle = _party_gle.copy()
					_debit_gle.update({
						"account": default_receivable_account,
						"credit": 0,
						"credit_in_account_currency": 0, 
						"debit": self.amount,
						"debit_in_account_currency": self.amount,
					})
					gl_entries.append(_debit_gle)
				else:
					frappe.throw('Please set company default receivalble account.')
			else:
				frappe.throw('Volunter account type must be receivalbe in {0}'.format(get_link_to_form('Party Type', 'Volunteer')))
			
	def on_cancel(self):
		""" 
		Payment Entry -> Payment Entry Reference
		GL Entry
		 """ 
		from frappe.desk.form.linked_with import get_linked_doctypes, cancel_all_linked_docs
		doc_ = get_linked_doctypes('GL Entry')
		# frappe.msgprint(frappe.as_json(doc_))
		# cancel_all_linked_docs('GL Entry')
		# for row in frappe.db.get_list('GL Entry', filters={'is_cancelled': 0, 'voucher_no': self.name}, fields=['name']):
		# 	frappe.get_doc('GL Entry', {'name': row.name}).cancel()

		# for row in frappe.get_list('Payment Entry Reference', {'docstatus': 1, 'reference_name': self.name}, 'parent'):
		# 	frappe.get_doc('Payment Entry', row.parent).cancel()
			
		# 	for row in frappe.db.get_list('GL Entry', filters={'is_cancelled': 0, 'voucher_no': row.parent}, fields=['name']):
		# 		frappe.get_doc('GL Entry', row.name).cancel()
		

@frappe.whitelist(allow_guest=True)
def capture_razorpay_donations(*args, **kwargs):
	"""
		Creates Donation from Razorpay Webhook Request Data on payment.captured event
		Creates Donor from email if not found
	"""
	data = frappe.request.get_data(as_text=True)

	try:
		verify_signature(data, endpoint='Donation')
	except Exception as e:
		log = frappe.log_error(e, 'Donation Webhook Verification Error')
		notify_failure(log)
		return { 'status': 'Failed', 'reason': e }

	if isinstance(data, str):
		data = json.loads(data)
	data = frappe._dict(data)

	payment = data.payload.get('payment', {}).get('entity', {})
	payment = frappe._dict(payment)

	try:
		if not data.event == 'payment.captured':
			return

		# to avoid capturing subscription payments as donations
		if payment.invoice_id or (
			payment.description and "subscription" in str(payment.description).lower()
		):
			return

		donor = get_donor(payment.email)
		if not donor:
			donor = create_donor(payment)

		donation = create_razorpay_donation(donor, payment)
		donation.run_method('create_payment_entry')

	except Exception as e:
		message = '{0}\n\n{1}\n\n{2}: {3}'.format(e, frappe.get_traceback(), _('Payment ID'), payment.id)
		log = frappe.log_error(message, _('Error creating donation entry for {0}').format(donor.name))
		notify_failure(log)
		return { 'status': 'Failed', 'reason': e }

	return { 'status': 'Success' }

def create_razorpay_donation(donor, payment):
	if not frappe.db.exists('Mode of Payment', payment.method):
		create_mode_of_payment(payment.method)

	company = get_company_for_donations()
	donation = frappe.get_doc({
		'doctype': 'Donation',
		'company': company,
		'donor': donor.name,
		'donor_name': donor.donor_name,
		'email': donor.email,
		'date': getdate(),
		'amount': flt(payment.amount) / 100, # Convert to rupees from paise
		'mode_of_payment': payment.method,
		'payment_id': payment.id
	}).insert(ignore_mandatory=True)

	donation.submit()
	return donation

def get_donor(email):
	donors = frappe.get_all('Donor',
		filters={'email': email},
		order_by='creation desc')

	try:
		return frappe.get_doc('Donor', donors[0]['name'])
	except Exception:
		return None

@frappe.whitelist()
def create_donor(payment):
	donor_details = frappe._dict(payment)
	donor_type = frappe.db.get_single_value('Non Profit Settings', 'default_donor_type')

	donor = frappe.new_doc('Donor')
	donor.update({
		'donor_name': donor_details.email,
		'donor_type': donor_type,
		'email': donor_details.email,
		'contact': donor_details.contact
	})

	if donor_details.get('notes'):
		donor = get_additional_notes(donor, donor_details)

	donor.insert(ignore_mandatory=True)
	return donor

def get_company_for_donations():
	company = frappe.db.get_single_value('Non Profit Settings', 'donation_company')
	if not company:
		from non_profit.non_profit.utils import get_company
		company = get_company()
	return company

def get_additional_notes(donor, donor_details):
	if type(donor_details.notes) == dict:
		for k, v in donor_details.notes.items():
			notes = '\n'.join('{}: {}'.format(k, v))

			# extract donor name from notes
			if 'name' in k.lower():
				donor.update({
					'donor_name': donor_details.notes.get(k)
				})

			# extract pan from notes
			if 'pan' in k.lower():
				donor.update({
					'pan_number': donor_details.notes.get(k)
				})

		donor.add_comment('Comment', notes)

	elif type(donor_details.notes) == str:
		donor.add_comment('Comment', donor_details.notes)

	return donor

def create_mode_of_payment(method):
	frappe.get_doc({
		'doctype': 'Mode of Payment',
		'mode_of_payment': method
	}).insert(ignore_mandatory=True)

def notify_failure(log):
	try:
		content = '''
			Dear System Manager,
			Razorpay webhook for creating donation failed due to some reason.
			Please check the error log linked below
			Error Log: {0}
			Regards, Administrator
		'''.format(get_link_to_form('Error Log', log.name))

		sendmail_to_system_managers(_('[Important] [ERPNext] Razorpay donation webhook failed, please check.'), content)
	except Exception:
		pass

@frappe.whitelist()
def no_donation_by_volunteers():
	cur_date = getdate()
	month_start = get_first_day(cur_date) 
	month_end = get_last_day(cur_date)
	month_name = formatdate(cur_date, 'MMM')

	no_donations = frappe.db.sql('''
		select 
			v.name, v.mobile_no, d.name
		from 
			`tabVolunteer` v inner join `tabDonation` d on (v.name!=d.party)
		where 
			v.status='Approved' 
			and d.docstatus=1
			and v.mobile_no is not null
			and d.date between %(month_start)s and %(month_end)s
		group by 
			v.name
		''', {
			'month_start': month_start,
			'month_end': month_end,
			}, as_dict=1)
	
	sms_text = frappe.db.get_single_value('Non Profit Settings', 'sms_text')
	
	receivers_list = []
	for d in no_donations:
		mobile_no = str(d.mobile_no).replace("-", "")
		receivers_list.append(mobile_no)
	
	send_sms(receivers_list, sms_text%{'month_name': month_name})