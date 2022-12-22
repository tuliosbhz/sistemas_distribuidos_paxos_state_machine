# # importing the requests library
# import requests
# import db_ocpp_methods as ocppdb

# def charge_point_post():
#     # defining the api-endpoint
#     API_ENDPOINT = "http://vcpes14.inesctec.pt/api/measurements"

#     # your API key here
#     API_KEY = "XXXXXXXXXXXXXXXXX"

#     energy, voltage, current, power = ocppdb.read_metervalues()

#     # data to be sent to api
#     data = {
#             "hlc_state": self.hlc_state,
#             "ChargingState": self.chargingState,
#             "Voltage": voltage,
#             "Current": current,
#             "Power": power,
#             "Energy": energy,
#             "SessionId": "0000000000000053"
#         }

#     # sending post request and saving response as response object
#     r = requests.post(url = API_ENDPOINT, data = data)

#     # extracting response text
#     pastebin_url = r.text
#     print("The pastebin URL is:%s"%pastebin_url)

# def charge_point_put():
#     # defining the api-endpoint
#     API_ENDPOINT = "http://vcpes14.inesctec.pt/api/measurements"

#     # your API key here
#     API_KEY = "XXXXXXXXXXXXXXXXX"

#     energy, voltage, current, power = ocppdb.read_metervalues()

#     # data to be sent to api
#     data = {
#             "hlc_state": self.hlc_state,
#             "ChargingState": self.chargingState,
#             "Voltage": voltage,
#             "Current": current,
#             "Power": power,
#             "Energy": energy,
#             "SessionId": "0000000000000053"
#         }

#     # sending post request and saving response as response object
#     r = requests.put(url = API_ENDPOINT, data = data)

#     # extracting response text
#     pastebin_url = r.text
#     print("The pastebin URL is:%s"%pastebin_url)
