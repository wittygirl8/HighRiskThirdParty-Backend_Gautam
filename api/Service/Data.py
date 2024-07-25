import traceback

from utils.db import MSSQLConnection

db = MSSQLConnection()


class Data:
    def __init__(self):
        self.HCO_parent = {}
        self.HCO_payment = {}
        self.US_payment = {}
        self.HCO_child = {}
        self.HCO_interaction = {}
        self.HCO_meeting = {}
        self.HCO_sample = {}

    def populate(self):
        try:
            print("Populating parent and clild")
            hco = db.sql_exec(f"select distinct Parent_Name_vod__c,Parent_Account_vod__c from [dbo].[HCP_2_HCO_US_raw]")
            for each in hco:
                self.HCO_parent[each["Parent_Name_vod__c"]] = each["Parent_Account_vod__c"]
            print(f"{len(self.HCO_parent)} parent found")
            hco = db.sql_exec(f"select distinct Child_Name_vod__c,Child_Account_vod__c from [dbo].[HCP_2_HCO_US_raw]")
            for each in hco:
                self.HCO_child[each["Child_Name_vod__c"]] = each["Child_Account_vod__c"]
            print(f"{len(self.HCO_child)} child found")
            hco = db.sql_exec(f"select distinct HcpName, HcpId from [dbo].[sample_raw]")
            for each in hco:
                self.HCO_sample[each["HcpName"]] = each["HcpId"]
            print(f"{len(self.HCO_sample)} sample found")
            hco = db.sql_exec(f"select distinct HcpName, HcpId from [dbo].[meetings_raw]")
            for each in hco:
                self.HCO_meeting[each["HcpName"]] = each["HcpId"]
            print(f"{len(self.HCO_meeting)} meeting found")
            hco = db.sql_exec(f"select distinct HcpName, HcpId from [dbo].[interactions_raw]")
            for each in hco:
                self.HCO_interaction[each["HcpName"]] = each["HcpId"]
            print(f"{len(self.HCO_interaction)} interactions found")
            return None
        except Exception as e:
            print("Scorecard.populate(): " + str(e))
            traceback.print_exc()
            return None

    def populate_payment(self):
        try:
            hco = db.sql_exec(f"select distinct VendorName, VendorNumber from [dbo].[payments_raw]")  # [mj].[all_tov]
            for each in hco:
                self.HCO_payment[each["VendorName"]] = each["VendorNumber"]
            print(f"{len(self.HCO_payment)} payment found")
            hco = db.sql_exec(f"select distinct VendorName, VendorNumber from [mj].[all_tov]")  # [mj].[all_tov]
            for each in hco:
                self.US_payment[each["VendorName"]] = each["VendorNumber"]
            print(f"{len(self.HCO_payment)} payment found")
            return None
        except Exception as e:
            print("Scorecard.populate_payment(): " + str(e))
            traceback.print_exc()
            return None

    def get_payment_hco_id_by_name(self, name):
        if not len(self.HCO_payment):
            self.populate_payment()
        if name in self.HCO_payment.keys():
            return self.HCO_payment[name]
        if name in self.US_payment.keys():
            return self.US_payment[name]
        return None

    def get_internal_hco_id_by_name(self, name):
        if not len(self.HCO_child):
            self.populate()
        if name in self.HCO_child.keys():
            return self.HCO_child[name]
        if name in self.HCO_parent.keys():
            return self.HCO_parent[name]
        if name in self.HCO_interaction.keys():
            return self.HCO_interaction[name]
        if name in self.HCO_meeting.keys():
            return self.HCO_meeting[name]
        if name in self.HCO_sample.keys():
            return self.HCO_sample[name]
        return None

    def link_internal_hco_2_external(self, data):
        try:
            hco_list = db.sql_exec("select HCO, id, internal_hco_id from app.hco")
            i = 0
            for each in hco_list:
                i += 1
                if not each["internal_hco_id"]:
                    _id = self.get_internal_hco_id_by_name(each["HCO"])
                    if _id:
                        print(f"{len(hco_list)}/{i} found {_id} for {each['HCO']}")
                        conn = db.get_db()
                        cursor = conn.cursor()
                        update_query = f"""
                            UPDATE [app].[hco]
                            SET [internal_hco_id]=?
                            WHERE [ID] = ?
                            """
                        cursor.execute(update_query, (_id, each["id"]))
                        conn.commit()
                        cursor.close()
            hcp_list = db.sql_exec("select [hcp_name], id, internal_hcp_id from app.hcp")
            i = 0
            for each in hcp_list:
                i += 1
                if not each["internal_hcp_id"]:
                    _id = self.get_internal_hco_id_by_name(each["hcp_name"])
                    if _id:
                        print(f"{len(hcp_list)}/{i} found {_id} for {each['hcp_name']}")
                        conn = db.get_db()
                        cursor = conn.cursor()
                        update_query = f"""
                            UPDATE [app].[hcp]
                            SET [internal_hcp_id]=?
                            WHERE [id] = ?
                            """
                        cursor.execute(update_query, (_id, each["id"]))
                        conn.commit()
                        cursor.close()
            return True, 'test', {}
        except Exception as e:
            print("Scorecard.test(): " + str(e))
            traceback.print_exc()
            return False, "Something went wrong"

    def link_payment_hco_2_external(self, data):
        try:
            hco_list = db.sql_exec("select HCO, id, payment_hco_id from app.hco")
            i = 0
            for each in hco_list:
                i += 1
                if not each["payment_hco_id"]:
                    _id = self.get_payment_hco_id_by_name(each["HCO"])
                    if _id:
                        print(f"{len(hco_list)}/{i} found {_id} for {each['HCO']}")
                        conn = db.get_db()
                        cursor = conn.cursor()
                        update_query = f"""
                            UPDATE [app].[hco]
                            SET [payment_hco_id]=?
                            WHERE [ID] = ?
                            """
                        cursor.execute(update_query, (_id, each["id"]))
                        conn.commit()
                        cursor.close()
            hcp_list = db.sql_exec("select [hcp_name], id, payment_hcp_id from app.hcp")
            i = 0
            for each in hcp_list:
                i += 1
                if not each["payment_hcp_id"]:
                    _id = self.get_payment_hco_id_by_name(each["hcp_name"])
                    if _id:
                        print(f"{len(hcp_list)}/{i} found {_id} for {each['hcp_name']}")
                        conn = db.get_db()
                        cursor = conn.cursor()
                        update_query = f"""
                            UPDATE [app].[hcp]
                            SET [payment_hcp_id]=?
                            WHERE [id] = ?
                            """
                        cursor.execute(update_query, (_id, each["id"]))
                        conn.commit()
                        cursor.close()
            return True, 'test', {}
        except Exception as e:
            print("Scorecard.test(): " + str(e))
            traceback.print_exc()
            return False, "Something went wrong"
