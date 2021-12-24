A smart e-ink display picture frame made as a gift. It listens for changes in a Google Cloud database, allows for overrides by the user, and communicates with the [Smart Clock](https://github.com/GrandmaFunk/smart-clock) by sending a value which will cause a pixel on the clock to blink. Automatically centers messages and crops images. This frame is meant for the Pimoroni Inky Impressions e-ink display.

The service files are included, but should be places in the /etc/systemd/system directory and scheduled to run on boot if desired.

```
sudo cp service/check_memo.service /etc/systemd/system/check_memo.service
sudo cp service/check_memo.timer /etc/systemd/system/check_memo.timer
cd /etc/systemd/system/check_memo.timer
sudo systemctl daemon-reload
sudo systemctl enable check_memo.timer
sudo systemctl start check_memo.timer
```
