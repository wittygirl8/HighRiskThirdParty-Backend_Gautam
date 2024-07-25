import traceback
import pandas as pd

from utils.db import MSSQLConnection

db = MSSQLConnection()


class Scorecard:

    def test(self, data):  # tbd
        try:
            # YOUR CODE HERE
            return True, 'test', {}
        except Exception as e:
            print("Scorecard.test(): " + str(e))
            traceback.print_exc()
            return False, "Something went wrong" 

    def dashboard_stats(self, data):
        """
            Dashboard stats are of the format 
            statsData = [
                    {
                        'title': "Fayth",
                        'count': 3,
                    }
                ]
        """
        try:
            print(data)
            country = data.get('country')
            org = data.get('orgType')
    
            if country == 'null':
                return True, "dashboard_stats", []

            query = f'''select * from [app2].[vCountryHcoSummary] where country = '{country}' '''

            summary_df = db.select_df(query)

            metric_summary = list()
            for rowIndex, row in summary_df.iterrows():
                metric_summary.append(
                    {
                        'title': row['MetricName'],
                        'count': row['MetricValue']
                    }
                )

            return True, "dashboard_stats", metric_summary

        except Exception as e:
            print("Scorecard.dashboard_stats(): " + str(e))
            traceback.print_exc()
            return False, "Something went wrong"
        
    def dashboard_risk_table(self, data):
        """
        riskscoreData = [
            {
                'id': 'B078',
                'name': "Ava",
                'riskscore': 31,
            },
            ]
        """
        try:
            print(data)
            country = data.get('country')
            org = data.get('orgType')
    
            if country == 'null':
                return True, "dashboard_risk_table", []
            
            query = f''' select [OriginalEntityId], [Name], [RiskScore] from [app2].[vHcoRiskScore] where country = '{country}' '''

            risk_score_df = db.select_df(query)

            risk_score_data = list()
            for rowIndex, row in risk_score_df.iterrows():
                risk_score_data.append(
                    {
                        'id': row['OriginalEntityId'],
                        'name': row['Name'],
                        'riskscore': row['RiskScore']
                    }
                )

            risk_score_data.sort(reverse=True, key=lambda x: x['riskscore'])
            lengthLimit = min(5, len(risk_score_data))

            return True, 'dashboard_risk_table', risk_score_data[0:lengthLimit]

        except Exception as e:
            print("Scorecard.dashboard_risk_table(): " + str(e))
            traceback.print_exc()
            return False, "Something went wrong"

    def dashboard_business_activities(self, data):
        """
        Business Activites should return in the format
        businessActivitiesData = [
            {
                'id': HCO id,
                'name': <name of HCO>,
                <Business Activity>: <value in payment>
            }
            ]
        """

        try:
            print(data)
            country = data.get('country')
            org = data.get('orgType')
    
            if country == 'null':
                return True, "dashboard_business_activities", []

            currency_mapping = {'usa': 'USD', 'brazil': 'BRL', 'spain': 'EUR'}

            business_activities_query = f'''select distinct [BusinessActivity] from [app2].[vMultiActivityPayments]'''
            business_activities = db.select_df(business_activities_query)['BusinessActivity'].values

            result_cols = ', '.join([f"ISNULL([{col}], 0) AS [{col}]" for col in business_activities])
            pivot_cols = ', '.join([f"[{col}]" for col in business_activities])

            query = f'''select 
                        [ID],
                        [Name],
                        ''' + result_cols + f''' 
                        FROM (
                            select 
                            [ID], [Name], BusinessActivity, SUM([InvoiceLineAmountLocal]) as [Amount] from [app2].[vMultiActivityPayments] 
                            where country = '{country}' and LEFT([ID], 1) IN ('B', 'S', 'U') and currency = '{currency_mapping[country]}' 
                            group by [ID], [Name], BusinessActivity) A
                        PIVOT
                        (sum([Amount]) for BusinessActivity IN (
                            ''' + pivot_cols + f''')) B;
                    '''

            activity_payment_df = db.select_df(query)

            activity_payments = list()
            for rowIndex, row in activity_payment_df.iterrows():
                activity_payment = dict()
                activity_payment['id'] = row['ID']
                activity_payment['Name'] = row['Name']
                activity_payment['sortTotal'] = 0

                for col in business_activities:
                    if col in activity_payment_df:
                        activity_payment[col] = '{:,.2f}'.format(row[col]) + ' ' + str(currency_mapping[country])
                        activity_payment['sortTotal'] += row[col]
                        continue
                    
                    activity_payment[col] = 0

                activity_payment['total'] = '{:,.2f}'.format(activity_payment['sortTotal']) + ' ' + str(currency_mapping[country])
                activity_payments.append(
                    activity_payment
                )

            activity_payments.sort(reverse=True, key=lambda x: x['sortTotal'])
            lengthLimit = min(5, len(activity_payments))
            return True, 'dashboard_business_activities', activity_payments[0:lengthLimit]
        
        except Exception as e:
            print("Scorecard.dashboard_business_activities(): " + str(e))
            traceback.print_exc()
            return False, "Something went wrong"

    def dashboard_connections(self, data):
        """
            Connections should return the format:
            connectionsTableData = 
            mediaData = {
            'labels': ["June", "Marry", "Christen", "Barcelona"],
            'datasets': [
                {
                    'label': "Positive",
                    'data': [-100, 50, -75, 100, -50, 60],
                    'borderColor': "rgb(255, 99, 132)",
                    'backgroundColor': "rgba(255, 99, 132, 0.5)",
                },
                {
                    'label': "Negative",
                    'data': [-100, 50, -75, 100, -50, 60],
                    'borderColor': "rgb(53, 162, 235)",
                    'backgroundColor': "rgba(53, 162, 235, 0.5)",
                },],}
        """

        try:
            print(data)
            country = data['country']
            org = data.get('orgType')
            if country == 'null':
                return True, "dashboard_connections_table", []
            
            query = f'''select OriginalEntityId, Name, NetworkConnectedHCOs from [app2].[vHcoNetworkSummary] where Country = '{country}' '''
            connections_df = db.select_df(query)

            connectionsData = {
                'None': 0,
                'Low': 0,
                'Medium': 0,
                'High': 0
            }

            for rowIndex, row in connections_df.iterrows():
                if row['NetworkConnectedHCOs'] == 0:
                    connectionsData['None'] += 1
                elif row['NetworkConnectedHCOs'] >= 20:
                    connectionsData['High'] += 1
                elif row['NetworkConnectedHCOs'] >= 10:
                    connectionsData['Medium'] += 1
                else:
                    connectionsData['Low'] += 1

            labels = ['None', 'Low', 'Medium', 'High']
            connections_output = {
                'labels': labels,
                'datasets': [
                    {
                        'label': 'Connection Strength',
                        'data': [connectionsData[label] for label in labels],
                        'borderColor': "rgb(53, 162, 235)",
                        'backgroundColor': "rgba(53, 162, 235, 0.5)",
                     }
                ]
            }

            return True, 'dashboard_connections', connections_output            

        except Exception as e:
            print("Scorecard.dashboard_connections_table(): " + str(e))
            traceback.print_exc()
            return False, "Something went wrong"

    def dashboard_global_spend(self, data):
        """
        globalSpendData = [
            {
                'id': 1,
                'name': "Ava",
                'Brazil': 31,
                'Spain': 31,
                'USA': 31
            },
            ]
        """

        try:
            print(data)
            country = data.get('country')
            org = data.get('orgType')
    
            if country == 'null':
                return True, "dashboard_global_spend", []
            
            currency_mapping = {'usa': 'USD', 'brazil': 'BRL', 'spain': 'EUR'}

            query = f'''select 
                        [ID],
                        [Name],
                        ISNULL([BRAZIL], 0)     AS [BRAZIL],
                        ISNULL([SPAIN], 0)      AS [SPAIN],
                        ISNULL([USA], 0)        AS [USA]
                    from (
                    select [ID], [Name], InvoiceLineAmountLocal as [Amount], Country from [app2].[vMultiCountryPayments]) A
                    pivot
                    (sum([Amount]) for [country] IN ([BRAZIL], [SPAIN], [USA])) B; '''

            inter_country_payment_df = db.select_df(query)

            inter_country_payments = list()
            for rowIndex, row in inter_country_payment_df.iterrows():
                inter_country_payment = {
                    'id': row['ID'],
                    'Name': row['Name'],
                    'Brazil': '{:,.2f}'.format(row['BRAZIL']) + ' BRL', 
                    'Spain': '{:,.2f}'.format(row['SPAIN']) + ' EUR', 
                    'USA': '{:,.2f}'.format(row['USA']) + ' USD',
                }
                inter_country_payments.append(inter_country_payment)

            return True, 'dashboard_global_spend', inter_country_payments

        except Exception as e:
            print("Scorecard.dashboard_global_spend(): " + str(e))
            traceback.print_exc()
            return False, "Something went wrong"   

    def dashboard_media_coverage(self, data):
        """  
        Get media coverage data in the following format:

        mediaData = {
            'labels': ["June", "Marry", "Christen", "Barcelona"],
            'datasets': [
                {
                    'label': "Positive",
                    'data': [-100, 50, -75, 100, -50, 60],
                    'borderColor': "rgb(255, 99, 132)",
                    'backgroundColor': "rgba(255, 99, 132, 0.5)",
                },
                {
                    'label': "Negative",
                    'data': [-100, 50, -75, 100, -50, 60],
                    'borderColor': "rgb(53, 162, 235)",
                    'backgroundColor': "rgba(53, 162, 235, 0.5)",
                },],}
        """
        
        try:
            print(data)
            country = data.get('country')
            org = data.get('orgType')
    
            if country == 'null':
                return True, "dashboard_media_coverage", []

            if org == 'hco':
                query = f'''select DISTINCT MAX(B.[ID]) AS ID, A.[HCO/HCP], A.[Positive Count], A.[Negative Count] 
                          from (select * from [app2].[media_coverage] where Country = '{country}' and EntityType = 'HCO') A 
                          INNER JOIN [app2].[vHco] B ON A.[HCO/HCP] = B.[hco] AND A.[Country] = B.[Country]
                          WHERE B.[PaymentCount] > 0
                          group by A.[HCO/HCP], A.[Positive Count], A.[Negative Count]'''
            else:
                query = f'''select DISTINCT MAX(B.[ID]) AS ID, A.[HCO/HCP], A.[Positive Count], A.[Negative Count] 
                          from (select * from [app2].[media_coverage] where Country = '{country}' and EntityType = 'HCP') A 
                          INNER JOIN [app2].[vHcp] B ON A.[HCO/HCP] = B.[hcp_name] AND A.[Country] = B.[Country] 
                          group by A.[HCO/HCP], A.[Positive Count], A.[Negative Count]'''
            media_df = db.select_df(query)

            media_data_list = list()
            for rowIndex, row in media_df.iterrows():
                media_data_dict = {
                    'id': row['ID'],
                    'name': row['HCO/HCP'],
                    'positive_count': row['Positive Count'],
                    'negative_count': row['Negative Count']
                }
                media_data_list.append(media_data_dict)

            # sort by negative media first, positive media second in the case where there is no negative media
            media_data_list.sort(reverse=True, key=lambda x: (x['negative_count'], x['positive_count']))

            lengthLimit = min(5, len(media_data_list))

            media_data = {
                'ids': [media_data_dict['id'] for media_data_dict in media_data_list][0:lengthLimit],
                'labels': [media_data_dict['name'] for media_data_dict in media_data_list][0:lengthLimit],
                'datasets': []
            }

            positive_data = {
                'label': 'Positive', 'data': [media_data_dict['positive_count'] for media_data_dict in media_data_list][0:lengthLimit], 
                'borderColor': "rgb(53, 162, 235)",
                'backgroundColor': "rgba(53, 162, 235, 0.5)"
                }
            negative_data = {
                'label': 'Negative', 'data': [-1 * media_data_dict['negative_count'] for media_data_dict in media_data_list][0:lengthLimit], 
                'borderColor': "rgb(255, 99, 132)",
                'backgroundColor': "rgba(255, 99, 132, 0.5)",
                }

            media_data['datasets'] = [positive_data, negative_data]

            return True, 'dashboard_media_coverage', media_data
        
        except Exception as e:
            print("Scorecard.dashboard_media_coverage(): " + str(e))
            traceback.print_exc()
            return False, "Something went wrong"

    def dashboard_connections_table(self, data):
        """
            Connections should return the format:
            connectionsTableData = [
            {
                'id': '123',
                'name': 'Amy',
                'priority': 'Medium',
            }
            ]
        """

        try:
            print(data)
            country = data['country']
            org = data.get('orgType')
            if country == 'null':
                return True, "dashboard_connections_table", []
            
            query = f'''select OriginalEntityId, Name, NetworkConnectedHCOs from [app2].[vHcoNetworkSummary] where Country = '{country}' '''
            connections_df = db.select_df(query)

            connectionsTableData = list()

            for rowIndex, row in connections_df.iterrows():
                priority = ''
                if row['NetworkConnectedHCOs'] == 0:
                    priority = 'None'
                elif row['NetworkConnectedHCOs'] >= 20:
                    priority = 'High'
                elif row['NetworkConnectedHCOs'] >= 10:
                    priority = 'Medium'
                else:
                    priority = 'Low'

                connectionsTableData.append(
                        {
                            'id': row['OriginalEntityId'],
                            'name': row['Name'],
                            'connection_count': row['NetworkConnectedHCOs'],
                            'priority': priority
                        }
                    )

            connectionsTableData.sort(reverse=True, key=lambda x: (x['connection_count'], x['name']))

            filteredConnectionsTableData = list()
            highest_counter = 0
            category_iter = 'High'
            for data in connectionsTableData:
                if category_iter != data['priority']:
                    category_iter = data['priority']
                    highest_counter = 0
                if highest_counter < 5:
                    filteredConnectionsTableData.append(data)
                    highest_counter += 1

            return True, 'dashboard_connections_table', filteredConnectionsTableData

        except Exception as e:
            print("Scorecard.dashboard_connections_table(): " + str(e))
            traceback.print_exc()
            return False, "Something went wrong"
