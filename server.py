import socket
import pytz
from pymongo import MongoClient
from datetime import datetime, timedelta


def get_database():
    url = "mongodb+srv://user1:user1Password@cluster0.0f9ks.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(url)
    return client


def process_query(query, db):
    # MongoDB collection
    collection = db.IoT_virtual
    meta = db.IoT_metadata

    try:
        pst = pytz.timezone("US/Pacific")
        if query == "1":  # Average moisture in the past three hours
            utc_now = datetime.now(pytz.utc)
            three_hours_ago_utc = utc_now - timedelta(hours=3)
            three_hours_ago_pst = three_hours_ago_utc.astimezone(pst)

            results = collection.find({
                "payload.Moisture Meter - Moisture2": {"$exists": True},
                "time": {"$gte": three_hours_ago_utc}
            })

            metaRes = meta.find({"customAttributes.name": "Fridge1"})
            desiredMin, desiredMax = 0, 0
            for doc in metaRes:
                desiredMin += float(doc['customAttributes']['children'][0]['customAttributes']['children'][2]['customAttributes']['desiredMinValue'])
                desiredMax += float(doc['customAttributes']['children'][0]['customAttributes']['children'][2]['customAttributes']['desiredMaxValue'])

            total_moisture, count = 0, 0
            for doc in results:
                total_moisture += float(doc['payload']['Moisture Meter - Moisture2'])
                count += 1

            if count == 0:
                return "No moisture data found in the past three hours."
            average_moisture = total_moisture / count
            if desiredMin <= average_moisture <= desiredMax:
                return (
                    f"Average moisture in the fridge (last 3 hours, PST): {average_moisture:.2f} RH%.\n"
                    f"Queried from: {three_hours_ago_pst.strftime('%Y-%m-%d %H:%M:%S')} PST to now."
                )
            else:
                return (
                    f"Average moisture in the fridge (last 3 hours, PST): {average_moisture:.2f} RH%.\n"
                    f"Queried from: {three_hours_ago_pst.strftime('%Y-%m-%d %H:%M:%S')} PST to now.\n"
                    f"\nAVERAGE MOISTURE IS NOT WITHIN DESIRED RANGE, PLEASE CHECK ON THIS DEVICE.\n"
                )

        elif query == "2":  # Average water consumption per cycle in the dishwasher
            results = collection.find({"payload.WaterFlowDish": {"$exists": True}})
            metaRes = meta.find({"customAttributes.name": "washer"})

            desiredMin, desiredMax = 0, 0
            for doc in metaRes:
                desiredMin += float(doc['customAttributes']['children'][0]['customAttributes']['children'][2]['customAttributes']['desiredMinValue'])
                desiredMax += float(doc['customAttributes']['children'][0]['customAttributes']['children'][2]['customAttributes']['desiredMaxValue'])

            total_water_liters, count = 0, 0
            for doc in results:
                total_water_liters += float(doc['payload']['WaterFlowDish'])
                count += 1

            if count == 0:
                return "No water consumption data available."
            average_water_gallons = total_water_liters * 0.264172 / count
            if desiredMin <= average_water_gallons <= desiredMax:
                return f"Average water consumption per cycle: {average_water_gallons:.2f} gallons/min."
            else:
                return (f"Average water consumption per cycle: {average_water_gallons:.2f} gallons/min.\n"
                        f"\nAVERAGE WATER FLOW IS NOT WITHIN DESIRED RANGE, PLEASE CHECK ON THIS DEVICE.\n")


        elif query == "3":  # Device consuming more electricity
            results = collection.find({
                "$or": [
                    {"payload.Ammeter1": {"$exists": True}},
                    {"payload.Ammeter2": {"$exists": True}},
                    {"payload.AmmeterDish": {"$exists": True}}
                ]
            })

            consumption = {"Fridge 1": 0, "Fridge 2": 0, "Dishwasher": 0}
            for doc in results:
                if "Ammeter1" in doc['payload']:
                    consumption["Fridge 1"] += float(doc['payload']['Ammeter1']) * 0.001  # Wh to kWh
                if "Ammeter2" in doc['payload']:
                    consumption["Fridge 2"] += float(doc['payload']['Ammeter2']) * 0.001  # Wh to kWh
                if "AmmeterDish" in doc['payload']:
                    consumption["Dishwasher"] += float(doc['payload']['AmmeterDish']) * 0.001  # Wh to kWh

            max_device = max(consumption, key=consumption.get)
            return (
                f"The device consuming the most electricity is {max_device} with {consumption[max_device]:.2f} kWh."
            )

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
