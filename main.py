import os
import time
import traceback
from datetime import datetime
from dotenv import load_dotenv
import paramiko

def log(message: str) -> None:
    """Печатает сообщение с текущим временем."""
    print(f"{datetime.now().strftime('%H:%M:%S')} {message}")

def sftp_upload_dir(sftp: paramiko.SFTPClient, local_dir: str, remote_dir: str) -> None:
    """Рекурсивно копирует локальную папку на SFTP-сервер."""
    try:
        sftp.chdir(remote_dir)
    except IOError:
        sftp.mkdir(remote_dir)
        sftp.chdir(remote_dir)

    for item in os.listdir(local_dir):
        local_path = os.path.join(local_dir, item)
        remote_path = os.path.join(remote_dir, item)
        if os.path.isdir(local_path):
            try:
                sftp.stat(remote_path)
            except FileNotFoundError:
                sftp.mkdir(remote_path)
            sftp_upload_dir(sftp, local_path, remote_path)
        else:
            sftp.put(local_path, remote_path)
            try:
                sftp.chmod(remote_path, 0o777)
            except Exception:
                pass  # Некоторые сервера могут не позволять смену прав
def main():
    load_dotenv()
    SFTP_SERVER = os.getenv("SFTP_SERVER")
    SFTP_PORT = int(os.getenv("SFTP_PORT", "22"))
    SFTP_USER = os.getenv("SFTP_USER")
    SFTP_PASSWORD = os.getenv("SFTP_PASSWORD")
    SFTP_SERVER_FOLDER_PATH = os.getenv("SFTP_SERVER_FOLDER_PATH")
    LOCAL_FOLDER = os.getenv("LOCAL_FOLDER")
    PERIOD_SEC = int(os.getenv("PERIOD_SEC", "60"))

    if not all([SFTP_SERVER, SFTP_USER, SFTP_PASSWORD, SFTP_SERVER_FOLDER_PATH, LOCAL_FOLDER]):
        log("Ошибка: не все параметры заданы в .env")
        return

    while True:
        try:
            log("Запущено копирование")
            transport = paramiko.Transport((SFTP_SERVER, SFTP_PORT))
            transport.connect(username=SFTP_USER, password=SFTP_PASSWORD)
            sftp = paramiko.SFTPClient.from_transport(transport)

            sftp_upload_dir(sftp, LOCAL_FOLDER, SFTP_SERVER_FOLDER_PATH)

            sftp.close()
            transport.close()
            log("Копирование успешно завершено")
        except Exception as e:
            log(f"Ошибка: {e}")
            traceback.print_exc()
        time.sleep(PERIOD_SEC)


if __name__ == "__main__":
    main()