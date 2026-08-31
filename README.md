# Roma Bot

This is a discord bot for [Roma's discord server](https://discord.gg/9aqmDgpb7a) made with `discord.py`.

## Requirements

- Python 3.10+
- pip
- Discord Bot Application + Token ([Discord Developer Portal](https://discord.com/developers/applications))

## 1. Clone the repo

```bash
git clone https://github.com/FabBeyond/RomaBot.git
cd RomaBot
```

## 2. Create a virtual environment
 
```bash
python3 -m venv venv
source venv/bin/activate      # Linux/macOS
# venv\Scripts\activate       # Windows
```

## 3. Install dependencies
 
```bash
pip install -r requirements.txt
```

## 4. Configure environment variables
 
Create a `.env` file in the project root:
 
```env
bot-token=your-bot-token-here
```


## 7. Run the bot

If you set up romabot.service for systemctl:
```bash
./run.sh
```
Else:
```bash
python bot.py
```
