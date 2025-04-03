import threading
import schedule
import time


# ========= Фоновый процесс планировщика =========
def schedule_jobs():
    while True:
        schedule.run_pending()
        time.sleep(20)

def start_scheduler_thread():
    thread = threading.Thread(target=schedule_jobs)
    thread.daemon = True
    thread.start()