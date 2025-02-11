#!/usr/bin/env python3
import argparse
import struct
import sys
from bluetooth import BluetoothSocket, RFCOMM, find_service

def send_file(server_address, filename, uuid="94f39d29-7d6d-437d-973b-fba39e49d4ee"):
    print("サービスを検索中…")
    service_matches = find_service(uuid=uuid, address=server_address)
    if len(service_matches) == 0:
        print("サービスが見つかりません")
        sys.exit(0)

    first_match = service_matches[0]
    port = first_match["port"]
    host = first_match["host"]
    print("ホスト:", host, "ポート:", port)

    sock = BluetoothSocket(RFCOMM)
    sock.connect((host, port))
    print("接続しました")

    try:
        with open(filename, "rb") as f:
            file_data = f.read()
    except Exception as e:
        print("ファイル読み込みエラー:", e)
        sock.close()
        sys.exit(0)

    file_size = len(file_data)
    filename_bytes = filename.encode("utf-8")

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
    parser = argparse.ArgumentParser(description="Bluetooth File Transfer Client")
    parser.add_argument("--server", required=True,
                        help="受信側デバイスのBluetoothアドレス（例: B8:27:EB:1F:CC:9F）")
    parser.add_argument("--file", required=True,
                        help="送信するファイルのパス")
    parser.add_argument("--uuid", default="94f39d29-7d6d-437d-973b-fba39e49d4ee",
                        help="サービスのUUID")
    args = parser.parse_args()

    send_file(server_address=args.server, filename=args.file, uuid=args.uuid)

if __name__ == '__main__':
    main()
