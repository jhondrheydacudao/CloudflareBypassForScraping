import time
import logging
import os
from flask import Flask, request, jsonify
from CloudflareBypasser import CloudflareBypasser
from DrissionPage import ChromiumPage, ChromiumOptions
from pyvirtualdisplay import Display

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('cloudflare_bypass.log', mode='w')
    ]
)

app = Flask(__name__)

def get_chromium_options(browser_path: str, arguments: list) -> ChromiumOptions:
    """
    Configures and returns Chromium options.
    
    :param browser_path: Path to the Chromium browser executable.
    :param arguments: List of arguments for the Chromium browser.
    :return: Configured ChromiumOptions instance.
    """
    options = ChromiumOptions().auto_port()
    options.set_paths(browser_path=browser_path)
    for argument in arguments:
        options.set_argument(argument)
    return options

@app.route('/bypass', methods=['GET'])
def bypass_cloudflare():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL parameter is required!"}), 400

    logging.info(f"🌐 Received request to bypass Cloudflare for URL: {url}")

    isHeadless = os.getenv('HEADLESS', 'false').lower() == 'true'
    if isHeadless:
        display = Display(visible=0, size=(1920, 1080))
        display.start()

    browser_path = os.getenv('CHROME_PATH', "/usr/bin/google-chrome")
    
    # Arguments to make the browser better for automation and less detectable.
    arguments = [
        "-no-first-run",
        "-force-color-profile=srgb",
        "-metrics-recording-only",
        "-password-store=basic",
        "-use-mock-keychain",
        "-export-tagged-pdf",
        "-no-default-browser-check",
        "-disable-background-mode",
        "-enable-features=NetworkService,NetworkServiceInProcess,LoadCryptoTokenExtension,PermuteTLSExtensions",
        "-disable-features=FlashDeprecationWarning,EnablePasswordsAccountStorage",
        "-deny-permission-prompts",
        "-disable-gpu",
        "-accept-lang=en-US",
    ]
    
    options = get_chromium_options(browser_path, arguments)

    # Initialize the browser
    driver = ChromiumPage(addr_or_opts=options)
    
    try:
        logging.info('Navigating to the provided URL.')
        driver.get(url)

        logging.info('Starting Cloudflare bypass.')
        cf_bypasser = CloudflareBypasser(driver)

        # Bypass the Cloudflare page
        cf_bypasser.bypass()

        logging.info("Bypass successful!")
        logging.info(f"Title of the page: {driver.title}")

        # Sleep to let the user see the result
        time.sleep(3)

        # Returning the final URL
        final_url = driver.current_url
        return jsonify({
            "message": "Cloudflare bypass successful!",
            "bypassed_url": final_url,
            "title": driver.title
        })

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        logging.info('Closing the browser.')
        driver.quit()
        if isHeadless:
            display.stop()

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=400)
