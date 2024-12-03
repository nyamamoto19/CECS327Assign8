import socket
import pytz
from pymongo import MongoClient
from datetime import datetime, timedelta

#creates a connection between the server and the mongoDB
def get_database():
    url = "mongodb+srv://user1:user1Password@cluster0.0f9ks.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(url)
    return client


def process_query(query, db):
    # MongoDB collection
    collection = db.IoT_virtual #holds the virtual data that the sensors create
    meta = db.IoT_metadata #holds the metadata for all of the devices

    try:
        pst = pytz.timezone("US/Pacific")
        if query == "1":  # Average moisture in the past three hours
            #sets the time and time range of 3 hours
            utc_now = datetime.now(pytz.utc)
            three_hours_ago_utc = utc_now - timedelta(hours=3)
            three_hours_ago_pst = three_hours_ago_utc.astimezone(pst)

            results = collection.find({ #finds all data with moisture in the payload, within the time frame
                "payload.Moisture Meter - Moisture2": {"$exists": True},
                "time": {"$gte": three_hours_ago_utc}
            })

            metaRes = meta.find({"customAttributes.name": "Fridge1"}) #gets the metadata for fridge
            desiredMin, desiredMax = 0, 0 #out desired data range min and max
            #sets the desired min and max to the desiredMinValue and desiredMaxValue from the database
            for doc in metaRes:
                desiredMin += float(doc['customAttributes']['children'][0]['customAttributes']['children'][2]['customAttributes']['desiredMinValue'])
                desiredMax += float(doc['customAttributes']['children'][0]['customAttributes']['children'][2]['customAttributes']['desiredMaxValue'])

            total_moisture, count = 0, 0
            #gets all the moisture meter data, and sets a counter for finding the average value
            for doc in results:
                total_moisture += float(doc['payload']['Moisture Meter - Moisture2'])
                count += 1

            if count == 0:
                return "No moisture data found in the past three hours."
            average_moisture = total_moisture / count #average of the data
            if desiredMin <= average_moisture <= desiredMax: 
                return (
                    f"Average moisture in the fridge (last 3 hours, PST): {average_moisture:.2f} RH%.\n"
                    f"Queried from: {three_hours_ago_pst.strftime('%Y-%m-%d %H:%M:%S')} PST to now.\n"
                )
            else: #when data returned is out of range of the desired values
                return (
                    f"Average moisture in the fridge (last 3 hours, PST): {average_moisture:.2f} RH%.\n"
                    f"Queried from: {three_hours_ago_pst.strftime('%Y-%m-%d %H:%M:%S')} PST to now.\n"
                    f"\nAVERAGE MOISTURE IS NOT WITHIN DESIRED RANGE, PLEASE CHECK ON THIS DEVICE.\n"
                )

        elif query == "2":  # Average water consumption per cycle in the dishwasher
            results = collection.find({"payload.WaterFlowDish": {"$exists": True}}) #gets data for waterflow meter
            metaRes = meta.find({"customAttributes.name": "washer"}) #gets metadata for the washer

            desiredMin, desiredMax = 0, 0
            #sets the desired min and max
            for doc in metaRes:
                desiredMin += float(doc['customAttributes']['children'][0]['customAttributes']['children'][1]['customAttributes']['desiredMinValue'])
                desiredMax += float(doc['customAttributes']['children'][0]['customAttributes']['children'][1]['customAttributes']['desiredMaxValue'])
            total_water_liters, count = 0, 0
            for doc in results:
                total_water_liters += float(doc['payload']['WaterFlowDish'])
                count += 1

            if count == 0:
                return "No water consumption data available."
            #data in database is saved as L/Min and we convert liters to gallons
            average_water_gallons = total_water_liters * 0.264172 / count
            desiredMin *= 0.264172
            desiredMax *= 0.264172
            if desiredMin <= average_water_gallons <= desiredMax:
                return f"Average water consumption per cycle: {average_water_gallons:.2f} gallons/min.\n"
            else:
                return (f"Average water consumption per cycle: {average_water_gallons:.2f} gallons/min.\n"
                        f"\nAVERAGE WATER FLOW IS NOT WITHIN DESIRED RANGE, PLEASE CHECK ON THIS DEVICE.\n")


        elif query == "3":  # Device consuming more electricity
            #gets data for all the ammeter data from the three devices
            results = collection.find({
                "$or": [
                    {"payload.Ammeter1": {"$exists": True}},
                    {"payload.Ammeter2": {"$exists": True}},
                    {"payload.AmmeterDish": {"$exists": True}}
                ]
            })
            #gets ammeter metadata from one device, and can be used for all three devices since they all have the same parameters
            metaRes = meta.find({
                "$or": [
                    {"customAttributes.name": "washer"},
                    {"customAttributes.name": "Fridge1"},
                    {"customAttributes.name": "Fridge2"}
                ]
            })
            #sets max and min for ammeter
            ampmin, ampmax = 0, 0
            for doc in metaRes:
                if doc['customAttributes']['name'] == 'Fridge1':
                    ampmin += float(doc['customAttributes']['children'][0]['customAttributes']['children'][1]['customAttributes']['desiredMinValue'])
                    ampmax += float(doc['customAttributes']['children'][0]['customAttributes']['children'][1]['customAttributes']['desiredMaxValue'])
            #converts to watts and then kilowatts from an assumed 120 V circuit
            ampmax *= (0.001 * 120)
            ampmin *= (0.001 * 120)
            consumption = {"Fridge 1": 0, "Fridge 2": 0, "Dishwasher": 0}

            f1count,f2count,wcount = 0,0,0
            #ammeter measurement are in Amps
            #gets total amps measured among all the values in database
            for doc in results:
                if "Ammeter1" in doc['payload']:
                    consumption["Fridge 1"] += float(doc['payload']['Ammeter1'])
                    f1count += 1
                if "Ammeter2" in doc['payload']:
                    consumption["Fridge 2"] += float(doc['payload']['Ammeter2'])
                    f2count += 1
                if "AmmeterDish" in doc['payload']:
                    consumption["Dishwasher"] += float(doc['payload']['AmmeterDish'])
                    wcount += 1
            #takes average of the amps and converts it to watts,and then kilowatts
            for x in consumption:
                if x == "Fridge 1":
                    consumption[x] = (consumption[x]/f1count) * 0.001 * 120  # Wh to kWh and 120 V for average fridge
                if x == "Fridge 2":
                    consumption[x] = (consumption[x] / f2count) * 0.001 * 120  # Wh to kWh and 120 V for average fridge
                if x == "Dishwasher":
                    consumption[x] = (consumption[x] / wcount) * 0.001 * 120  # Wh to kWh and 120 V for average fridge
            #list for all devices out of range in electricity consumption
            outOfRange = []
            for x in consumption:
                if consumption[x] > ampmax or consumption[x] < ampmin:
                    outOfRange.append(x)
            #gets the device that uses the most electricity
            max_device = max(consumption, key=consumption.get)

            if len(outOfRange) > 0:
                return (f"The device consuming the most electricity is {max_device} with {consumption[max_device]:.2f} kWh.\n"
                        f"\nTHE FOLLOWING DEVICE(S) WERE OUT OF THE DESIRED RANGE. PLEASE CHECK THESE DEVICES\n{' '.join(str(i) for i in outOfRange)}\n")
            else:
                return f"The device consuming the most electricity is {max_device} with {consumption[max_device]:.2f} kWh.\n"

        else:
            return "Invalid query."

    except Exception as e:
        return f"An error occurred: {e}"

def main():
    # Create a TCP socket (SOCK_STREAM)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server_ip = input("Enter the IP address to bind the server to: ")
        server_port = int(input("Enter the port number for the server to listen on: "))

        # Bind the socket to the provided IP and port
        server_socket.bind((server_ip, server_port))
        server_socket.listen(1)

        mongoDB = get_database().test  # Connect to MongoDB
        print(f"Server is listening on {server_ip}:{server_port}")
        print("Type 'shutdown' from the client to stop the server.")

        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Connection established with {client_address}")

            while True:
                message = client_socket.recv(1024).decode()

                if message.lower() == 'shutdown':
                    print(f"Shutdown command received from {client_address}")
                    client_socket.send("shutdown".encode())
                    break

                print(f"Received query: {message}")
                response = process_query(message, mongoDB)
                client_socket.send(response.encode())
                print(f"Sent response: {response}")

            client_socket.close()
            break

    except Exception as e:
        print(f"Server error: {e}")
    finally:
        print("Server shutting down...")
        server_socket.close()


if __name__ == "__main__":
    main()
