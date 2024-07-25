import traceback
import os, json
from utils.db import MSSQLConnection
import pandas as pd

db = MSSQLConnection()
import datetime


class Deepdive:
    def __init__(self):
        self.base_path = "data"

    def read_json(self, filename):
        json_object = dict()
        try:
            if os.path.isfile(self.base_path + "\\" + filename):
                with open(self.base_path + "\\" + filename, 'r', encoding='utf-8') as openfile:
                    # Reading from json file
                    json_object = json.load(openfile)
        except Exception as e:
            print(e)
        finally:
            return json_object

    def get_countries(self, data):  # tbd
        try:

            user = data["user"]
            if user["type"].strip() != "admin":
                print("in if")
                users = db.select(f"SELECT c.id,c.name as country, c.code FROM [app].[country] c join [app].[access] a "
                                  f"on c.id=a.[country_id] where a.user_id='{user['id']}'")
            else:
                print("in else")
                users = db.select(f"SELECT [id],[name],[code]FROM [app].[country]")
            print(users)
            return True, "access countries", users
        except Exception as e:
            print("Deepdive.data_by_country(): " + str(e))
            traceback.print_exc()
            return False, "Something went wrong"

    def get_negative_news(self, title, hco_news, hcp_news, color):

        if color == "#fb7e81":
            for article in hco_news:
                if (article['hco'] == title) and (article["sentiment"].lower() == "negative." or article["sentiment"].lower() == "negative"):
                    return True

        if color == "#95c0f9":
            for article in hcp_news:

                if (article['hcp'] == title) and (article["sentiment"].lower() == "negative." or article["sentiment"].lower() == "negative"):
                    return True

        return False

    def graph_by_country(self, data):
        """ Graph with selectable org type. If only HCOs or HCPs are selected,
            pairs of edges are joined between them if there is a common middle node """
        try:
            print(data)
            country = data['country']
            conn = data.get('connection')
            link = data.get('link')
            org = data.get('orgType')
            if country == 'null':
                return True, "graph_by_country", []

            # get payment range
            currency_mapping = {'usa': 'USD', 'brazil': 'BRL', 'spain': 'EUR'}
            # set default minimum to 1 and default to no max
            payment_min = data['min'] if (data['min'] not in ('0', 'null')) else 1 #(10000 if country == 'usa' else 5000)
            payment_max = data['max'] if (data['max'] not in ('0', 'null')) else None 

            # query nodes and edges
            edgeSource = 'vAllEdges' if conn == 'weak' else 'vStrongEdges'

            # get all nodes from selected country with amount and indicator for payment range
            
            # condition for inPaymentRange; add 1 to capture fractions
            query_ext = f' and PaymentAmount <= ({payment_max} + 1)' if payment_max is not None else ''
            
            # condition for node type - HCO ids start with a country initial
            if org == 'hco':
                org_ext = f" and [NodeType] = 'HCO'" 
            elif org == 'hcp':
                org_ext = f" and [NodeType] = 'HCP'"
            else:
                org_ext = ''

            query = f"select [id] as [node_id], [Name] as VendorName, PaymentAmount, InteractionCount, \
                      case when PaymentAmount >= {payment_min}" + query_ext + f" then 1 else 0 end as [inPaymentRange], \
                      [NodeType] \
                      FROM [app2].[vAllNodes] \
                      WHERE country = '{country}'" + org_ext

            all_nodes = db.select_df(query)
            
            # set base nodes as nodes connected to GSK
            # base_nodes = all_nodes[(all_nodes['PaymentAmount'] > 0) | (all_nodes['InteractionCount'] > 0)]
            # too many HCPs with interaction but no payments
            base_nodes = all_nodes[(all_nodes['PaymentAmount'] > 0)]
            
            payment_max = base_nodes['PaymentAmount'].max() if payment_max is None else payment_max
            
            # get edges between nodes in selected country
            # if org is hcp or hco only, collapse edge pairs where there is a middle node in common
            subqueryA = f"select hco_id, hcp_id from [app2].{edgeSource} where country = '{country}'"

            if org == 'hco':
                # allow multiple edges between two HCO to enable increased thickness for multiple connections
                query = f'with t1 as ({subqueryA}) \
                        select A.[hco_id] as [from_id], B.[hco_id] as [to_id] from t1 A \
                        inner join t1 B on A.hcp_id = B.hcp_id where A.hco_id < B.hco_id'
            elif org == 'hcp':
                query = f'with t1 as ({subqueryA}) \
                        select distinct A.[hcp_id] as [from_id], B.[hcp_id] as [to_id] from t1 A \
                        inner join t1 B on A.hco_id = B.hco_id where A.hcp_id < B.hcp_id'
            else:
                # only include edges where the hcp can join two different hcos
                # or where the hcp has payments
                query = f'with t1 as ({subqueryA}) \
                        select distinct A.[hcp_id] as [from_id], A.[hco_id] as [to_id] from t1 A \
                        inner join t1 B on A.hcp_id = B.hcp_id where A.hco_id <> B.hco_id \
                        union \
                        select distinct A.[hcp_id] as [from_id], A.[hco_id] as [to_id] from t1 A \
                        inner join [app2].[vHcp] B on A.hcp_id = B.ID and b.PaymentCount > 0'

            orgType_edges = db.select_df(query)

            # join to the base nodes 
            orgType_edges = orgType_edges.merge(
                base_nodes[['node_id', 'inPaymentRange']], how='left', left_on=['from_id'], right_on=['node_id']
            )
            orgType_edges = orgType_edges.merge(
                base_nodes[['node_id', 'inPaymentRange']], how='left', left_on=['to_id'], right_on=['node_id'],
                suffixes=['_from', '_to']
            )
            
            # filter to include only edges either to or from one of the base nodes
            orgType_edges = orgType_edges[~(pd.isna(orgType_edges['node_id_from'])) | ~(pd.isna(orgType_edges['node_id_to'])) ]


            # look for additional nodes that join to an in-scope edge but are not in the base nodes
            additional_nodes = all_nodes.merge(
                orgType_edges[pd.isna(orgType_edges['node_id_from'])][['from_id']].drop_duplicates(), how='left', left_on=['node_id'], right_on=['from_id']
            )
            additional_nodes = additional_nodes.merge(
                orgType_edges[pd.isna(orgType_edges['node_id_to'])][['to_id']].drop_duplicates(), how='left', left_on=['node_id'], right_on=['to_id']
            )
            additional_nodes = additional_nodes[~(pd.isna(additional_nodes['from_id'])) | ~(pd.isna(additional_nodes['to_id'])) ]


            # node has page, shape, color, id, label, title, designation
            # edge has from, to, page
            nodes_list = []
            edges_list = []

            # Test removing GSK node
            # x = {
            #     "id": str(10001),
            #     "x": 0,
            #     "y": 0,
            #     "fixed": {
            #         "x": True,
            #         "y": True
            #     },
            #     "label": "GSK",
            #     "title": "GSK",
            #     "color": "#fdfd00",
            #     "size": 100,
            #     "shape": "image",
            #     "image": "https://www.mxp-webshop.de/media/image/20/82/24/GSK-Logo.png"
            # }
            # nodes_list.append(x)

            for rowIndex, row in base_nodes.iterrows():
                node_dict = dict()
                node_dict['page'] = 1
                node_dict['id'] = row['node_id']
                node_dict['shape'] = 'dot'
                if row['NodeType'] == 'HCO':
                    node_dict['color'] = "#fb7e81"
                else:
                    node_dict['color'] = "#95c0f9"
                node_dict['label'] = row['VendorName']
                node_dict['title'] = row['VendorName']
                node_dict['designation'] = ""
                node_dict['size'] = 50 if row['inPaymentRange'] == 1 else 10
                nodes_list.append(node_dict)

            for rowIndex, row in additional_nodes.iterrows():
                node_dict = dict()
                node_dict['page'] = 1
                node_dict['id'] = row['node_id']
                node_dict['shape'] = 'dot'
                if row['NodeType'] == 'HCO':
                    node_dict['color'] = "#fb7e81"
                else:
                    node_dict['color'] = "#95c0f9"
                node_dict['label'] = row['VendorName']
                node_dict['title'] = row['VendorName']
                node_dict['designation'] = ""
                node_dict['size'] = 50 if row['inPaymentRange'] == 1 else 10
                nodes_list.append(node_dict)

            for rowIndex, row in orgType_edges.iterrows():
                edge_dict = dict()
                edge_dict['from'] = row['from_id']
                edge_dict['to'] = row['to_id']
                edge_dict['page'] = 1
                #edge_dict['width'] = row['inPaymentRange_from'] + row['inPaymentRange_to'] + 1
                edges_list.append(edge_dict)

            final_result = dict()
            graph = dict()

            graph['nodes'] = nodes_list
            graph['edges'] = edges_list
            graph['price_range'] = [1, int(payment_max)]
            final_result['counter'] = 5
            final_result['graph'] = graph
            final_result['events'] = {}

            if link.lower() == 'negative' :
                neg_nodes_list = []
                neg_nodes_list.append(x)
                with open("./data/outputhco.json", encoding='latin-1') as inputfile:
                    hco_news = json.load(inputfile)
                with open("./data/NewhcpNewsHeadlines.json", encoding='latin-1') as inputfile:
                    hcp_news = json.load(inputfile)
                for i in nodes_list:
                    isNegative = self.get_negative_news(i["title"], hco_news, hcp_news, i["color"])
                    if isNegative:
                        neg_nodes_list.append(i)
                graph['nodes'] = neg_nodes_list
            return True, "graph_by_country", final_result
        except Exception as e:
            print("Deepdive.graph_by_country(): " + str(e))
            traceback.print_exc()
            return False, "Something went wrong"

    def graph_by_node(self, data):
        try:
            # _ret = self.read_json("subGraph.json")
            # return True, "graph_by_node", _ret
            iden = data['id']
            conn = data.get('connection')
            
            if iden == 'null':
                True, "null_data", []
            
            # query nodes and edges
            edgeSource = 'vAllEdges' if conn == 'weak' else 'vStrongEdges'

            if 'B' in iden or 'S' in iden or 'U' in iden:
                sameTypeId = 'hco_id'
                otherTypeId = 'hcp_id'
            else:
                sameTypeId = 'hcp_id'
                otherTypeId = 'hco_id'

            query = f"SELECT  NULL as from_id \
                            ,[ID] as to_id \
                            ,[COUNTRY] \
                            ,[Name] \
                            ,[NodeType] \
                            ,[PaymentCount] \
                            ,10001 as 'gsk' \
                      FROM [app2].[vAllNodes] \
                      WHERE [ID] = '{iden}' \
                      UNION \
                      SELECT e.[{sameTypeId}] as [from_id] \
                            ,e.[{otherTypeId}] as [to_id] \
                            ,n.[COUNTRY] \
                            ,n.[Name] \
                            ,n.[NodeType] \
                            ,n.[PaymentCount] \
                            ,10001 as 'gsk' \
                      FROM [app2].[{edgeSource}] e \
                      INNER JOIN [app2].[vAllNodes] n \
                      ON e.[{otherTypeId}] = n.[ID] \
                      WHERE e.[{sameTypeId}] = '{iden}' \
                      UNION \
                      SELECT e2.[{otherTypeId}] as [from_id] \
                            ,e2.[{sameTypeId}] as [to_id] \
                            ,n.[COUNTRY] \
                            ,n.[Name] \
                            ,n.[NodeType] \
                            ,n.[PaymentCount] \
                            ,10001 as 'gsk' \
                      FROM [app2].[{edgeSource}] e1 \
                      INNER JOIN [app2].[{edgeSource}] e2 \
                      ON e1.[{otherTypeId}] = e2.[{otherTypeId}] \
                      AND e1.[{sameTypeId}] <> e2.[{sameTypeId}] \
                      INNER JOIN [app2].[vAllNodes] n \
                      ON e2.[{sameTypeId}] = n.[ID] \
                      WHERE e1.[{sameTypeId}] = '{iden}'"

            edgesAndNodes = db.select_df(query)

            # everything in the result set should be a node
            nodes = edgesAndNodes[['to_id', 'Name', 'NodeType']].drop_duplicates()

            # every node with payments should get a GSK edge
            gskEdges = edgesAndNodes[(edgesAndNodes['PaymentCount'] > 0)][['gsk', 'to_id']].drop_duplicates()

            # every result row with a from_id should become an edge
            otherEdges = edgesAndNodes[~(pd.isna(edgesAndNodes['from_id']))][['from_id', 'to_id']].drop_duplicates()

            edges_list = []
            for i, row in gskEdges.iterrows():
                edge_dict = dict()
                edge_dict['from'] = row['gsk']
                edge_dict['to'] = row['to_id']
                edges_list.append(edge_dict)

            for i, row in otherEdges.iterrows():
                edge_dict = dict()
                edge_dict['from'] = row['from_id']
                edge_dict['to'] = row['to_id']
                edges_list.append(edge_dict)

            print(edges_list)

            node_list = []

            x = {
                "id": str(10001),
                "x": 0,
                "y": 0,
                "fixed": {
                    "x": True,
                    "y": True
                },
                "label": "GSK",
                "title": "GSK",
                "color": "#fdfd00",
                "size": 75,
                "shape": "image",
                "image": "https://www.mxp-webshop.de/media/image/20/82/24/GSK-Logo.png"
            }
            node_list.append(x)

            for i, row in nodes.iterrows():
                node_dict = dict()
                node_dict['page'] = 1
                node_dict['shape'] = 'dot'
                if row['NodeType'] == 'HCO':
                    node_dict['color'] = "#fb7e81"
                else:
                    node_dict['color'] = "#95c0f9"
                node_dict['id'] = row['to_id']
                node_dict['label'] = row['Name']
                node_dict['title'] = row['Name']
                node_dict['designation'] = ""
                node_list.append(node_dict)
            
            final_result = dict()
            graph = dict()

            graph['nodes'] = node_list
            graph['edges'] = edges_list
            graph['pagination'] = {'first_page': 1, 'last_page': 1}
            final_result['counter'] = 5
            final_result['graph'] = graph
            final_result['events'] = {}

            _ret = final_result

            return True, "graph_by_node", _ret
        except Exception as e:
            print("Deepdive.graph_by_node(): " + str(e))
            traceback.print_exc()
            return False, "Something went wrong"

    def timeline(self, data):  # tbd
        try:
            # YOUR CODE HERE
            # REMOVE THIS ONCE IMPLEMENTED
            # _ret = self.read_json("chronology.json")
            # return True, "timeline", _ret
            timeline_list = []
            iden = data['id']
            if iden == 'null':
                True, "null_data", []

            if 'B' in data['id'] or 'S' in data['id'] or 'U' in data['id']:
                query = f"select HCO, payment_hco_id from [app2].[vHco] where ID = '{iden}'"
                db = MSSQLConnection()
                entity = db.select_df(query)
                for i, row in entity.iterrows():
                    entity_name = row['HCO']
                    payment_id = row['payment_hco_id']
                    break
                with open("./data/outputhco.json", encoding='latin-1') as inputfile:
                    hco_news = json.load(inputfile)

                for article in hco_news:
                    if article['hco'] == entity_name:
                        event_dict = dict()
                        event_dict["id"] = data['id']
                        event_dict["tag"] = article['hco'] + ' : ' + ' External News Event'
                        event_dict["category"] = 'External News Event'
                        event_dict['date'] = article['date']
                        event_dict['sortdate'] = datetime.date.fromtimestamp(
                            datetime.datetime.strptime(article['date'], "%Y-%m-%d").timestamp())
                        event_dict['description'] = article['link']
                        timeline_list.append(event_dict)
            else:
                db = MSSQLConnection()
                query = f"select hcp_name, payment_hcp_id from [app2].[vHcp] where Id = '{iden}'"
                entity = db.select_df(query)
                for i, row in entity.iterrows():
                    entity_name = row['hcp_name']
                    payment_id = row['payment_hcp_id']
                    break
                with open("./data/NewhcpNewsHeadlines.json", encoding='latin-1') as inputfile:
                    hco_news = json.load(inputfile)

                for article in hco_news:
                    if article['hcp'] == entity_name:
                        event_dict = dict()
                        event_dict["id"] = data['id']
                        event_dict["tag"] = article['hco'] + ' : ' + article['hcp'] + ' : ' + ' External News Event'
                        event_dict["category"] = 'External News Event'
                        event_dict['date'] = article['date']
                        event_dict['sortdate'] = datetime.date.fromtimestamp(
                            datetime.datetime.strptime(article['date'], "%Y-%m-%d").timestamp())
                        event_dict['description'] = article['link']
                        timeline_list.append(event_dict)
            import time
            time.sleep(1)  # testing reduced time here; was 5
            # interactions:
            db = MSSQLConnection()
            query = f"SELECT [InteractionType],[InteractionSubtype],[InteractionTopic],[ParentCallId],[InteractionStart],[HcpName] FROM [app2].[vInteractions] where [ID] = '{iden}' order by [InteractionStart]"
            interactions = db.select_df(query)
            if not interactions.empty:
                for i, row in interactions.iterrows():
                    event_dict = dict()
                    event_dict["id"] = data['id']
                    event_dict["tag"] = row['InteractionSubtype'] + ' with ' + row["HcpName"]
                    event_dict["category"] = row['InteractionType']
                    event_dict['date'] = str(row['InteractionStart'])
                    event_dict['sortdate'] = row['InteractionStart']
                    event_dict['description'] = row['ParentCallId'] + ' | ' + row['InteractionTopic']
                    timeline_list.append(event_dict)

            # payments
            query = f"SELECT [ThirdPartyPaymentsLineId],[InvoiceGlDate],[PaymentType],[PaymentSubtype],[InvoiceLineAmountLocal],[AllText],[Currency],\
                        [VendorNumber],[VendorName] FROM [app2].[vPayments] where [VendorNumber] = '{payment_id}' order by [InvoiceGlDate]"
            payments = db.select_df(query)
            if not payments.empty:
                for i, row in payments.iterrows():
                    event_dict = dict()
                    event_dict["id"] = data['id']
                    event_dict["tag"] = row['PaymentSubtype'] + ' for ' + row["VendorName"]
                    event_dict["category"] = row['PaymentType']
                    event_dict['date'] = str(row['InvoiceGlDate'])
                    event_dict['sortdate'] = row['InvoiceGlDate']
                    event_dict['description'] = '{:,.2f}'.format(row['InvoiceLineAmountLocal']) + ' ' + str(row['Currency']) + ' | ' + row['AllText'] # format with thousands separaters and 2dp
                    timeline_list.append(event_dict)

            newlist = sorted(timeline_list, key=lambda d: d['sortdate'])
            _ret = newlist
            return True, "timeline", _ret

        except Exception as e:
            print("Deepdive.timeline(): " + str(e))
            traceback.print_exc()
            return False, "Something went wrong"

    def ext_events(self, data):  # tbd
        try:
            # YOUR CODE HERE
            # REMOVE THIS ONCE IMPLEMENTED
            # _ret = self.read_json("eventTimeline.json")
            iden = data['id']
            if iden == 'null':
                True, "null_data", []

            timeline_list = []
            if 'B' in data['id'] or 'S' in data['id'] or 'U' in data['id']:
                query = f"select HCO from [app2].[vHco] where ID = '{iden}'"
                db = MSSQLConnection()
                entity = db.select_df(query)
                for i, row in entity.iterrows():
                    entity_name = row['HCO']
                    break
                with open("./data/outputhco.json", encoding='latin-1') as inputfile:
                    hco_news = json.load(inputfile)

                for article in hco_news:
                    if article['hco'] == entity_name:
                        event_dict = dict()
                        event_dict["id"] = data['id']
                        event_dict["title"] = article['title']
                        event_dict["hco"] = article['hco']
                        event_dict['source'] = article['source']
                        event_dict['date'] = article['date']
                        event_dict['link'] = article['link']
                        event_dict['country'] = article['country']
                        event_dict['collaborators'] = ''
                        event_dict['category'] = article['category']
                        event_dict['sentiment'] = article['sentiment']
                        event_dict['flag'] = 'HCO'
                        timeline_list.append(event_dict)
            else:
                query = f"select hcp_name from [app2].[vHcp] where Id = '{iden}'"
                db = MSSQLConnection()
                entity = db.select_df(query)
                for i, row in entity.iterrows():
                    entity_name = row['hcp_name']
                    break
                with open("./data/NewhcpNewsHeadlines.json", encoding='latin-1') as inputfile:
                    hco_news = json.load(inputfile)

                for article in hco_news:
                    if article['hcp'] == entity_name:
                        event_dict = dict()
                        event_dict["id"] = data['id']
                        event_dict["title"] = article['title']
                        event_dict["hco"] = article['hco']
                        event_dict["hcp"] = article['hcp']
                        event_dict['source'] = article['source']
                        event_dict['date'] = article['date']
                        event_dict['link'] = article['link']
                        event_dict['country'] = article['country']
                        event_dict['collaborators'] = ''
                        event_dict['category'] = article['category']
                        event_dict['sentiment'] = article['sentiment']
                        event_dict['flag'] = "HCP"

                        timeline_list.append(event_dict)
            _ret = timeline_list

            return True, "ext_events", _ret
        except Exception as e:
            print("Deepdive.ext_events(): " + str(e))
            traceback.print_exc()
            return False, "Something went wrong"

    def overview(self, data):  # tbd
        try:
            # YOUR CODE HERE
            # REMOVE THIS ONCE IMPLEMENTED
            return_dict = dict()
            iden = data['id']
            if iden == 'null':
                True, "null_data", []

            currency_mapping = {'usa': 'USD', 'brazil': 'BRL', 'spain': 'EUR'}

            query = f"select ID, [Name], PaymentAmount, InteractionCount, LOWER(Country) as Country from [app2].[vAllNodes] where ID = '{iden}'"
            db = MSSQLConnection()
            entity = db.select_df(query)
            if not entity.empty:
                for i, row in entity.iterrows():
                    payment_amount = row['PaymentAmount']
                    total_interactions = row['InteractionCount']
                    entity_name = row['Name']
                    currency = currency_mapping[row['Country']]
                    break

            return_dict['totalPaymentMade'] = '{:,.2f}'.format(payment_amount) + ' ' + currency # format with thousands separaters and 2dp

            return_dict['totalInteraction'] = str(total_interactions)
            return_dict['selectedName'] = entity_name
            print(return_dict, '00000000000000000000000000000000000000000000000000000000000000')
            if 'B' in data['id'] or 'S' in data['id'] or 'U' in data['id']:
                with open("./data/outputhco.json", encoding='latin-1') as inputfile:
                    hco_news = json.load(inputfile)
                i = 0
                for article in hco_news:
                    if article['hco'] == entity_name:
                        i += 1
                print(i, "total media articles")
            else:
                with open("./data/NewhcpNewsHeadlines.json", encoding='latin-1') as inputfile:
                    hco_news = json.load(inputfile)
                i = 0
                for article in hco_news:
                    if article['hcp'] == entity_name:
                        i += 1
            return_dict['mediaArticles'] = str(i)
            return_dict['riskIdentified'] = str(0)
            _ret = [return_dict]

            print(_ret)
            # _ret = self.read_json("overview.json")
            return True, "overview", _ret
        except Exception as e:
            print("Deepdive.overview(): " + str(e))
            traceback.print_exc()
            return False, "Something went wrong"
