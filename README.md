# Android Screen Mirroring tool

adb を使って Android の画面をミラーリングします。
Oculus Go にも使えます。


## Install 方法 (Windows)

1. python (3.x) を install します
2. pip を使って opencv と pywin32 を install します
  1. pip3 install opencv-python
  2. pip3 install pywin32
3. adb を install してください (Android SDK の install で OK)
4. adb.exe にパスを通してください
  - AndroidStudio の場合は C:/Users/<USERNAME>/AppData/Local/Android/sdk/platform-tools あたりにあります


## Install 方法 (Linux)

    $ sudo atp install python3-pip
    $ pip3 install opencv-python
    $ sudo atp install adb


## 接続方法

1. Android 端末を Developer mode にします
2. Android 端末を USB でつなぎます

[Android Developer: Run apps on a hardware device](https://developer.android.com/studio/run/device)

adb の Wi-Fi 接続も可能です。

[Android Developer: Android Debug Bridge (adb)](https://developer.android.com/studio/command-line/adb)


## Mirroring

    python android_mirrortool.py

画面に動きがないと Windows が出ません。

Wi-Fi の場合は bitrate や画面サイズを下げてください。

    python android_mirrortool.py --bitrate 4m --size 1280x720



## Screen Capture

    python android_mirrortool.py -c

png で保存します。



## 参考にした情報

http://answers.opencv.org/question/28744/python-cv2videocapture-from-subprocesspipe/




