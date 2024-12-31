from __future__ import unicode_literals
from frappe import _
import frappe

def execute(filters=None):
    columns, data = get_columns(), get_data(filters)
    return columns, data

def get_columns():
    columns = [
           {
            "label": _("Donor ID"),
            "fieldname": "d_name",
            "fieldtype": "Link",
            "options": "Donor",
            "width": 240,
        },
         {
            "label": _("Proscribed Person ID"),
            "fieldname": "p_name",
            "fieldtype": "Link",
            "options": "Proscribed Person",
            "width": 240,
        },
        {
            "label": _("Name"),
            "fieldname": "name1",
            "fieldtype": "data",
     
            "width": 240,
        },
        {
            "label": _("Father Name"),
            "fieldname": "father_name",
            "fieldtype": "Data",
            "width": 250
        },
        {
            "fieldname": "cnic",
            "label": _("CNIC"),
            "fieldtype": "Data",
            "width": 250
        }
    ]
    return columns

def get_data(filters):
    conditions = get_conditions(filters)
    return frappe.db.sql(f"""
        SELECT
            d.name as d_name,
            p.name as p_name,
            p.name1,
            p.father_name,
            p.cnic
        FROM
            `tabProscribed Person` p
        JOIN
            `tabDonor` d
        ON
            REPLACE(p.cnic, '-', '') = REPLACE(d.cnic, '-', '')
        WHERE
            1 = 1
            {conditions}
        ORDER BY
            d.creation ASC
        """, filters, as_dict=1)



def get_conditions(filters):
    conditions = ""

    if filters.get("cnic"):
        conditions += " AND p.cnic LIKE %(cnic)s"
        filters["cnic"] = f"%{filters['cnic']}%"  

    return conditions
