#!/usr/bin/env python3
import argparse
import struct
import sys
from bluetooth import BluetoothSocket, RFCOMM

def send_file(server_address, port, filename):
    sock = BluetoothSocket(RFCOMM)
    print(f"サーバ {server_address} のポート {port} に接続中…")
    sock.connect((server_address, port))
    print("接続しました")

    try:
        with open(filename, "rb") as f:
            file_data = f.read()
    except Exception as e:
        print("ファイル読み込みエラー:", e)
        sock.close()
        sys.exit(1)

    file_size = len(file_data)
    # ファイル名はパスではなく basename のみを送る（受信側の保存先は output_dir で指定）
    filename_bytes =  (filename.split("/")[-1]).encode("utf-8")

    try:
        # 1. ファイル名の長さ（4 バイト）を送信
        sock.send(struct.pack(">I", len(filename_bytes)))
        # 2. ファイル名を送信
        sock.send(filename_bytes)
        # 3. ファイルサイズ（8 バイト）を送信
        sock.send(struct.pack(">Q", file_size))
        # 4. ファイルデータを送信
        sock.send(file_data)
        print("ファイル送信完了")
    except Exception as e:
        print("送信エラー:", e)
    finally:
        sock.close()

def main():
    parser = argparse.ArgumentParser(description="Bluetooth File Transfer Client (No advertise_service)")
    parser.add_argument("--server", required=True,
                        help="受信側デバイスの Bluetooth アドレス（例: B8:27:EB:1F:CC:9F）")
    parser.add_argument("--port", type=int, default=3,
                        help="接続する RFCOMM ポート（デフォルト: 3）")
    parser.add_argument("--file", required=True,
                        help="送信するファイルのパス")
    args = parser.parse_args()
    send_file(server_address=args.server, port=args.port, filename=args.file)

if __name__ == '__main__':
    main()
