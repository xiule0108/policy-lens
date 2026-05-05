import os
import signal
import time


RUNNING = True


def _stop_worker(signum: int, frame: object) -> None:
    global RUNNING
    RUNNING = False


def main() -> None:
    signal.signal(signal.SIGTERM, _stop_worker)
    signal.signal(signal.SIGINT, _stop_worker)

    storage_dir = os.getenv("STORAGE_DIR", "./storage")
    print(f"PolicyLens worker skeleton started. storage_dir={storage_dir}", flush=True)
    while RUNNING:
        time.sleep(10)
    print("PolicyLens worker skeleton stopped.", flush=True)


if __name__ == "__main__":
    main()
