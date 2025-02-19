#!/usr/bin/env python3
import os
import time
import glob

import click
from PIL import Image
from rgbmatrix import RGBMatrix, RGBMatrixOptions


def get_latest_image_path(folder):
    """
    指定フォルダ内のファイルのうち、最も新しい画像ファイルのパスを返す。
    画像ファイルが無い場合は None を返す。
    """
    valid_extensions = (".jpg", ".jpeg", ".png", ".gif", ".bmp")
    files = glob.glob(os.path.join(folder, "*"))
    if not files:
        return None

    # 更新時刻が新しい順にソート
    files.sort(key=os.path.getmtime, reverse=True)
    for file_path in files:
        if file_path.lower().endswith(valid_extensions):
            return file_path
    return None


def setup_matrix(rows, cols, chain_length, parallel,
                 hardware_mapping, gpio_slowdown, no_hardware_pulse,
                 pwm_bits, pwm_lsb_nanoseconds):
    """
    rpi-rgb-led-matrix のオプションを設定し、RGBMatrix インスタンスを返す。
    今回は物理ハードウェアは1段分なので、parallel は 1 を指定してセットアップします。
    """
    options = RGBMatrixOptions()
    options.rows = rows
    options.cols = cols
    options.chain_length = chain_length
    # 物理的なパネルは1段分なので、ここでは parallel=1 としておく
    options.parallel = 1
    options.hardware_mapping = hardware_mapping

    if gpio_slowdown is not None:
        options.gpio_slowdown = gpio_slowdown
    if no_hardware_pulse:
        options.disable_hardware_pulsing = True

    options.pwm_bits = pwm_bits
    options.pwm_lsb_nanoseconds = pwm_lsb_nanoseconds

    return RGBMatrix(options=options)


@click.command()
@click.option('--watch-folder', '-w', default='./samples',
              help='監視するフォルダのパス')
@click.option('--image', default=None, type=str,
              help='表示する画像ファイルのパス。指定された場合、監視フォルダではなくこの画像を表示します。')
@click.option('--rows', default=64, type=int,
              help='パネル1枚あたりの行数')
@click.option('--cols', default=64, type=int,
              help='パネル1枚あたりの列数')
@click.option('--chain-length', default=3, type=int,
              help='横方向に連結されたパネル数')
@click.option('--parallel', default=3, type=int,
              help='全体画像を縦方向に分割する段数。各ハードウェアは1段分を表示します')
@click.option('--hardware-mapping', default='regular',
              help='rpi-rgb-led-matrix での配線方法 (例: "regular", "adafruit-hat" 等)')
@click.option('--gpio-slowdown', default=0, type=int,
              help='GPIO のスローダウン設定。0で最大フレッシュレート（ただしハードウェアの安定性に注意）')
@click.option('--no-hardware-pulse', is_flag=True,
              help='ハードウェアパルス無効化（root権限不要で実行する場合に指定）')
@click.option('--pwm-bits', default=7, type=int,
              help='PWM ビット数。低い値ほど高フレッシュレートになるが色の階調が減少')
@click.option('--pwm-lsb-nanoseconds', default=80, type=int,
              help='PWM LSB nanoseconds。低い値ほど高フレッシュレートになる')
@click.option('--idx', default=1, type=int,
              help='全体画像の中で表示する段の番号 (上から1～parallel)。例えば --parallel=3 の場合、--idx 1,2,3 でそれぞれ上、中、下の部分を表示')
def main(watch_folder, image, rows, cols, chain_length, parallel,
         hardware_mapping, gpio_slowdown, no_hardware_pulse,
         pwm_bits, pwm_lsb_nanoseconds, idx):
    """
    LED パネルをセットアップし、以下のいずれかの画像を表示します。

    - --image が指定された場合は、その画像ファイルを表示。
    - 指定がない場合は、監視フォルダ内の最新画像を表示。

    全体画像は、
      横: chain-length * cols
      縦: parallel * rows
    の解像度で構成され、上から idx 番目の段 (高さ rows) をクロップして
    物理的な LED パネル（1段分）に表示します。

    各ハードウェアは物理的に1段分の表示（解像度: 横 = chain-length×cols, 縦 = rows）を行います。
    複数台のハードウェアで全体画像の各段を表示する場合、
    各ハードウェアには同じ画像を渡し、--parallel で全体の段数、--idx で表示する段番号 (上から) を指定してください。
    """
    # 全体画像の想定解像度
    overall_width = cols * chain_length
    overall_height = rows * parallel
    # 物理的な表示解像度（各ハードウェアは1段分）
    physical_width = overall_width
    physical_height = rows

    # 物理ハードウェアは1段なので、matrix の parallel は常に 1
    matrix = setup_matrix(rows, cols, chain_length, parallel=1,
                          hardware_mapping=hardware_mapping,
                          gpio_slowdown=gpio_slowdown,
                          no_hardware_pulse=no_hardware_pulse,
                          pwm_bits=pwm_bits,
                          pwm_lsb_nanoseconds=pwm_lsb_nanoseconds)

    canvas = matrix.CreateFrameCanvas()
    current_displayed_path = None

    # idx の値を 1 ～ parallel の範囲に補正
    if idx < 1:
        idx = 1
    if idx > parallel:
        idx = parallel

    try:
        while True:
            # --image が指定されている場合はそちらを利用、それ以外は監視フォルダ内の最新画像を取得
            if image is not None:
                new_path = image
            else:
                new_path = get_latest_image_path(watch_folder)

            if new_path and new_path != current_displayed_path:
                try:
                    img = Image.open(new_path).convert("RGB")
                    if parallel > 1:
                        # まず、元画像を全体画像の解像度にリサイズ
                        img = img.resize((overall_width, overall_height), Image.Resampling.LANCZOS)
                        # 上から idx 番目の段をクロップする
                        crop_top = (idx - 1) * rows
                        crop_bottom = idx * rows
                        img = img.crop((0, crop_top, overall_width, crop_bottom))
                        # クロップ後の画像は (overall_width, rows) となるので、物理パネルに合わせて表示
                        canvas.Clear()
                        canvas.SetImage(img, 0, 0)
                        print(f"[INFO] Displayed cropped image (idx={idx}) from {new_path}")
                    else:
                        # parallel==1 の場合は、全体画像を物理解像度にリサイズして表示
                        img = img.resize((physical_width, physical_height), Image.Resampling.LANCZOS)
                        canvas.Clear()
                        canvas.SetImage(img, 0, 0)
                        print(f"[INFO] Displayed full image (parallel=1) from {new_path}")

                    canvas = matrix.SwapOnVSync(canvas)
                    current_displayed_path = new_path
                except Exception as e:
                    print(f"[ERROR] Failed to display {new_path}: {e}")
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting gracefully.")


if __name__ == '__main__':
    main()
