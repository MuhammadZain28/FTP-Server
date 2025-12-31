import socket
import os

SERVER_IP = "127.0.0.1"
SERVER_PORT = 21
BUFFER_SIZE = 4096

def recv_response(sock):
    data = sock.recv(BUFFER_SIZE)
    return data.decode(errors="ignore")

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_IP, SERVER_PORT))

    print(recv_response(sock))  # Welcome message

    while True:
        cmd = input("ftp> ").strip()

        if not cmd:
            continue

        sock.send((cmd + "\r\n").encode())

        if cmd.upper().startswith("STOR"):
            filename = cmd.split(" ", 1)[1]
            if not os.path.isfile(filename):
                print("File not found")
                continue

            print(recv_response(sock))  # 150 response
            with open(filename, "rb") as f:
                while chunk := f.read(BUFFER_SIZE):
                    sock.send(chunk)
            sock.send(b"\r\n")  # end marker
            print(recv_response(sock))  # 226 response

        elif cmd.upper().startswith("RETR"):
            filename = cmd.split(" ", 1)[1]

            response = recv_response(sock)
            print(response)

            if not response.startswith("150"):
                continue

            # Extract file size
            size = int(response.split()[1])
            received = 0

            with open(filename, "wb") as f:
                while received < size:
                    data = sock.recv(min(BUFFER_SIZE, size - received))
                    if not data:
                        break
                    f.write(data)
                    received += len(data)
                    print(f"Downloaded {received}/{size} bytes", end="\r")

            # Final confirmation
            print(recv_response(sock))  # 226
            print("Download complete")

        else:
            response = recv_response(sock)
            print(response)

        if cmd.upper() == "QUIT":
            break

    sock.close()

if __name__ == "__main__":
    main()
