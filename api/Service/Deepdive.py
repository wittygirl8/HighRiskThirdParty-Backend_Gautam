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

    def data_by_country(self, data):  # tbd
        try:
            # YOUR CODE HERE
            # REMOVE THIS ONCE IMPLEMENTED
            # if data["country"].strip().lower() == "brazil":
            #     _ret = self.read_json("brazil.json")
            # if data["country"].strip().lower() == "spain":
            #     _ret = self.read_json("spain.json")
            # if data["country"].strip().lower() == "usa":
            #     _ret = self.read_json("usa.json")
            # TILL HERE
            print(data)
            country = data['country']
            conn = data.get('connection')
            link = data.get('link')
            if country == 'null':
                True, "data_by_country", [] 

            currency_mapping = {'usa' : 'USD', 'brazil': 'BRL', 'spain': 'EUR'}

            query = f"select VendorName, [InvoiceLineAmountLocal], [currency] from mj.all_tov where currency = '{currency_mapping.get(country)}'"
            
            # Execute the query
            payments = db.select_df(query)
            print(payments.shape[0])
            payments['Quartile'] = pd.qcut(payments['InvoiceLineAmountLocal'], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'])

            if (data['min'] == '0' and data['max'] == '0') or (data['min'] == 'null' and data['max'] == 'null') :
                if country == 'usa':
                    min = 10000
                else:
                    min =5000
                max = payments['InvoiceLineAmountLocal'].max()

            else:
                min = int(data['min'])
                max = int(data['max'])

            # payments = payments[payments['InvoiceLineAmountLocal']>=10000]
            
            payments = payments[(payments['InvoiceLineAmountLocal']>=min) & (payments['InvoiceLineAmountLocal']<=max)]
            print(payments.shape[0])
            payments['VendorName'] = payments['VendorName'].str.lower()
            payments = payments[['VendorName']].drop_duplicates()


            edges_list = []

            if conn == 'multiple':
                query = f"select \
                            trim(a.hco_id) as 'from', cast(a.hcp_id as varchar) as 'to', count(*) as 'count' \
                            from app.FactHcpHco a \
                            join \
                            (select hcp_id, count(distinct hco_id) as count_hco from app.FactHcpHco where country = '{country}' group by hcp_id having count(distinct hco_id) > 1)b \
                            on a.hcp_id = b.hcp_id \
                            where a.country = '{country}' \
                            group by trim(a.hco_id), cast(a.hcp_id as varchar) \
                            having count(*) =1"
            else: 
                query = f"select \
                            trim(a.hco_id) as 'from', cast(a.hcp_id as varchar) as 'to', count(*) as 'count' \
                            from app.FactHcpHco a \
                            join \
                            (select hcp_id, count(distinct hco_id) as count_hco from app.FactHcpHco where country = '{country}' group by hcp_id having count(distinct hco_id) >= 1)b \
                            on a.hcp_id = b.hcp_id \
                            where a.country = '{country}' \
                            group by trim(a.hco_id), cast(a.hcp_id as varchar) \
                            having count(*) =1"
            hcp_edges = db.select_df(query)
            print(hcp_edges.shape[0])
            query = f"select distinct cast(Id as varchar) as 'hcp_id', hcp_name from dbo.hcp_info where country = '{country}'"
            hcp_names = db.select_df(query)
            query = f"select distinct trim(ID) as 'hco_id', HCO  as 'hco_name' from app.hco where country = '{country}'"
            hco_names = db.select_df(query) 
            merged_hcp = hcp_edges.merge(hcp_names, how = 'left', left_on = ['to'], right_on = ['hcp_id'])
            merged_hcp['hcp_name'] = merged_hcp['hcp_name'].str.lower()
            merged_hcp_hco = merged_hcp.merge(hco_names, how = 'left', left_on = ['from'], right_on = ['hco_id'])
            merged_hcp_hco['hco_name'] = merged_hcp_hco['hco_name'].str.lower()

            print(merged_hcp_hco.shape[0])

            distinct_hcps = merged_hcp_hco[['to','hcp_name']].drop_duplicates()

            distinct_hcos = merged_hcp_hco[['from','hco_name']].drop_duplicates()
            print(distinct_hcps.shape[0])
            print(distinct_hcos.shape[0])

            merged_hcp_payments = distinct_hcps.merge(payments, how = 'inner', left_on = ['hcp_name'], right_on = ['VendorName'])


            merged_hco_payments = distinct_hcos.merge(payments, how = 'inner', left_on = ['hco_name'], right_on = ['VendorName'])


            print(merged_hcp_payments.shape[0])
            print(merged_hco_payments.shape[0])

            # for those HCPs which do not ahve payments but are a part of the hcos and have multiple connections
            query = f"select \
                            trim(a.hco_id) as 'from', cast(a.hcp_id as varchar) as 'to', count(*) as 'count' \
                            from app.FactHcpHco a \
                            join \
                            (select hcp_id, count(distinct hco_id) as count_hco from app.FactHcpHco where country = '{country}' group by hcp_id having count(distinct hco_id) > 1)b \
                            on a.hcp_id = b.hcp_id \
                            where a.country = '{country}' \
                            group by trim(a.hco_id), cast(a.hcp_id as varchar) \
                            having count(*) =1"

            additional_hcps = db.select_df(query)

            rel_hcps = additional_hcps.merge(merged_hco_payments, how = "inner", left_on = ["from"], right_on = ['from'])

            print(rel_hcps.shape[0])
            print("---------------------------------------------------------------------------------------------------------------")
            print(rel_hcps)
            rel_hcps = rel_hcps[['from','to']]
            print("*******************************************************************************************************************")
            print(rel_hcps)


            merged_hco_payments_edges = merged_hco_payments[['from', 'VendorName']].drop_duplicates()
            print(merged_hco_payments_edges.shape[0])

            merged_hcp_payments_edges = merged_hcp_payments[['to', 'VendorName']].drop_duplicates()
            print(merged_hcp_payments_edges)

            merged_hcp_payments_edges = merged_hcp_payments_edges.rename(columns={'to':'hcp_id_distinct_payments', 'VendorName':'vn_distinct_payments'})

            hcp_edges = merged_hcp_hco.merge(merged_hcp_payments_edges, how = 'inner', left_on = ['to'], right_on = ['hcp_id_distinct_payments'])
            hcp_edges = hcp_edges[['from','to']]
            print(hcp_edges.shape[0])

            final_hcps = pd.concat([hcp_edges,rel_hcps], ignore_index=True).drop_duplicates()
            print("£££££££££££££££££££££££££££££££££££££££££££££££")
            print(final_hcps)
            print(final_hcps.shape[0])

                    
            for i,row in merged_hco_payments_edges.iterrows():
                edges_dict = dict()
                
                edges_dict['to'] = row['from']
                edges_dict['from'] = '10001'
                edges_dict['page'] = 1
                edges_list.append(edges_dict)

            for i,row in hcp_edges.iterrows():
                edges_dict = dict()
                
                edges_dict['to'] = row['to']
                edges_dict['from'] = '10001'
                edges_dict['page'] = 1
                edges_list.append(edges_dict)


            for i,row in final_hcps.iterrows():
                
                hcp_dict = dict()
                hcp_dict["from"] = row['from']
                hcp_dict["to"] = row["to"]
                hcp_dict['page'] = 1
                
                edges_list.append(hcp_dict)
                # print(len(edges_list))
            print(len(edges_list))

            node_list = []

            x = {
                        "id": str(10001),
                        "x": 0,
                        "y": 0,
                        "fixed": {
                            "x": True,
                            "y": True
                        },
                        "label": "Company",
                        "title": "Company",
                        "color": "#fdfd00",
                        "size": 100,
                        "shape": "image",
                        "image": "https://dieselpunkcore.com/wp-content/uploads/2014/06/logo-placeholder.png",
                    }
            node_list.append(x)

            final_edges = pd.concat([merged_hco_payments_edges, final_hcps], ignore_index = True)
            print(final_edges)
            hcos_for_nodes = final_edges[['from']].drop_duplicates()
            hcps_for_nodes = final_edges[['to']].drop_duplicates()

            print(hcos_for_nodes.shape[0], ",", hcps_for_nodes.shape[0])

            query = f"SELECT cast(a.Id as varchar) as 'id', a.hcp_name, a.country, max(b.designation) as 'designation' FROM dbo.hcp_info a \
            join app.FactHcpHco b on a.Id = b.hcp_id where a.country = '{country}' group by cast(a.Id as varchar), a.hcp_name, a.country "
            # Execute the query
            df = db.select_df(query)
            nodes_df = df[['id','hcp_name','designation','country']]

            nodes_merged = hcps_for_nodes.merge(nodes_df, how = 'inner', left_on = ["to"], right_on = ["id"] )
            print(nodes_merged)
            nodes_merged = nodes_merged.drop_duplicates(subset=['id'])

            query = f"select a.COUNTRY, a.HCO, a.ID, max(b.hco_id) from app.hco a join app.FactHcpHco b on a.ID = b.hco_id where a.COUNTRY = '{country}' group by a.COUNTRY, a.HCO, a.ID"

            # Execute the query
            hco_df = db.select_df(query)




            nodes_hco_df = hco_df.rename(columns={'HCO':'label', 'ID':'id', 'COUNTRY':'country'})



            nodes_hco_merged = hcos_for_nodes.merge(nodes_hco_df, how = 'inner', left_on = ["from"], right_on = ["id"] )

            # nodes_merged = nodes_merged.drop_duplicates(subset = ['Id'])
            # nodes_hco_merged = nodes_hco_merged.drop_duplicates(subset = ['id'])

            # print(nodes_merged)
            # print(nodes_hco_merged)
            a = 0
            for i,row in nodes_hco_merged.iterrows():
                a+=1
                node_hco_dict = dict()
                node_hco_dict['page'] = 1
                
                node_hco_dict['shape'] = 'dot'
                node_hco_dict['color'] = "#fb7e81"
                node_hco_dict['id'] = row['id']
                node_hco_dict['label'] = row['label']
                node_hco_dict['title'] = row['label']
                node_hco_dict['designation'] = ""
                node_list.append(node_hco_dict)
            print(f"number of hco nodes is {a}")
            b = 0
            for i,row in nodes_merged.iterrows():
                if row['to'] == 'NaN':
                    print("if in")
                    continue
                b+=1
                node_dict = dict()
                node_dict['shape'] = 'dot'
                node_dict['color'] = "#95c0f9"
                node_dict['id'] = row['id']
                node_dict['label'] = row['hcp_name']
                node_dict['title'] = row['hcp_name']
                node_dict['designation'] = row['designation']
                node_dict['page'] = 1
                
                node_list.append(node_dict)
            print(f"number of hcp nodes is {b}")

            final_result = dict()
            graph = dict()

            final_node_list = []
            final_edge_list = []
            for item in node_list:
                
                final_node_list.append(item)

            for item in edges_list:
                
                final_edge_list.append(item)



            graph['nodes'] = final_node_list
            graph['edges'] = final_edge_list
            graph['price_range'] = [min,int(max)]
            final_result['counter'] = 5
            final_result['graph'] = graph
            final_result['events'] = {}

            _ret = final_result

            if link.lower() == 'negative':
                print("negative = data.get('negative')")
                neg_nodes_list = []
                neg_nodes_list.append(x)
                with open("./data/outputhco.json", encoding='latin-1') as inputfile:
                    hco_news = json.load(inputfile)
                with open("./data/NewhcpNewsHeadlines.json", encoding='latin-1') as inputfile:
                    hcp_news = json.load(inputfile)
                for i in final_node_list:
                    #print("isNegative____________________________", i["title"])
                    isNegative = self.get_negative_news(i["title"], hco_news, hcp_news, i["color"])
                    #print("isNegative____________________________", isNegative)
                    if isNegative:
                        neg_nodes_list.append(i)
                graph['nodes'] = neg_nodes_list

            return True, "data_by_country", _ret 
        except Exception as e:
            print("Deepdive.data_by_country(): " + str(e))
            traceback.print_exc()
            return False, "Something went wrong"

    def data_by_node(self, data):  # tbd
        try:
            # # YOUR CODE HERE
            # # REMOVE THIS ONCE IMPLEMENTED
            # _ret = self.read_json("subGraph.json")
            # return True, "data_by_node", _ret
            iden = data['id']
            extra_edges_final = pd.DataFrame(columns=['hcp_id','hco_id'])
            if iden == 'null':
                
                True, "null_data", [] 
            if 'B' in iden or 'S' in iden or 'U' in iden:
                query = f"select 10001 as 'gsk', trim(hco_id) as 'hco', cast(hcp_id as varchar) as 'hcp', count(*) as count from app.FactHcpHco where hco_id = '{iden}' group by trim(hco_id), cast(hcp_id as varchar)"
            else: 
                query = f"select 10001 as 'gsk', trim(hco_id) as 'hco', cast(hcp_id as varchar) as 'hcp', count(*) as count from app.FactHcpHco where hcp_id = '{iden}'  group by trim(hco_id), cast(hcp_id as varchar)"

            edges = db.select_df(query)
            print(edges.shape[0])
            edges_list = []
            if 'B' in iden or 'S' in iden or 'U' in iden:
                char_first = iden[0]
                hcps = edges[['hcp']]

                query = f"select cast(hcp_id as varchar) as 'hcp_id', trim(hco_id) as 'hco_id', count(*) as count from app.FactHcpHco where hco_id <> '{iden}' and hco_id like'{char_first}%' group by cast(hcp_id as varchar), trim(hco_id)"
                extra_edges = db.select_df(query)
                if not extra_edges.empty:
                    print("inif")
                    extra_edges_final = hcps.merge(extra_edges, how = 'inner', left_on = ['hcp'], right_on = ['hcp_id'])
                    extra_edges_final = extra_edges_final[['hco_id', 'hcp_id']].drop_duplicates()
                    extra_edges_final = extra_edges_final.dropna(subset = ['hcp_id'])
                    print(extra_edges_final.shape[0])
                    
                    for i,row in extra_edges_final.iterrows():
                        edges_dict = dict()
                        print(row['hcp_id'])
                        if row['hcp_id']:
                            edges_dict['from'] = row['hcp_id']
                            edges_dict['to'] = row['hco_id']
                            edges_list.append(edges_dict)
                

            for i,row in edges.iterrows():
                edges_dict = dict()
                edges_dict['from'] = row['gsk']
                edges_dict['to'] = row['hco']
                edges_list.append(edges_dict)

            for i,row in edges.iterrows():
                edges_dict = dict()
                edges_dict['from'] = row['hco']
                edges_dict['to'] = row['hcp']
                edges_list.append(edges_dict)

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
                        "label": "Company",
                        "title": "Company",
                        "color": "#fdfd00",
                        "size": 45,
                        "shape": "image",
                        "image": "https://dieselpunkcore.com/wp-content/uploads/2014/06/logo-placeholder.png",
                    }
            node_list.append(x)

            if not extra_edges_final.empty:
                hcp1 = extra_edges_final[['hcp_id']].rename(columns={'hcp_id' : 'hcp'})
                hcp2 = edges[['hcp']]
                hcps = pd.concat([hcp1,hcp2], ignore_index = True)
            else:
                hcps = edges[['hcp']]

            hcps = hcps.drop_duplicates()

            if not extra_edges_final.empty:
                hco1 = extra_edges_final[['hco_id']].rename(columns={'hco_id' : 'hco'})
                hco2 = edges[['hco']]
                hcos = pd.concat([hco1,hco2], ignore_index = True)
            else:
                hcos = edges[['hco']]

            hcos = hcos.drop_duplicates()



            query = f"SELECT cast(a.Id as varchar) as 'id', a.hcp_name, a.country, max(b.designation) as 'designation' FROM dbo.hcp_info a \
            join app.FactHcpHco b on a.Id = b.hcp_id group by cast(a.Id as varchar), a.hcp_name, a.country "
            # Execute the query
            df = db.select_df(query)
            nodes_df = df[['id','hcp_name','designation','country']]

            nodes_merged = hcps.merge(nodes_df, how = 'inner', left_on = ["hcp"], right_on = ["id"] )
            print(nodes_merged)
            nodes_merged = nodes_merged.drop_duplicates(subset=['id'])

            query = f"select a.COUNTRY, a.HCO, a.ID, max(b.hco_id) from app.hco a join app.FactHcpHco b on a.ID = b.hco_id group by a.COUNTRY, a.HCO, a.ID"

            # Execute the query
            hco_df = db.select_df(query)

            nodes_hco_df = hco_df.rename(columns={'HCO':'label', 'ID':'id', 'COUNTRY':'country'})
            nodes_hco_merged = hcos.merge(nodes_hco_df, how = 'inner', left_on = ["hco"], right_on = ["id"] )

            a = 0
            for i,row in nodes_hco_merged.iterrows():
                a+=1
                node_hco_dict = dict()
                node_hco_dict['page'] = 1
                
                node_hco_dict['shape'] = 'dot'
                node_hco_dict['color'] = "#fb7e81"
                node_hco_dict['id'] = row['id']
                node_hco_dict['label'] = row['label']
                node_hco_dict['title'] = row['label']
                node_hco_dict['designation'] = ""
                node_list.append(node_hco_dict)
            print(f"number of hco nodes is {a}")
            b = 0
            for i,row in nodes_merged.iterrows():
                b+=1
                node_dict = dict()
                node_dict['shape'] = 'dot'
                node_dict['color'] = "#95c0f9"
                node_dict['id'] = row['id']
                node_dict['label'] = row['hcp_name']
                node_dict['title'] = row['hcp_name']
                node_dict['designation'] = row['designation']
                node_dict['page'] = 1
                
                node_list.append(node_dict)
            print(f"number of hcp nodes is {b}")

            final_result = dict()
            graph = dict()


            graph['nodes'] = node_list
            graph['edges'] = edges_list
            graph['pagination'] = {'first_page' : 1, 'last_page' : 1}
            final_result['counter'] = 5
            final_result['graph'] = graph
            final_result['events'] = {}

            _ret = final_result



            return True, "data_by_node", _ret 
        except Exception as e:
            print("Deepdive.data_by_node(): " + str(e))
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
                query = f"select HCO from app.hco where ID = '{iden}'"
                db = MSSQLConnection()
                entity = db.select_df(query)
                for i,row in entity.iterrows():
                    entity_name = row['HCO']
                    break
                with open("./data/outputhco.json", encoding='latin-1') as inputfile:
                    hco_news = json.load(inputfile)
                
                for article in hco_news:
                    if article['hco'] == entity_name:
                        event_dict = dict()
                        event_dict["id"] = data['id']
                        event_dict["tag"] = article['hco'] + ' : ' + ' External News Event'
                        event_dict["category"] = 'External News Event'
                        event_dict['date'] = datetime.datetime.fromtimestamp(datetime.datetime.strptime(article['date'], "%Y-%m-%d").timestamp())
                        event_dict['description'] = article['link']
                        timeline_list.append(event_dict)
            else:
                db = MSSQLConnection()
                query = f"select hcp_name from dbo.hcp_info where Id = '{iden}'"
                entity = db.select_df(query)
                for i,row in entity.iterrows():
                    entity_name = row['hcp_name']
                    break
                with open("./data/NewhcpNewsHeadlines.json", encoding='latin-1') as inputfile:
                    hco_news = json.load(inputfile)
                
                for article in hco_news:
                    if article['hcp'] == entity_name:
                        event_dict = dict()
                        event_dict["id"] = data['id']
                        event_dict["tag"] = article['hco'] + ' : '+ article['hcp']+ ' : ' + ' External News Event'
                        event_dict["category"] = 'External News Event'
                        event_dict['date'] = datetime.datetime.fromtimestamp(datetime.datetime.strptime(article['date'], "%Y-%m-%d").timestamp())
                        event_dict['description'] = article['link']
                        timeline_list.append(event_dict)
            import time
            time.sleep(5)
            #interactions:
            db = MSSQLConnection()
            query = f"SELECT [RecordType],[EventType],[CallType],[Product],[CallStart],[HcpName] FROM [dbo].[interactions_raw] where [HcpName] = '{entity_name}' order by [CallStart]"
            interactions = db.select_df(query)
            if not interactions.empty:
                for i,row in interactions.iterrows():
                    event_dict = dict()
                    event_dict["id"] = data['id']
                    event_dict["tag"] = 'Meeting : Interaction with ' + row["HcpName"]
                    event_dict["category"] = row['CallType']
                    event_dict['date'] = row['CallStart']
                    event_dict['description'] = row['RecordType'] + ' | ' + row['EventType'] + ' | ' + row['Product']
                    timeline_list.append(event_dict)

            #payments
            if 'B' in data['id'] or 'S' in data['id'] or 'U' in data['id']:
                query = f"select hco_id, payment_hcp_id from app.FactHcpHco where hco_id = '{iden}' and payment_hcp_id is not null"
                entity = db.select_df(query)
                if not entity.empty:
                    for i,row in entity.iterrows():
                        payment_id = row['payment_hcp_id']
                        break
            else:    
                query = f"select hco_id, payment_hcp_id from app.FactHcpHco where hcp_id = '{iden}' and payment_hcp_id is not null"
                entity = db.select_df(query)
                if not entity.empty:
                    for i,row in entity.iterrows():
                        payment_id = row['payment_hcp_id']
                        break
            
            query = f"SELECT [ThirdPartyPaymentsLineId],[InvoiceClearingDate],[InvoiceClearingType],[InvoiceLineAmountLocal],[AllText],[Currency],\
                        [VendorNumber],[VendorName],[VendorType],[Monetary/Non-Monetary] FROM [mj].[all_tov] where [VendorNumber] = '{payment_id}' order by [InvoiceClearingDate]"
            payments = db.select_df(query)
            if not payments.empty:
                for i,row in payments.iterrows():
                    event_dict = dict()
                    event_dict["id"] = data['id']
                    event_dict["tag"] = 'Payments for ' + row["VendorName"]
                    event_dict["category"] = 'Payment'
                    event_dict['date'] = row['InvoiceClearingDate']
                    event_dict['description'] = str(row['InvoiceLineAmountLocal']) + ' | ' + str(row['Currency']) + ' | ' + row['AllText']
                    timeline_list.append(event_dict)

            query = f"SELECT [ThirdPartyPaymentsLineId],[InvoiceClearingDate],[InvoiceClearingType],[InvoiceLineAmountLocal],[AllText],[Currency],\
                        [VendorNumber],[VendorName],[VendorType],[Monetary/Non-Monetary] FROM [mj].[tov_exc_payments] where [VendorNumber] = '{payment_id}' order by [InvoiceClearingDate]"
            payments = db.select_df(query)
            if not payments.empty:
                for i,row in payments.iterrows():
                    event_dict = dict()
                    event_dict["id"] = data['id']
                    event_dict["tag"] = 'Payments for ' + row["VendorName"]
                    event_dict["category"] = 'Payment'
                    event_dict['date'] = row['InvoiceClearingDate']
                    event_dict['description'] = str(row['InvoiceLineAmountLocal']) + ' | ' + row['Currency'] + ' | ' + row['AllText']
                    timeline_list.append(event_dict)
                    
            newlist = sorted(timeline_list, key=lambda d: d['date'])
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
                query = f"select HCO from app.hco where ID = '{iden}'"
                db = MSSQLConnection()
                entity = db.select_df(query)
                for i,row in entity.iterrows():
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
                query = f"select hcp_name from dbo.hcp_info where Id = '{iden}'"
                db = MSSQLConnection()
                entity = db.select_df(query)
                for i,row in entity.iterrows():
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
            if 'B' in data['id'] or 'S' in data['id'] or 'U' in data['id']:
                query = f"select hco_id, payment_hcp_id from app.FactHcpHco where hco_id = '{iden}' and payment_hcp_id is not null"
                db = MSSQLConnection()
                entity = db.select_df(query)
                if not entity.empty:
                    for i,row in entity.iterrows():
                        payment_id = row['payment_hcp_id']
                        break
            else:    
                query = f"select hco_id, payment_hcp_id from app.FactHcpHco where hcp_id = '{iden}' and payment_hcp_id is not null"
                db = MSSQLConnection()
                entity = db.select_df(query)
                if not entity.empty:
                    for i,row in entity.iterrows():
                        payment_id = row['payment_hcp_id']
                        break
            payment_amount = 0
            payment_amount2 = 0
            query = f"SELECT SUM(cast([InvoiceLineAmountLocal] as float)) as 'payment', [VendorNumber] FROM [mj].[all_tov] where [VendorNumber] = '{payment_id}' group by [VendorNumber]"
            db = MSSQLConnection()
            payments = db.select_df(query)
            if not payments.empty:
                for i,row in payments.iterrows():
                    payment_amount = row['payment']
            
            query = f"SELECT SUM(cast([InvoiceLineAmountLocal] as float)) as 'payment', [VendorNumber] FROM [mj].[tov_exc_payments] where [VendorNumber] = '{payment_id}' group by [VendorNumber]"
            db = MSSQLConnection()
            payments = db.select_df(query)
            if not payments.empty:
                for i,row in payments.iterrows():
                    payment_amount2 = row['payment']
            
            
            return_dict['totalPaymentMade'] = str(payment_amount + payment_amount2)
            if 'B' in data['id'] or 'S' in data['id'] or 'U' in data['id']:
                db = MSSQLConnection()
                query = f"select HCO from app.hco where ID = '{iden}'"
                entity = db.select_df(query)
                for i,row in entity.iterrows():
                    entity_name = row['HCO']
                    break
            else: 
                query = f"select hcp_name from dbo.hcp_info where Id = '{iden}'"
                db = MSSQLConnection()
                entity = db.select_df(query)
                for i,row in entity.iterrows():
                    entity_name = row['hcp_name']
                    break
            
            query = f"SELECT count(*) as 'total_interactions' FROM [dbo].[interactions_raw] where [HcpName] = '{entity_name}'"
            db = MSSQLConnection()
            interactions = db.select_df(query)
            if not interactions.empty:
                for i,row in interactions.iterrows():
                    total_interactions = row['total_interactions']   
            
            return_dict['totalImteraction'] = str(total_interactions)
            return_dict['selectedName'] = entity_name
            print(return_dict, '00000000000000000000000000000000000000000000000000000000000000')
            if 'B' in data['id'] or 'S' in data['id'] or 'U' in data['id']:
                query = f"select HCO from app.hco where ID = '{iden}'"
                db = MSSQLConnection()
                entity = db.select_df(query)
                for i,row in entity.iterrows():
                    entity_name = row['HCO']
                    break
                with open("./data/outputhco.json", encoding='latin-1') as inputfile:
                    hco_news = json.load(inputfile)
                i=0
                for article in hco_news:
                    if article['hco'] == entity_name:
                        i+=1
                print(i, "total media articles")
            else:
                query = f"select hcp_name from dbo.hcp_info where Id = '{iden}'"
                db = MSSQLConnection()
                entity = db.select_df(query)
                for i,row in entity.iterrows():
                    entity_name = row['hcp_name']
                    break
                with open("./data/NewhcpNewsHeadlines.json", encoding='latin-1') as inputfile:
                    hco_news = json.load(inputfile)
                i=0
                for article in hco_news:
                    if article['hcp'] == entity_name:
                        i+=1
            return_dict['mediaArticles'] = str(i)
            return_dict['riskIdentified'] = str(5)
            _ret = [return_dict]

            print(_ret)
            # _ret = self.read_json("overview.json")
            return True, "overview", _ret
        except Exception as e:
            print("Deepdive.overview(): " + str(e))
            traceback.print_exc()
            return False, "Something went wrong"
