# Smart Frame

A smart e-ink display picture frame made as a gift. It listens for changes in a Google Cloud Firestore database, allows for overrides by the user using the buttons on the frame, and communicates with the [Smart Clock](https://github.com/GrandmaFunk/smart-clock) by writing a value to the database which will cause a pixel on the clock to blink.

Messages are automatically centered and a random font is selected. New images are downloaded from Google Cloud Storage and automatically resized.

This frame is meant for the [Pimoroni Inky Impressions](https://shop.pimoroni.com/products/inky-impression-5-7) e-ink display.

![smart-frame](smart-frame.jpg)

## Running on Boot

As an alternative to cron, the ```systemd``` files are included in the ```service``` directory, but should be placed in the ```/etc/systemd/system``` directory and scheduled to run on boot if desired using the following commands:

```
sudo cp service/check_memo.service /etc/systemd/system/check_memo.service
sudo cp service/check_memo.timer /etc/systemd/system/check_memo.timer
cd /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable check_memo.timer
sudo systemctl enable check_memo.service
```

## Secrets Storage

An uncommitted `.secrets` directory holds the `key.json` Google Authentication Credentials and a `vars.json` file with values for the name of the GCP project (`cloud_project`) and the name of the Google Cloud Storage bucket (`bucket_name`).