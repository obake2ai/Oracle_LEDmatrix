#!/usr/bin/env python3
import argparse
import os
import struct
from bluetooth import BluetoothSocket, RFCOMM, advertise_service, SERIAL_PORT_CLASS, SERIAL_PORT_PROFILE

def run_server(port=0, output_dir=".", uuid="94f39d29-7d6d-437d-973b-fba39e49d4ee"):
    # RFCOMM ソケットを作成して待ち受け
    server_sock = BluetoothSocket(RFCOMM)
    server_sock.bind(("", port))  # port が 0 の場合は自動で空いているポートが割り当てられます
    server_sock.listen(1)
    actual_port = server_sock.getsockname()[1]

    # サービスの広告（advertise）
    advertise_service(
        server_sock,
        "FileTransferServer",
        service_id=uuid,
        service_classes=[uuid, SERIAL_PORT_CLASS],
        profiles=[SERIAL_PORT_PROFILE]
    )
    print(f"RFCOMM チャネル {actual_port} で接続待ち…")

    client_sock, client_info = server_sock.accept()
    print("接続を受け付けました:", client_info)

    try:
        # 1. ファイル名の長さ（4 バイト）を受信
        data = client_sock.recv(4)
        if len(data) < 4:
            print("ファイル名の長さを受信できませんでした")
            return
        filename_len = struct.unpack('>I', data)[0]

        # 2. ファイル名を受信
        filename = client_sock.recv(filename_len).decode('utf-8')
        print("受信ファイル名:", filename)

        # 3. ファイルサイズ（8 バイト）を受信
        data = client_sock.recv(8)
        if len(data) < 8:
            print("ファイルサイズを受信できませんでした")
            return
        file_size = struct.unpack('>Q', data)[0]
        print("ファイルサイズ:", file_size, "バイト")

        # 4. ファイルデータを受信
        received = 0
        output_path = os.path.join(output_dir, filename)
        with open(output_path, 'wb') as f:
            while received < file_size:
                chunk = client_sock.recv(1024)
                if not chunk:
                    break
                f.write(chunk)
                received += len(chunk)
                print(f"受信済み: {received} / {file_size} バイト", end="\r")
        print(f"\nファイル受信完了: {output_path}")
    except Exception as e:
        print("エラー:", e)
    finally:
        client_sock.close()
        server_sock.close()

def main():
    parser = argparse.ArgumentParser(description="Bluetooth File Transfer Server")
    parser.add_argument("--port", type=int, default=0,
                        help="使用するRFCOMMポート（デフォルト: 0（自動割り当て））")
    parser.add_argument("--output-dir", default=".",
                        help="受信ファイルの保存ディレクトリ（デフォルト: カレントディレクトリ）")
    parser.add_argument("--uuid", default="94f39d29-7d6d-437d-973b-fba39e49d4ee",
                        help="サービスのUUID")
    args = parser.parse_args()

    run_server(port=args.port, output_dir=args.output_dir, uuid=args.uuid)

if __name__ == '__main__':
    main()
