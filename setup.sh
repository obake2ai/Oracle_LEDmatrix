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
cd ~
sudo raspi-config nonint do_vnc 0

############################
# 2. システムの更新とアップグレード
############################
echo "=== システムの更新とアップグレード ==="
echo "aptのロック解除を待っています..."
while sudo fuser /var/lib/apt/lists/lock >/dev/null 2>&1; do
  sleep 5
done

echo "ロックが解除されました。システム更新を開始します。"
sudo apt update && sudo apt upgrade -y

############################
# 3. 必要なパッケージのインストール (cython3)
############################
echo "=== cython3 python3-click のインストール ==="
sudo apt install -y cython3
sudo apt install python3-click

############################
# 4. Wi‑Fi 接続設定 (2.4GHz, 隠しSSID)
############################
# echo "=== Wi-Fi 設定 ==="
# # 指定のSSIDが既に存在するか確認し、存在しなければ設定を追記
# if grep -q "ssid=\"$WIFI_SSID\"" /etc/wpa_supplicant/wpa_supplicant.conf; then
#     echo "既に $WIFI_SSID の設定が存在するため、追加はスキップします。"
# else
#     echo "新たなWi‑Fi設定を /etc/wpa_supplicant/wpa_supplicant.conf に追記します。"
#     sudo tee -a /etc/wpa_supplicant/wpa_supplicant.conf > /dev/null <<EOF
#
# network={
#     ssid="$WIFI_SSID"
#     psk="$WIFI_PASS"
#     scan_ssid=1
# }
# EOF
# fi
#
# echo "Wi-Fi設定を更新しました。wpa_supplicant を再起動して接続を試みます。"
# sudo systemctl restart wpa_supplicant
# sleep 5
#
# # 接続状態の確認
# if iw dev wlan0 link | grep -q "Not connected"; then
#   echo "※ 注意: Wi-Fi接続に失敗しました。（セットアップ時は、ギャラリー用Wi-Fiを設定するため実際の接続は期待していません。）"
# else
#   echo "Wi-Fi接続に成功しました。"
# fi

############################
# 5. rpi-rgb-led-matrix リポジトリのクローンとビルド
############################
# github.com に接続できるかチェックする関数
check_network() {
  local RETRY=0
  local MAX_RETRY=5
  while ! ping -c 1 github.com &>/dev/null; do
    RETRY=$((RETRY+1))
    if [ "$RETRY" -ge "$MAX_RETRY" ]; then
      echo "ネットワーク接続に失敗しました。github.com に接続できません。"
      exit 1
    fi
    echo "ネットワーク接続待機中... ($RETRY/$MAX_RETRY)"
    sleep 5
  done
}

echo "=== rpi-rgb-led-matrix のクローンとビルド ==="
cd ~
if [ ! -d "rpi-rgb-led-matrix" ]; then
  echo "github.com への接続を確認します..."
  check_network
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
sudo python3 sample_view.py --no-hardware-pulse --gpio-slowdown=4 --chain-length=1 --parallel=1 --pwm-bits=9 --pwm-lsb-nanoseconds=100 --image ./samples/oracle_sample.png

############################
# 7. Python の cap_sys_nice 権限設定
############################
echo "=== Python の権限設定 (cap_sys_nice) ==="
sudo setcap 'cap_sys_nice=eip' /usr/bin/python3.11

echo "=== セットアップ完了 ==="
