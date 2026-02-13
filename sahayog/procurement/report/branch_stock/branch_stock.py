import frappe

def execute(filters=None):
    if not filters:
        filters = {}

    warehouse = filters.get("warehouse")

    columns = [
        dict(fieldname="item_code", label="Item Code", fieldtype="Link", options="Item", width=150),
        dict(fieldname="item_name", label="Item Name", fieldtype="Data", width=200),
        dict(fieldname="warehouse", label="Warehouse", fieldtype="Link", options="Warehouse", width=150),
        dict(fieldname="stock_balance", label="Stock Balance", fieldtype="Float", width=120),
        dict(fieldname="select_row", label="Select Items", fieldtype="Data", width=60),
    ]

    # Conditions for the query
    conditions = ["bin.actual_qty != 0"]
    values = {}

    if warehouse:
        # Get the sol_id of the selected custom_warehouse branch
        selected_sol_id = frappe.db.get_value("Branch", {"custom_warehouse": warehouse}, "sol_id")
        if selected_sol_id:
            # Join with Branch to filter all warehouses belonging to this sol_id
            # Note: We match bin.warehouse to custom_warehouse in tabBranch
            conditions.append("exists (select 1 from `tabBranch` br where br.custom_warehouse = bin.warehouse and br.sol_id = %(sol_id)s)")
            values["sol_id"] = selected_sol_id
        else:
            # Fallback to direct warehouse match if no sol_id mapping found
            conditions.append("bin.warehouse = %(warehouse)s")
            values["warehouse"] = warehouse
    else:
        # If no warehouse is selected, only allow Admin or System Manager to see all stock
        user_roles = frappe.get_roles(frappe.session.user)
        if frappe.session.user != "Administrator" and "System Manager" not in user_roles:
            return columns, []

    where_clause = " WHERE " + " AND ".join(conditions)

    query = f"""
        SELECT
            bin.item_code,
            item.item_name,
            bin.warehouse,
            SUM(bin.actual_qty) AS stock_balance,
            '' AS select_row
        FROM `tabBin` bin
        LEFT JOIN `tabItem` item ON bin.item_code = item.name
        {where_clause}
        GROUP BY bin.item_code, item.item_name, bin.warehouse
        HAVING SUM(bin.actual_qty) != 0
        ORDER BY bin.item_code, bin.warehouse
    """

    data = frappe.db.sql(query, values, as_dict=True)
    return columns, data
