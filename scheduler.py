import requests
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# Cấu hình logging để thấy output
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')

# Lịch trình: Chạy mỗi 14 phút, từ 7h đến 23h (giờ server)
# Lưu ý: Múi giờ sẽ phụ thuộc vào cấu hình của server
SCHEDULE = CronTrigger(minute='*/14', hour='7-23')

def ping_service(url):
    """Gửi một GET request đến URL được chỉ định."""
    if not url:
        logging.warning("[SCHEDULER] PING_URL is not set. Skipping ping.")
        return

    try:
        response = requests.get(url, timeout=10) # Đặt timeout 10 giây
        if response.status_code == 200:
            logging.info(f"[SCHEDULER] Keep-alive ping to {url} OK (Status: {response.status_code})")
        else:
            logging.warning(f"[SCHEDULER] Keep-alive ping to {url} FAILED (Status: {response.status_code})")
    except requests.exceptions.RequestException as e:
        logging.error(f"[SCHEDULER] Error while sending ping request to {url}: {e}")

def start_keep_alive_job(ping_url):
    """Khởi tạo và bắt đầu cron job."""
    if not ping_url:
        logging.warning("[SCHEDULER] No PING_URL provided, keep-alive job will not start.")
        return None

    scheduler = BackgroundScheduler(timezone='Asia/Ho_Chi_Minh') # Đặt múi giờ Việt Nam
    
    # Thêm tác vụ vào scheduler
    scheduler.add_job(
        ping_service,
        trigger=SCHEDULE,
        args=[ping_url],
        id='keep_alive_ping_job',
        name='Ping service to prevent sleep',
        replace_existing=True
    )
    
    try:
        scheduler.start()
        logging.info(f"[SCHEDULER] Keep-alive job started. Pinging {ping_url} every 14 minutes from 7am to 11pm (Asia/Ho_Chi_Minh).")
        return scheduler
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logging.info("[SCHEDULER] Keep-alive job shut down.")
        
    return None