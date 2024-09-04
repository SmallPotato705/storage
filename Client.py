import socket

# 創建一個TCP/IP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 連接到服務器
client_socket.connect(('localhost', 65432))

# 發送數據
message = "$TMSCT"
client_socket.send(message.encode('utf-8'))

# 接收回應
response = client_socket.recv(1024).decode('utf-8')
print(f"從服務器接收到的回應: {response}")

# 關閉socket
client_socket.close()
