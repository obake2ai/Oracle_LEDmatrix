#!/bin/bash
set -e  # エラー発生時にスクリプトを終了

# コマンドライン引数でSSIDとパスワードを受け取る
if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <wifi_ssid> <wifi_password>"
  exit 1
fi

WIFI_SSID="$1"
WIFI_PASS="$2"

############################
# 1. VNC の有効化
############################
echo "=== VNC を有効化します ==="
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
# 4. Wi‑Fi 接続設定 (2.4GHz, 隠しSSID)
############################
echo "=== Wi-Fi 設定 ==="
# 指定のSSIDが既に存在するか確認し、存在しなければ設定を追記
if grep -q "ssid=\"$WIFI_SSID\"" /etc/wpa_supplicant/wpa_supplicant.conf; then
    echo "既に $WIFI_SSID の設定が存在するため、追加はスキップします。"
else
    echo "新たなWi‑Fi設定を /etc/wpa_supplicant/wpa_supplicant.conf に追記します。"
    sudo tee -a /etc/wpa_supplicant/wpa_supplicant.conf > /dev/null <<EOF

network={
    ssid="$WIFI_SSID"
    psk="$WIFI_PASS"
    scan_ssid=1
}
EOF
fi

echo "Wi-Fi設定を更新しました。wpa_supplicant を再起動して接続を試みます。"
sudo systemctl restart wpa_supplicant
sleep 5

# 接続状態の確認
if iw dev wlan0 link | grep -q "Not connected"; then
  echo "Wi-Fi接続に失敗しました。SSIDやパスワード、設定内容を確認してください。"
else
  echo "Wi-Fi接続に成功しました。"
fi

############################
# 5. rpi-rgb-led-matrix リポジトリのクローンとビルド
############################
echo "=== rpi-rgb-led-matrix のクローンとビルド ==="
cd ~
if [ ! -d "rpi-rgb-led-matrix" ]; then
  git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
else
  echo "rpi-rgb-led-matrix ディレクトリが既に存在するため、クローン処理をスキップします。"
fi
cd rpi-rgb-led-matrix
make
sudo make install-python

############################
# 6. Oracle_LEDmatrix リポジトリのクローンとセットアップ
############################
echo "=== Oracle_LEDmatrix のクローンとセットアップ ==="
cd ~
if [ ! -d "Oracle_LEDmatrix" ]; then
  git clone https://github.com/obake2ai/Oracle_LEDmatrix.git
else
  echo "Oracle_LEDmatrix ディレクトリが既に存在するため、クローン処理をスキップします。"
fi
cd Oracle_LEDmatrix
pip install click

############################
# 7. Python の cap_sys_nice 権限設定
############################
echo "=== Python の権限設定 (cap_sys_nice) ==="
sudo setcap 'cap_sys_nice=eip' /usr/bin/python3.11

echo "=== セットアップ完了 ==="
