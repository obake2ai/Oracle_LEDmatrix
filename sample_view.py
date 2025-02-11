#!/usr/bin/env python3
import os
import time
import glob

import click
from PIL import Image
from rgbmatrix import RGBMatrix, RGBMatrixOptions


def get_latest_image_path(folder):
    """
    指定フォルダ内のファイルのうち、もっとも新しい画像ファイルのパスを返す。
    画像ファイルが無い場合は None を返す。
    """
    valid_extensions = (".jpg", ".jpeg", ".png", ".gif", ".bmp")
    files = glob.glob(os.path.join(folder, "*"))

    if not files:
        return None

    # 更新時刻が新しい順にソート
    files.sort(key=os.path.getmtime, reverse=True)

    # 画像ファイルかどうかを確認し、一番最初に見つかった画像ファイルを返す
    for file_path in files:
        if file_path.lower().endswith(valid_extensions):
            return file_path

    return None


def setup_matrix(rows, cols, chain_length, parallel,
                 hardware_mapping, gpio_slowdown, no_hardware_pulse,
                 pwm_bits, pwm_lsb_nanoseconds):
    """
    rpi-rgb-led-matrix のオプションを設定し、RGBMatrix インスタンスを返す。
    PWM 関連のパラメータを設定することでフレッシュレートの向上を試みる。
    """
    options = RGBMatrixOptions()
    options.rows = rows
    options.cols = cols
    options.chain_length = chain_length
    options.parallel = parallel
    options.hardware_mapping = hardware_mapping

    # GPIO スローダウン設定
    if gpio_slowdown is not None:
        options.gpio_slowdown = gpio_slowdown

    # ハードウェアパルス無効化の設定
    if no_hardware_pulse:
        options.disable_hardware_pulsing = True

    # PWM 関連の設定
    options.pwm_bits = pwm_bits
    options.pwm_lsb_nanoseconds = pwm_lsb_nanoseconds

    return RGBMatrix(options=options)


@click.command()
@click.option('--watch-folder', '-w', default='./samples',
              help='監視するフォルダのパス')
@click.option('--rows', default=64, type=int,
              help='パネル1枚あたりの行数')
@click.option('--cols', default=64, type=int,
              help='パネル1枚あたりの列数')
@click.option('--chain-length', default=3, type=int,
              help='横方向に連結されたパネル数')
@click.option('--parallel', default=3, type=int,
              help='縦方向に連結されたパネル数')
@click.option('--hardware-mapping', default='regular',
              help='rpi-rgb-led-matrix での配線方法 (例: "regular", "adafruit-hat" 等)')
@click.option('--gpio-slowdown', default=0, type=int,
              help='GPIO のスローダウン設定。0 で最大フレッシュレート (ただしハードウェアの安定性に注意)')
@click.option('--no-hardware-pulse', is_flag=True,
              help='--led-no-hardware-pulse 相当。root 権限不要で実行する場合に指定する。')
@click.option('--pwm-bits', default=7, type=int,
              help='PWM ビット数。低い値ほど高フレッシュレートになるが色の階調が減少')
@click.option('--pwm-lsb-nanoseconds', default=80, type=int,
              help='PWM LSB nanoseconds。低い値ほど高フレッシュレートになる')
@click.option('--idx', default=0, type=int,
              help='表示するパネルの行番号 (1～parallel)。0の場合は全体表示します')
def main(watch_folder, rows, cols, chain_length, parallel,
         hardware_mapping, gpio_slowdown, no_hardware_pulse,
         pwm_bits, pwm_lsb_nanoseconds, idx):
    """
    LED パネルをセットアップし、監視フォルダにある最新の画像を表示します。

    改善点:
    - ダブルバッファリング (CreateFrameCanvas と SwapOnVSync) により更新時のちらつきを低減
    - PWM ビット数と PWM LSB nanoseconds の調整により、フレッシュレート向上を試みる
    - 新たに --idx オプションを追加。これにより、画像を縦方向に分割し、
      指定された行 (1-indexed) の部分のみをクロップして表示できます。
      例: chain-length=3（解像度 192×192）で parallel=3 のとき、
           --idx 1 なら元画像の上部 1/3 をクロップし 192×64 にリサイズ、上段に表示。
           parallel=4, --idx 2 なら元画像の上から2番目の1/4の部分をクロップし表示。
    """
    # LEDマトリックスのセットアップ
    matrix = setup_matrix(rows, cols, chain_length, parallel,
                          hardware_mapping, gpio_slowdown, no_hardware_pulse,
                          pwm_bits, pwm_lsb_nanoseconds)

    # パネル全体の解像度 (例: 3x3パネル、各64x64 → 192x192)
    total_width = cols * chain_length
    total_height = rows * parallel

    # ダブルバッファリング用キャンバスの作成
    canvas = matrix.CreateFrameCanvas()

    # 現在表示中の画像パスを記録
    current_displayed_path = None

    try:
        while True:
            latest_image_path = get_latest_image_path(watch_folder)

            # 新しい画像ファイルが見つかった場合のみ再表示
            if latest_image_path and latest_image_path != current_displayed_path:
                try:
                    image = Image.open(latest_image_path).convert("RGB")

                    # --idx が 1 以上、かつ parallel の範囲内なら部分表示用のクロップ処理を実施
                    if 1 <= idx <= parallel:
                        # 画像全体を parallel 分割したうち、(idx) 番目の領域を抽出する
                        orig_width, orig_height = image.size
                        crop_top = int(orig_height * (idx - 1) / parallel)
                        crop_bottom = int(orig_height * idx / parallel)
                        image = image.crop((0, crop_top, orig_width, crop_bottom))
                        # リサイズ後のサイズは、横: パネル全体幅, 縦: 1パネル分 (rows)
                        image = image.resize((total_width, rows), Image.Resampling.LANCZOS)
                        # キャンバスをクリアして、対応するパネル行 (y オフセット (idx-1)*rows) に配置
                        canvas.Clear()
                        canvas.SetImage(image, 0, (idx - 1) * rows)
                        print(f"[INFO] Displayed cropped image (idx={idx}): {latest_image_path}")
                    else:
                        # --idx が指定されていない（または 0 または範囲外）場合は、画像全体を表示
                        image = image.resize((total_width, total_height), Image.Resampling.LANCZOS)
                        canvas.Clear()
                        canvas.SetImage(image, 0, 0)
                        print(f"[INFO] Displayed full image: {latest_image_path}")

                    # ダブルバッファリングでスムーズに画面更新
                    canvas = matrix.SwapOnVSync(canvas)
                    current_displayed_path = latest_image_path
                except Exception as e:
                    print(f"[ERROR] Failed to display {latest_image_path}: {e}")

            # 1秒ごとに監視フォルダを再確認
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting gracefully.")


if __name__ == '__main__':
    main()
