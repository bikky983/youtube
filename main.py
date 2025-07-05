import time
import logging
import argparse
from youtube_bot import YouTubeBot
from config import ERROR_LOG_FILE

def parse_arguments():
    parser = argparse.ArgumentParser(description='YouTube Auto-Comment Bot')
    parser.add_argument(
        '--interval', 
        type=int, 
        default=3600,
        help='Interval between checks in seconds (default: 3600)'
    )
    parser.add_argument(
        '--run-once',
        action='store_true',
        help='Run the bot only once and exit'
    )
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    # Configure console logging
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # Get the root logger and add console handler
    root_logger = logging.getLogger()
    root_logger.addHandler(console_handler)
    
    logging.info("Starting YouTube Auto-Comment Bot")
    
    bot = YouTubeBot()
    
    if args.run_once:
        logging.info("Running bot once")
        bot.run()
        return
    
    logging.info(f"Bot will check for new videos every {args.interval} seconds")
    
    try:
        while True:
            bot.run()
            logging.info(f"Sleeping for {args.interval} seconds")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Bot stopped due to error: {str(e)}")

if __name__ == "__main__":
    main() 