import socket
import ipaddress


def validate_ip(ip_string):
    try:
        ipaddress.ip_address(ip_string)
        return True
    except ValueError:
        return False


def is_valid_query(query):
    valid_queries = [
        "1",
        "2",
        "3"
    ]
    return query in valid_queries, valid_queries


def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    while True:
        # Maybe the IP and port will be hardcoded in the future
        server_ip = input("Enter the server IP address: ")
        if not validate_ip(server_ip):
            print("Invalid IP address format. Please try again.")
            continue

        try:
            server_port = int(input("Enter the server port number: "))
            if server_port < 0 or server_port > 65535:
                raise ValueError
        except ValueError:
            print("Invalid port number. Please enter a value between 0 and 65535.")
            continue

        try:
            client_socket.connect((server_ip, server_port))
            print(f"Connected to server at {server_ip}:{server_port}\n")
        except socket.error as e:
            print(f"Failed to connect: {e}")
            client_socket.close()
            return

        # Infinite loop to send multiple messages to the server
        while True:
            print("Enter one of the following valid queries:")
            print("Type 1 for: What is the average moisture inside my kitchen fridge in the past three hours?")
            print("Type 2 for: What is the average water consumption per cycle in my smart dishwasher?")
            print("Type 3 for: Which device consumed more electricity among my three IoT devices (two refrigerators and a dishwasher)?")
            print("Type 'exit' to quit.")

            query = input("Your query: ")

            if query.lower() == 'exit':
                print("Exiting client.")
                client_socket.close()
                return

            is_valid, valid_queries = is_valid_query(query)
            if not is_valid:
                print("\nSorry, this query cannot be processed. Please try one of the following:")
                for q in valid_queries:
                    print(f"- {q}")
                continue

            try:
                # Send valid query to the server
                client_socket.send(query.encode())

                # Receive the server's response
                response = client_socket.recv(1024).decode()
                print(f"Server reply: {response}")
            except socket.error as e:
                print(f"Socket error: {e}")
                break


if __name__ == "__main__":
    main()
