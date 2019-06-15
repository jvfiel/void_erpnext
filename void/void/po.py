import frappe
from frappe.model.dynamic_links import get_dynamic_link_map

@frappe.whitelist()
def void_so(docname):
    # def remove_imported_data(file, force=0):


    submit_dn = frappe.db.sql_list("""
    		select DISTINCT t1.name
    		from `tabPurchase Receipt` t1,`tabPurchase Receipt Item` t2
    		where t1.name = t2.parent and t2.purchase_order = %s and t1.docstatus = 1""", docname)

    # if submit_dn:
    #     frappe.throw(_("Delivery Notes {0} must be cancelled before cancelling this Sales Order")
    #                  .format(comma_and(submit_dn)))
    if submit_dn:
        for dn in submit_dn:
            print dn
            frappe.get_doc("Purchase Receipt", dn).cancel()
            frappe.db.commit()

    # Checks Sales Invoice
    submit_rv = frappe.db.sql_list("""select DISTINCT t1.name
    		from `tabPurchase Invoice` t1,`tabPurchase Invoice Item` t2
    		where t1.name = t2.parent and t2.purchase_order = %s and t1.docstatus = 1""",
                                   docname)

    if submit_rv:
        for dn in submit_rv:
            print dn
            si = frappe.get_doc("Purchase Invoice", dn)

            exists_pe = frappe.db.sql("""select DISTINCT t1.name from `tabPayment Entry` t1, `tabPayment Entry Reference` t2
                                    where t1.name = t2.parent and t2.reference_name=%s and t1.docstatus=1""",si.name)
            if exists_pe:
                for pe in exists_pe:
                    print pe[0]
                    frappe.get_doc("Payment Entry",pe[0]).cancel()
                    exists_pr = frappe.db.sql("""select DISTINCT t1.name from `tabPayment Request` t1
                                                                  where t1.reference_name=%s and t1.docstatus=1""",
                                              si.name)
                    if exists_pr:
                        frappe.get_doc("Payment Entry",pe[0]).delete()
                    frappe.db.commit()
                    print "cancelled pe..."

            exists_pe = frappe.db.sql("""select DISTINCT t1.name from `tabPayment Request` t1
                                               where t1.reference_name=%s and t1.docstatus=1""",
                                      si.name)
            if exists_pe:
                for pe in exists_pe:
                    print pe
                    frappe.get_doc("Payment Request", pe[0]).cancel()
                    frappe.get_doc("Payment Request", pe[0]).delete()
                    frappe.db.commit()
            si.cancel()
            frappe.db.commit()

    exists_pe = frappe.db.sql("""select DISTINCT t1.name from `tabPayment Entry` t1, `tabPayment Entry Reference` t2
                            where t1.name = t2.parent and t2.reference_name=%s and t1.docstatus=1""", docname)
    if exists_pe:
        for pe in exists_pe:
            print pe[0]
            frappe.get_doc("Payment Entry", pe[0]).cancel()
            exists_pr = frappe.db.sql("""select DISTINCT t1.name from `tabPayment Request` t1
                                                                             where t1.reference_name=%s and t1.docstatus=1""",
                                      docname)
            if exists_pr:
                frappe.get_doc("Payment Entry", pe[0]).delete()
            frappe.db.commit()
            print "cancelled pe..."

    exists_pe = frappe.db.sql("""select DISTINCT t1.name from `tabPayment Request` t1
                                       where t1.reference_name=%s and t1.docstatus=1""",
                              docname)
    if exists_pe:
        for pe in exists_pe:
            print pe
            frappe.get_doc("Payment Request", pe[0]).cancel()
            frappe.get_doc("Payment Request", pe[0]).delete()
            frappe.db.commit()


    frappe.get_doc("Purchase Order", docname).cancel()

    return True


def check_if_doc_is_linked(doc, method="Delete"):
    """
        Raises excption if the given doc(dt, dn) is linked in another record.
    """
    from frappe.model.rename_doc import get_link_fields
    link_fields = get_link_fields(doc.doctype)
    link_fields = [[lf['parent'], lf['fieldname'], lf['issingle']] for lf in link_fields]

    for link_dt, link_field, issingle in link_fields:
        if not issingle:
            for item in frappe.db.get_values(link_dt, {link_field: doc.name},
                                             ["name", "parent", "parenttype", "docstatus"], as_dict=True):
                linked_doctype = item.parenttype if item.parent else link_dt
                if linked_doctype in (
                "Communication", "ToDo", "DocShare", "Email Unsubscribe", 'File', 'Version', "Activity Log"):
                    # don't check for communication and todo!
                    continue

                if not item:
                    continue
                elif (method != "Delete" or item.docstatus == 2) and (method != "Cancel" or item.docstatus != 1):
                    # don't raise exception if not
                    # linked to a non-cancelled doc when deleting or to a submitted doc when cancelling
                    continue
                elif link_dt == doc.doctype and (item.parent or item.name) == doc.name:
                    # don't raise exception if not
                    # linked to same item or doc having same name as the item
                    continue
                else:
                    reference_docname = item.parent or item.name
                    # raise_link_exists_exception(doc, linked_doctype, reference_docname)
                    return reference_docname,linked_doctype

        else:
            if frappe.db.get_value(link_dt, None, link_field) == doc.name:
                # raise_link_exists_exception(doc, link_dt, link_dt)
                return link_dt,linked_doctype
    return None,None

def check_if_doc_is_dynamically_linked(doc, method="Delete"):
    '''Raise `frappe.LinkExistsError` if the document is dynamically linked'''
    for df in get_dynamic_link_map().get(doc.doctype, []):
        if df.parent in (
        "Communication", "ToDo", "DocShare", "Email Unsubscribe", "Activity Log", 'File', 'Version', 'View Log'):
            # don't check for communication and todo!
            continue

        meta = frappe.get_meta(df.parent)
        # if meta.issingle:
        #     # dynamic link in single doc
        #     refdoc = frappe.db.get_singles_dict(df.parent)
        #     if (refdoc.get(df.options) == doc.doctype
        #         and refdoc.get(df.fieldname) == doc.name
        #         and ((method == "Delete" and refdoc.docstatus < 2)
        #              or (method == "Cancel" and refdoc.docstatus == 1))
        #         ):
        #         # raise exception only if
        #         # linked to an non-cancelled doc when deleting
        #         # or linked to a submitted doc when cancelling
        #         raise_link_exists_exception(doc, df.parent, df.parent)
        # else:
            # dynamic link in table
        df["table"] = ", parent, parenttype, idx" if meta.istable else ""
        for refdoc in frappe.db.sql("""select name, docstatus{table} from `tab{parent}` where
            {options}=%s and {fieldname}=%s""".format(**df), (doc.doctype, doc.name), as_dict=True):

            if ((method == "Delete" and refdoc.docstatus < 2) or (method == "Cancel" and refdoc.docstatus == 1)):
                # raise exception only if
                # linked to an non-cancelled doc when deleting
                # or linked to a submitted doc when cancelling

                reference_doctype = refdoc.parenttype if meta.istable else df.parent
                reference_docname = refdoc.parent if meta.istable else refdoc.name
                at_position = "at Row: {0}".format(refdoc.idx) if meta.istable else ""

                # raise_link_exists_exception(doc, reference_doctype, reference_docname, at_position)
                return reference_docname,reference_doctype

    return None,None
