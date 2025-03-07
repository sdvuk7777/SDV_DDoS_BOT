import os
import random
import threading
import time
import logging
from datetime import datetime
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from flask import Flask, request

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Constants
WELCOME_IMAGES = [
    "https://telegra.ph/file/3f42d9aebe57894a5ef36.jpg",
    "https://telegra.ph/file/5bb4723d4c9271a2d626b.jpg",
    "https://telegra.ph/file/75bb8bb0d0097b64f163e.jpg",
    "https://telegra.ph/file/0c9de0690b9f0e4312531.jpg",
    "https://telegra.ph/file/b564108627b77e5bf1238.jpg",
    "https://telegra.ph/file/77c7580b6eeadf8afacc6.jpg",
    "https://telegra.ph/file/c5a9dd3e18e3a8c96575a.jpg",
]

LOG_GROUP_ID = "-1002238698538"  # Replace with your log group ID
MAX_REQUESTS = 1000000
UPDATE_INTERVAL = 300  # 5 minutes in seconds

# Dictionary to store active attacks
active_attacks = {}

# Flask app for webhook
app = Flask(__name__)

class SimulatedDDoSAttack:
    def __init__(self, target_url, user_id, username, context, chat_id, message_id):
        self.target_url = target_url
        self.user_id = user_id
        self.username = username
        self.context = context
        self.chat_id = chat_id
        self.message_id = message_id
        self.stop_event = threading.Event()
        self.sent_requests = 0
        self.start_time = datetime.now()
        self.update_thread = None
        self.attack_thread = None

    async def send_requests(self):
        """Simulate sending requests without actually performing a DDoS attack"""
        try:
            while not self.stop_event.is_set() and self.sent_requests < MAX_REQUESTS:
                try:
                    if self.sent_requests == 0:
                        response = requests.head(self.target_url, timeout=5)
                        logger.info(f"Verified URL exists: {self.target_url} | Status Code: {response.status_code}")
                    
                    increment = random.randint(50, 200)
                    self.sent_requests += increment
                    if self.sent_requests > MAX_REQUESTS:
                        self.sent_requests = MAX_REQUESTS
                    
                    time.sleep(0.5)
                    
                except requests.exceptions.RequestException as e:
                    logger.error(f"Error connecting to {self.target_url}: {e}")
                    await self.context.bot.send_message(
                        chat_id=self.chat_id,
                        text=f"❌ Error: Could not connect to {self.target_url}\n\nError details: {str(e)}"
                    )
                    self.stop_event.set()
                    break
        except Exception as e:
            logger.error(f"Unexpected error in send_requests: {e}")
            await self.context.bot.send_message(
                chat_id=self.chat_id,
                text=f"❌ Internal error occurred: {str(e)}"
            )
            self.stop_event.set()

    async def update_status(self):
        """Update the status message periodically"""
        try:
            while not self.stop_event.is_set() and self.sent_requests < MAX_REQUESTS:
                elapsed_time = (datetime.now() - self.start_time).total_seconds()
                
                status_message = (
                    f"🚀 *EDUCATIONAL SIMULATION IN PROGRESS*\n\n"
                    f"🔗 Target URL: `{self.target_url}`\n"
                    f"📊 Requests Sent: `{self.sent_requests:,}/{MAX_REQUESTS:,}`\n"
                    f"⏱ Elapsed Time: `{int(elapsed_time // 60)} min {int(elapsed_time % 60)} sec`\n\n"
                    f"Type /stop to end the simulation"
                )
                
                try:
                    await self.context.bot.delete_message(chat_id=self.chat_id, message_id=self.message_id)
                except Exception:
                    pass
                
                new_message = await self.context.bot.send_message(
                    chat_id=self.chat_id,
                    text=status_message,
                    parse_mode='Markdown'
                )
                self.message_id = new_message.message_id
                
                for _ in range(UPDATE_INTERVAL):
                    if self.stop_event.is_set() or self.sent_requests >= MAX_REQUESTS:
                        break
                    time.sleep(1)
                
                if self.sent_requests >= MAX_REQUESTS:
                    await self.context.bot.delete_message(chat_id=self.chat_id, message_id=self.message_id)
                    await self.context.bot.send_message(
                        chat_id=self.chat_id,
                        text=f"✅ Simulation completed!\n\n"
                             f"🔗 Target URL: `{self.target_url}`\n"
                             f"📊 Total Requests: `{self.sent_requests:,}`\n"
                             f"⏱ Total Time: `{int(elapsed_time // 60)} min {int(elapsed_time % 60)} sec`",
                        parse_mode='Markdown'
                    )
                    self.stop_event.set()
        except Exception as e:
            logger.error(f"Error in update_status: {e}")
            await self.context.bot.send_message(
                chat_id=self.chat_id,
                text=f"❌ Error updating status: {str(e)}"
            )
            self.stop_event.set()

    async def start(self):
        """Start the attack simulation"""
        try:
            await self.log_attack_start()
            
            self.attack_thread = threading.Thread(target=self.run_attack)
            self.attack_thread.daemon = True
            self.attack_thread.start()
            
            self.update_thread = threading.Thread(target=self.run_update)
            self.update_thread.daemon = True
            self.update_thread.start()
            
        except Exception as e:
            logger.error(f"Error starting attack: {e}")
            await self.context.bot.send_message(
                chat_id=self.chat_id,
                text=f"❌ Failed to start simulation: {str(e)}"
            )
            self.stop_event.set()

    def run_attack(self):
        """Run the attack in a thread-safe way"""
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.send_requests())
        loop.close()

    def run_update(self):
        """Run the update in a thread-safe way"""
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.update_status())
        loop.close()

    async def stop(self):
        """Stop the attack simulation"""
        self.stop_event.set()
        await self.log_attack_stop()
        
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        
        try:
            await self.context.bot.delete_message(chat_id=self.chat_id, message_id=self.message_id)
        except Exception:
            pass
        
        await self.context.bot.send_message(
            chat_id=self.chat_id,
            text=f"🛑 Simulation stopped!\n\n"
                 f"🔗 Target URL: `{self.target_url}`\n"
                 f"📊 Requests Sent: `{self.sent_requests:,}/{MAX_REQUESTS:,}`\n"
                 f"⏱ Duration: `{int(elapsed_time // 60)} min {int(elapsed_time % 60)} sec`",
            parse_mode='Markdown'
        )

    async def log_attack_start(self):
        """Log attack start to the log group"""
        try:
            log_message = (
                f"🚨 *NEW SIMULATION STARTED*\n\n"
                f"👤 User: @{self.username} (ID: `{self.user_id}`)\n"
                f"🔗 Target URL: `{self.target_url}`\n"
                f"⏰ Started at: `{self.start_time.strftime('%Y-%m-%d %H:%M:%S')}`"
            )
            
            await self.context.bot.send_message(
                chat_id=LOG_GROUP_ID,
                text=log_message,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error logging attack start: {e}")

    async def log_attack_stop(self):
        """Log attack stop to the log group"""
        try:
            stop_time = datetime.now()
            elapsed_time = (stop_time - self.start_time).total_seconds()
            
            log_message = (
                f"🛑 *SIMULATION STOPPED*\n\n"
                f"👤 User: @{self.username} (ID: `{self.user_id}`)\n"
                f"🔗 Target URL: `{self.target_url}`\n"
                f"📊 Requests Sent: `{self.sent_requests:,}/{MAX_REQUESTS:,}`\n"
                f"⏱ Duration: `{int(elapsed_time // 60)} min {int(elapsed_time % 60)} sec`\n"
                f"⏰ Stopped at: `{stop_time.strftime('%Y-%m-%d %H:%M:%S')}`"
            )
            
            await self.context.bot.send_message(
                chat_id=LOG_GROUP_ID,
                text=log_message,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error logging attack stop: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when the command /start is issued."""
    try:
        user = update.effective_user
        random_image = random.choice(WELCOME_IMAGES)
        
        welcome_message = (
            f"🌟 Welcome {user.first_name}! 🌟\n\n"
            f"👋 Hi there @{user.username}! Welcome to the Educational DDoS Simulation Bot.\n\n"
            f"💡 This bot is for educational purposes only to understand how DDoS attacks work.\n\n"
            f"🚀 Use the /atck command to start a simulation against a test website."
        )
        
        await update.message.reply_photo(
            photo=random_image,
            caption=welcome_message,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await update.message.reply_text(f"Sorry, an error occurred: {str(e)}")

async def attack_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /atck command - ask for URL."""
    try:
        user = update.effective_user
        user_id = user.id
        
        if user_id in active_attacks:
            await update.message.reply_text(
                "❌ You already have an active simulation running.\n"
                "Please use /stop to end it before starting a new one."
            )
            return
        
        await update.message.reply_text(
            "🔗 Please enter the target website URL:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Cancel", callback_data="cancel_attack")]
            ])
        )
    except Exception as e:
        logger.error(f"Error in attack_command: {e}")
        await update.message.reply_text(f"Sorry, an error occurred: {str(e)}")

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the URL input from the user."""
    try:
        user = update.effective_user
        user_id = user.id
        username = user.username or user.first_name
        url = update.message.text
        
        if not (url.startswith('http://') or url.startswith('https://')):
            await update.message.reply_text(
                "❌ Invalid URL format. Please enter a URL starting with http:// or https://"
            )
            return
        
        await update.message.delete()
        
        status_message = await update.message.reply_text(
            f"🚀 *PREPARING SIMULATION*\n\n"
            f"🔗 Target URL: `{url}`\n"
            f"⏳ Initializing...",
            parse_mode='Markdown'
        )
        
        attack = SimulatedDDoSAttack(
            target_url=url,
            user_id=user_id,
            username=username,
            context=context,
            chat_id=update.effective_chat.id,
            message_id=status_message.message_id
        )
        
        active_attacks[user_id] = attack
        await attack.start()
    except Exception as e:
        logger.error(f"Error in handle_url: {e}")
        await update.message.reply_text(f"Sorry, an error occurred: {str(e)}")

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop the attack when /stop command is issued."""
    try:
        user = update.effective_user
        user_id = user.id
        
        if user_id in active_attacks:
            attack = active_attacks[user_id]
            await attack.stop()
            del active_attacks[user_id]
        else:
            await update.message.reply_text("❌ You don't have any active simulations to stop.")
    except Exception as e:
        logger.error(f"Error in stop_command: {e}")
        await update.message.reply_text(f"Sorry, an error occurred: {str(e)}")

async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the cancel button callback."""
    try:
        query = update.callback_query
        await query.answer()
        await query.message.edit_text("✅ Attack preparation cancelled.")
    except Exception as e:
        logger.error(f"Error in cancel_callback: {e}")
        await update.callback_query.message.reply_text(f"Sorry, an error occurred: {str(e)}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors caused by updates."""
    logger.error(f"Update {update} caused error: {context.error}")
    try:
        if update:
            await update.message.reply_text(
                "❌ An unexpected error occurred. Please try again later."
            )
    except Exception:
        pass

# Flask route for webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put(update)
    return 'ok'

def main():
    """Start the bot."""
    token = "7841232248:AAHCJnnIQijECkKUUsNfJ7M2pBqmn9zzRWk"  # Replace with your bot token
    env_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if env_token:
        token = env_token
        
    if not token or token == "YOUR_BOT_TOKEN_HERE":
        logger.error("No valid token provided. Please edit the script to add your bot token.")
        return
    
    # Create the application
    global application
    application = Application.builder().token(token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("atck", attack_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CallbackQueryHandler(cancel_callback, pattern="^cancel_attack$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Entity("url"), handle_url))
    application.add_error_handler(error_handler)
    
    # Set webhook
    webhook_url = "https://sdv-ddos-bot.onrender.com/webhook"  # Replace with your Render app URL
    application.bot.set_webhook(webhook_url)
    
    # Start Flask server
    app.run(host='0.0.0.0', port=10000)

if __name__ == "__main__":
    main()