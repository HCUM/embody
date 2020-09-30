# ESP firmware
# emg_udp
Standard firmware that implements a config portal for Wi-Fi settings. It is based on WiFiManager (https://github.com/khoih-prog/ESP_WiFiManager).
If no SSID was previously registered, the config portal boots up automatically. Connect to the SSID "EMG_xxx" (where xxx is the Chip ID of your microcontroller) and use "emg" as password.
Navigate to "192.168.4.1" and configure Wi-Fi settings. On subsequent boot-ups, the microcontroller will try to connect to the provided configuration (Config portal boot can be forced by pressing the BOOT button).

# send_udp_V2
Custom firmware that hard codes Wi-Fi settings. Thus a change of settings requires flashing of firmware.