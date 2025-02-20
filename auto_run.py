#!/usr/bin/env python3
import socket
import subprocess
import sys

# config.py から読み込む
from config.config import PI_CONFIG

def main():
    # 1. ホスト名を取得
    hostname = socket.getfqdn()  # または gethostname()。環境によっては ".local" がつかない場合もあるので必要に応じて調整

    # 2. config.py から該当ホストの設定を探す
    host_config = None
    for setting in PI_CONFIG['settings']:
        if setting['host'] == hostname:
            host_config = setting
            break

    # 該当が見つからない場合は終了
    if host_config is None:
        print(f"[ERROR] No matching config found for hostname: {hostname}")
        sys.exit(1)

    # 3. 共通設定を取得
    gpio_slowdown = PI_CONFIG['gpio-slowdown']
    no_hardware_pulse = PI_CONFIG['no_hardware_pulse']
    pwm_bits = PI_CONFIG['led-pwm-bits']
    pwm_lsb_nanosecond = PI_CONFIG['pwm-lsb-nanosecond']

    # 4. ホスト固有のパラメータを取得
    chain_length = host_config['chain_length']
    parallel = host_config['parallel']
    idx = host_config['idx']
    watch_folder = host_config['target_dir']

    # 5. 特定ホストでパラメータを上書きしたい場合の例：
    #    ここでは zero2wh06.local の場合のみ pwm_bits=8 とし、
    #    それ以外は config.py で定義されたデフォルト値(4)を使う
    # if hostname == "zero2wh06.local":
    #     pwm_bits = 8
    # else:
    #     pwm_bits = default_pwm_bits

    # 6. コマンドを組み立て
    cmd_list = [
        "sudo",
        "python3",
        "run_led_viewer.py",
        "--gpio-slowdown", str(gpio_slowdown),
        "--chain-length", str(chain_length),
        "--parallel", str(parallel),
        "--pwm-bits", str(pwm_bits),
        "--idx", str(idx),
        "--pwm-lsb-nanosecond", str(pwm_lsb_nanosecond),
        "--watch-folder", watch_folder,
    ]

    # True なら --no-hardware-pulse オプションを付与
    if no_hardware_pulse:
        cmd_list.append("--no-hardware-pulse")

    # 7. コマンドの確認用出力
    print("[INFO] Running command:")
    print("       " + " ".join(cmd_list))

    # 8. 実行
    subprocess.run(cmd_list)

if __name__ == "__main__":
    main()
