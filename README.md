# How to Run

### Configuration file

Create a configuration file **config.json** and add:
```
{
    "DISCORD_TOKEN":"TOKEN",
    "COOKIES_YOUTUBE":"path_to_cookies_file.txt"
}
```
---

### Cookies file

To extract the cookies, you need to be logged in with a gmail account and access youtube. Then you can use this tool to get the cookie file for [Firefox](https://addons.mozilla.org/en-US/firefox/addon/get-cookies-txt-locally/) and [Chrome](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc).

You can test if the cookie file is correct using this command with a valid YouTube link:
```
yt-dlp --cookies path_to_cookies_file.txt "link_to_youtube_video"
```

---

### Virtual Environment

You can create a virtual environment with the following command:
```
python3 -m venv venv
```
To install the necessary packages you can use:
```
pip install -r requirements.txt
```

---

### Run the Application

You can run the application with:
```
python3 tot.py
```

---

### Run the Application as a Service

You can create a service file in **/etc/systemd/system/bot.service**. Then you can configure the service with the following example:
```
[Unit]
Description=Discord Bot
After=multi-user.target network-online.target

[Service]
WorkingDirectory=/home/arnau/Desktop/discord-music-bot
ExecStart=/home/arnau/Desktop/discord-music-bot/venv/bin/python /home/arnau/Desktop/discord-music-bot/tot.py
Type=idle
Restart=on-failure
TimeoutStartSec=8
RestartSec=5

[Install]
WantedBy=multi-user.target
```
Then you'll have to run these commands:
```
sudo systemctl daemon-reload
systemctl start bot
sudo systemctl restart bot
sudo systemctl status bot.service
sudo journalctl -u bot.service -f  #Check the live outputs 
```
