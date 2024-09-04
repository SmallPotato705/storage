import socket

# 創建一個TCP/IP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 綁定socket到本地地址和端口
server_socket.bind(('localhost', 65432))

# 開始監聽傳入的連接，參數5表示允許等待的連接數量
server_socket.listen(5)
print("服務器已啟動，正在等待連接...")

while True:
    # 接受新連接
    client_socket, client_address = server_socket.accept()
    print(f"與 {client_address} 成功建立連接")
    
    # 接收數據
    data = client_socket.recv(1024).decode('utf-8')
    print(f"接收到的數據: {data}")

    # 發送回應
    response = "數據已接收"
    client_socket.send(response.encode('utf-8'))

    # 關閉客戶端socket
    client_socket.close()
