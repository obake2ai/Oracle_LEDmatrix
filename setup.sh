#!/bin/bash
set -e  # エラー発生時にスクリプトを終了

############################
# 1. VNCの有効化
############################
echo "=== VNC を有効化します ==="
# 非対話型で VNC を有効化 (0: enable)
sudo raspi-config nonint do_vnc 0

############################
# 2. システムの更新とアップグレード
############################
echo "=== システムの更新とアップグレード ==="
sudo apt update && sudo apt upgrade -y

############################
# 3. 必要なパッケージのインストール (cython3)
############################
echo "=== cython3 のインストール ==="
sudo apt install -y cython3

############################
# 4. Wi‑Fi 接続設定
############################
echo "=== Wi-Fi 設定 ==="
# Pi Zero 2 WHは2.4GHzのみ対応
# ※ 接続するWi‑FiのSSIDとパスワードを設定してください
WIFI_SSID="rootk-guest2.4"
WIFI_PASS="rootk8808"

# Wi‑Fiがステルス（隠し）SSIDの場合は scan_ssid=1 が必要
sudo tee -a /etc/wpa_supplicant/wpa_supplicant.conf > /dev/null <<EOF

network={
    ssid="$WIFI_SSID"
    psk="$WIFI_PASS"
    scan_ssid=1
}
EOF

echo "Wi-Fi設定を更新しました。ネットワークサービスを再起動します。"
# Wi-Fi再設定を試みる。失敗した場合は dhcpcd を再起動
sudo wpa_cli -i wlan0 reconfigure || sudo systemctl restart dhcpcd

############################
# 5. rpi-rgb-led-matrix リポジトリのクローンとビルド
############################
echo "=== rpi-rgb-led-matrix のクローンとビルド ==="
cd ~
git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
cd rpi-rgb-led-matrix
make
sudo make install-python

############################
# 6. Oracle_LEDmatrix リポジトリのクローンとセットアップ
############################
echo "=== Oracle_LEDmatrix のクローンとセットアップ ==="
cd ~
git clone https://github.com/obake2ai/Oracle_LEDmatrix.git
cd Oracle_LEDmatrix
pip install click

############################
# 7. Python の cap_sys_nice 権限設定
############################
echo "=== Python の権限設定 (cap_sys_nice) ==="
sudo setcap 'cap_sys_nice=eip' /usr/bin/python3.11

echo "=== セットアップ完了 ==="
