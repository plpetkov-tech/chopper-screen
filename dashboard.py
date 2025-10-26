#!/usr/bin/env python3
import subprocess
import pygame
import os
import time
import glob
import logging
from datetime import datetime, time as dt_time
import schedule

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ScreenDashboard:
    def __init__(self):
        # URL and refresh settings
        self.url = os.getenv('DISPLAY_URL', 'https://google.com')
        self.refresh_interval = int(os.getenv('REFRESH_INTERVAL', '300'))

        # Night mode settings
        self.night_mode_enabled = os.getenv('NIGHT_MODE_ENABLED', 'true').lower() == 'true'
        self.night_start = os.getenv('NIGHT_START', '22:00')
        self.night_end = os.getenv('NIGHT_END', '07:00')

        # Display settings
        self.window_width = int(os.getenv('WINDOW_WIDTH', '800'))
        self.window_height = int(os.getenv('WINDOW_HEIGHT', '600'))
        self.rotation = int(os.getenv('ROTATION', '0'))  # Rotation in degrees: 0, 90, 180, 270

        # Validate rotation
        if self.rotation not in [0, 90, 180, 270]:
            logger.warning(f"Invalid rotation {self.rotation}, defaulting to 0")
            self.rotation = 0

        # Chromium settings
        self.chromium_path = os.getenv('CHROMIUM_PATH', 'chromium-browser')
        self.chromium_timeout = int(os.getenv('CHROMIUM_TIMEOUT', '30'))
        self.screenshot_path = os.getenv('SCREENSHOT_PATH', '/tmp/screenshot.png')

        # Backlight settings
        self.backlight_path = os.getenv('BACKLIGHT_PATH', '')
        self.backlight_max = int(os.getenv('BACKLIGHT_MAX', '255'))

        # Auto-detect backlight if not specified
        if not self.backlight_path:
            backlight_devices = glob.glob('/sys/class/backlight/*/brightness')
            if backlight_devices:
                self.backlight_path = backlight_devices[0]
                logger.info(f"Auto-detected backlight device: {self.backlight_path}")

        # Initialize pygame with appropriate video driver
        self.screen = self._initialize_display()
        logger.info(f"Dashboard initialized - URL: {self.url}, Refresh: {self.refresh_interval}s")

    def _initialize_display(self):
        """Initialize pygame display with fallback drivers"""
        fullscreen = os.getenv('FULLSCREEN', 'true').lower() == 'true'

        # Try drivers in order: kmsdrm (modern), fbcon (legacy), directfb, dummy (fallback)
        drivers = ['kmsdrm', 'fbcon', 'directfb', 'dummy']

        # Allow override from environment
        preferred_driver = os.getenv('SDL_VIDEODRIVER', '')
        if preferred_driver:
            drivers.insert(0, preferred_driver)

        last_error = None
        for driver in drivers:
            try:
                logger.info(f"Attempting to initialize display with driver: {driver}")
                os.environ['SDL_VIDEODRIVER'] = driver
                pygame.init()

                if fullscreen:
                    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                else:
                    screen = pygame.display.set_mode((self.window_width, self.window_height))

                logger.info(f"Successfully initialized display with driver: {driver}")
                return screen

            except pygame.error as e:
                last_error = e
                logger.warning(f"Driver {driver} failed: {e}")
                pygame.quit()
                continue

        # If all drivers failed, raise the last error
        raise RuntimeError(f"Failed to initialize display with any driver. Last error: {last_error}")

    def take_screenshot(self):
        """Take screenshot of webpage using headless chrome"""
        cmd = [
            self.chromium_path,
            '--headless',
            '--disable-gpu',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-software-rasterizer',
            f'--screenshot={self.screenshot_path}',
            f'--window-size={self.window_width},{self.window_height}',
            self.url
        ]

        try:
            subprocess.run(cmd, check=True, timeout=self.chromium_timeout)
            logger.info(f"Screenshot captured: {self.screenshot_path}")
            return self.screenshot_path
        except subprocess.TimeoutExpired:
            logger.error(f"Screenshot timed out after {self.chromium_timeout}s")
            raise
        except subprocess.CalledProcessError as e:
            logger.error(f"Chromium failed with exit code {e.returncode}")
            raise

    def display_image(self, image_path):
        """Display image on framebuffer"""
        try:
            image = pygame.image.load(image_path)

            # Apply rotation if set
            if self.rotation != 0:
                image = pygame.transform.rotate(image, self.rotation)
                logger.debug(f"Image rotated by {self.rotation} degrees")

            # Scale to screen size
            screen_size = self.screen.get_size()
            image = pygame.transform.scale(image, screen_size)

            self.screen.blit(image, (0, 0))
            pygame.display.flip()
            logger.info("Image displayed successfully")
        except Exception as e:
            logger.error(f"Error displaying image: {e}")
            raise

    def set_backlight(self, value):
        """Set backlight brightness"""
        if not self.backlight_path:
            return

        try:
            with open(self.backlight_path, 'w') as f:
                f.write(str(value))
            logger.debug(f"Backlight set to {value}")
        except Exception as e:
            logger.warning(f"Failed to set backlight: {e}")

    def turn_off_screen(self):
        """Turn off screen by filling with black"""
        self.screen.fill((0, 0, 0))
        pygame.display.flip()
        self.set_backlight(0)
        logger.info("Screen turned off")

    def turn_on_screen(self):
        """Turn screen back on"""
        self.set_backlight(self.backlight_max)
        logger.debug("Screen turned on")

    def is_night_time(self):
        """Check if current time is in night hours"""
        if not self.night_mode_enabled:
            return False

        now = datetime.now().time()

        try:
            start_time = dt_time.fromisoformat(self.night_start)
            end_time = dt_time.fromisoformat(self.night_end)
        except ValueError as e:
            logger.error(f"Invalid time format: {e}")
            return False

        # Handle overnight ranges (e.g., 22:00 to 07:00)
        if start_time > end_time:
            return now >= start_time or now <= end_time
        else:
            return start_time <= now <= end_time

    def update_display(self):
        """Main update function"""
        try:
            if self.is_night_time():
                logger.info("Night time - turning off screen")
                self.turn_off_screen()
            else:
                logger.info(f"Updating display with {self.url}")
                screenshot = self.take_screenshot()
                self.display_image(screenshot)
                self.turn_on_screen()
        except Exception as e:
            logger.error(f"Error updating display: {e}", exc_info=True)

if __name__ == '__main__':
    logger.info("Starting Screen Dashboard")

    try:
        dashboard = ScreenDashboard()

        # Schedule updates
        schedule.every(dashboard.refresh_interval).seconds.do(dashboard.update_display)

        # Initial update
        dashboard.update_display()

        # Keep running
        check_interval = int(os.getenv('CHECK_INTERVAL', '60'))
        logger.info(f"Entering main loop (check every {check_interval}s)")

        while True:
            schedule.run_pending()
            time.sleep(check_interval)

    except KeyboardInterrupt:
        logger.info("Shutting down gracefully")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise
