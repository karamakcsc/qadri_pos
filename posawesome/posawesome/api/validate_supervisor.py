import frappe
from frappe import _
from frappe.utils import now_datetime

@frappe.whitelist()
def validate_supervisor_credentials(username, password, pos_profile, action):
    """
    Validate supervisor using either username or email.
    """
    try:
        from frappe.auth import check_password

        # Determine if input is an email or username
        user_id = None

        # Try to find the user by email first
        if frappe.db.exists("User", username):
            user_id = username
        else:
            # Then try by username field
            user_id = frappe.db.get_value("User", {"username": username}, "name")

        if not user_id:
            return {"success": False, "error": _("Invalid username or email")}

        # Verify password
        try:
            check_password(user_id, password)
        except frappe.AuthenticationError:
            return {"success": False, "error": _("Invalid username or password")}

        # Fetch user doc
        user = frappe.get_doc("User", user_id)

        # Check if user is enabled
        if not user.enabled:
            return {"success": False, "error": _("User account is disabled")}

        # Verify supervisor permission in POS Profile
        pos_doc = frappe.get_doc("POS Profile", pos_profile)
        is_allowed_supervisor = False

        if hasattr(pos_doc, "custom_pos_supervisor"):
            is_allowed_supervisor = any(
                d.supervisor == user.name for d in pos_doc.custom_pos_supervisor
            )

        if not is_allowed_supervisor:
            return {
                "success": False,
                "error": _("User does not have supervisor permissions for this POS Profile"),
            }

        # Log authorization
        create_authorization_log(
            supervisor=user.name,
            pos_profile=pos_profile,
            action=action,
            status="Approved",
        )

        return {
            "success": True,
            "message": _("Authorization successful"),
            "supervisor": {
                "name": user.name,
                "full_name": user.full_name,
                "email": user.email,
            },
        }

    except Exception:
        frappe.log_error(
            title="Supervisor Authentication Error",
            message=frappe.get_traceback(),
        )
        return {"success": False, "error": _("An error occurred during authentication")}


def create_authorization_log(supervisor, pos_profile, action, status):
    try:     
        frappe.get_doc({
            "doctype": "POS Authorization Log",
            "supervisor": supervisor,
            "pos_profile": pos_profile,
            "action": action,
            "status": status,
            "timestamp": now_datetime()
        }).insert(ignore_permissions=True)
        
    except Exception as e:
        frappe.log_error(
            title="Authorization Log Error",
            message=str(e)
        )


@frappe.whitelist()
def get_available_supervisors(pos_profile):
    try:
        supervisors = frappe.get_all(
            "Has Role",
            filters={
                "role": "POS Discount Supervisor",
                "parenttype": "User"
            },
            fields=["parent as user"]
        )
        
        supervisor_list = []
        for sup in supervisors:
            user = frappe.get_doc("User", sup.user)
            if user.enabled:
                supervisor_list.append({
                    "value": user.name,
                    "title": f"{user.full_name} ({user.email})",
                    "email": user.email,
                    "full_name": user.full_name
                })
        
        return supervisor_list
        
    except Exception as e:
        frappe.log_error(
            title="Get Supervisors Error",
            message=frappe.get_traceback()
        )
        return []