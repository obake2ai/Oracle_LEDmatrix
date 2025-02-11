#!/usr/bin/env python3
import argparse
import os
import struct
from bluetooth import BluetoothSocket, RFCOMM

def run_server(port, output_dir="."):
    # RFCOMM ソケットを作成して指定ポートで待ち受け
    server_sock = BluetoothSocket(RFCOMM)
    server_sock.bind(("", port))
    server_sock.listen(1)
    actual_port = server_sock.getsockname()[1]
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
        filename = client_sock.recv(filename_len).decode("utf-8")
        print("受信ファイル名:", filename)

        # 3. ファイルサイズ（8 バイト）を受信
        data = client_sock.recv(8)
        if len(data) < 8:
            print("ファイルサイズを受信できませんでした")
            return
        file_size = struct.unpack('>Q', data)[0]
        print("ファイルサイズ:", file_size, "バイト")

        # 4. ファイルデータを受信して保存
        received = 0
        output_path = os.path.join(output_dir, os.path.basename(filename))
        with open(output_path, "wb") as f:
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
    parser = argparse.ArgumentParser(description="Bluetooth File Transfer Server (No advertise_service)")
    parser.add_argument("--port", type=int, default=3,
                        help="使用する RFCOMM ポート（デフォルト: 3）")
    parser.add_argument("--output-dir", default=".",
                        help="受信ファイルの保存ディレクトリ（デフォルト: カレントディレクトリ）")
    args = parser.parse_args()
    run_server(port=args.port, output_dir=args.output_dir)

if __name__ == '__main__':
    main()
