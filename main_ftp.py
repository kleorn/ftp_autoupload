import ftplib
import os
import time
import traceback
from datetime import datetime
from dotenv import load_dotenv

def log(message: str) -> None:
    """Печатает сообщение с текущим временем."""
    print(f"{datetime.now().strftime('%H:%M:%S')} {message}")

def upload_folder(ftp: ftplib.FTP, local_folder: str, remote_folder: str) -> None:
    """Рекурсивно загружает содержимое локальной папки на FTP."""
    try:
        ftp.cwd(remote_folder)
    except ftplib.error_perm:
        # Создаем директорию, если её нет
        ftp.mkd(remote_folder)
        ftp.cwd(remote_folder)

    for item in os.listdir(local_folder):
        local_path = os.path.join(local_folder, item)
        if os.path.isdir(local_path):
            try:
                ftp.mkd(item)
            except ftplib.error_perm:
                pass  # Папка уже существует
            ftp.cwd(item)
            upload_folder(ftp, local_path, ".")
            ftp.cwd("..")
        else:
            with open(local_path, "rb") as f:
                ftp.storbinary(f"STOR {item}", f)
            try:
                ftp.sendcmd(f"SITE CHMOD 777 {item}")
            except Exception:
                log(f"Не удается установить права доступа к скопированным файлам")
                pass  # Некоторые FTP не поддерживают CHMOD

def main():
    load_dotenv()
    FTP_SERVER = os.getenv("FTP_SERVER")
    FTP_USER = os.getenv("FTP_USER")
    FTP_PASSWORD = os.getenv("FTP_PASSWORD")
    FTP_SERVER_FOLDER_PATH = os.getenv("FTP_SERVER_FOLDER_PATH")
    LOCAL_FOLDER = os.getenv("LOCAL_FOLDER")
    PERIOD_SEC = int(os.getenv("PERIOD_SEC", "60"))

    if not all([FTP_SERVER, FTP_USER, FTP_PASSWORD, LOCAL_FOLDER, FTP_SERVER_FOLDER_PATH]):
        log("Ошибка: не все параметры заданы в .env")
        return

    while True:
        try:
            log("Запущено копирование")
            with ftplib.FTP(FTP_SERVER) as ftp:
                ftp.login(FTP_USER, FTP_PASSWORD)
                upload_folder(ftp, LOCAL_FOLDER, FTP_SERVER_FOLDER_PATH)
            log("Копирование успешно завершено")
        except Exception as e:
            log(f"Ошибка: {e}")
            traceback.print_exc()
        time.sleep(PERIOD_SEC)



if __name__ == '__main__':
    main()
