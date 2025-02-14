# Telegram Order Bot 🤖  
A Python-based Telegram bot for handling food orders and payments.  

## 📌 Features  
✅ Display menu items and prices  
✅ Handle user orders and track order history  
✅ Request user details like address  
✅ Accept payment receipt uploads  
✅ Admin approval system for orders  

---

## 🚀 Setup Guide  

### 1️⃣ Clone the Repository  
First, clone this repo to your local machine:  
```bash
git clone https://github.com/yourusername/telegram-order-bot.git
cd telegram-order-bot
```
### 2️⃣ Install Dependencies
Ensure you have Python 3.10+ installed. Then, install the required libraries:

```bash
pip install -r requirements.txt
```
### 3️⃣ Create a Telegram Bot
Open Telegram and search for BotFather.
#### Send the command /newbot.
#### Follow the instructions to name your bot and get a Bot Token.
#### Copy the token and store it securely.

### 4️⃣ Configure Environment Variables
Instead of storing the bot token in the code, use an .env file (or GitHub Secrets).

Create a .env file in the root directory:

```bash

BOT_TOKEN=your-telegram-bot-token
ADMIN_ID=your-admin-user-id
```
### 🤖 Automating with GitHub Actions
This repository includes a GitHub Actions workflow (.github/workflows/bot.yml) to automatically run the bot when pushing updates.

⚠️ However, GitHub Actions does not keep the bot running 24/7. Instead, it executes the script and stops when finished. If you need continuous execution, see the Deployment section below.

⚙️ Setting Up GitHub Actions
#### 1️⃣ Enable GitHub Actions
Go to Settings → Actions
Select Allow all actions and reusable workflows
#### 2️⃣ Workflow File (.github/workflows/bot.yml)
This repository includes a workflow to run the bot on GitHub Actions. It is located at:

```bash

.github/workflows/bot.yml
```

## Here’s what it does:

✅ Installs Python and dependencies  

✅ Runs the bot script (bot.py) when you push changes 

✅ Stops execution after running (not 24/7) 



#### 3️⃣ How to Manually Trigger the Workflow
To manually run the bot from GitHub Actions:

Go to the "Actions" tab in your repository.
Select the workflow and click "Run workflow".

### 🖥️ 5️⃣ Running the Bot Locally
After setting everything up, you can start the bot manually:

```bash

python bot.py
```
### 🚀 6️⃣ Deploying the Bot for 24/7 Uptime
Since GitHub Actions does not keep your bot running, you should deploy it to a cloud service like:

✅ Heroku (Free but has limitations)

✅ Railway.app (Free, easy setup)

✅ Render.com

✅ VPS (AWS / Google Cloud / DigitalOcean) (For full control)


