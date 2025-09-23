from frappe import _


def get_dashboard_data(data):
    data["transactions"].append(
        {
            "label": _("Others"), 
            "items": ["Funds Transfer", "Payment Entry"]
        }
    )
    return data
