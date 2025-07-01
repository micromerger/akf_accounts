# Copyright (c) 2024, Nabeel Saleem and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import re

class Tehsil(Document):
	def validate(self):
		if not re.match("^[A-Z ]+$", self.tehsil_name.upper()):
			frappe.throw("Tehsil Name must contain only alphabets")
