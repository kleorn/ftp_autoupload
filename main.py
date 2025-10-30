import os
import time
import traceback
from datetime import datetime
from dotenv import load_dotenv
import paramiko

def log(message: str) -> None:
    """Печатает сообщение с текущим временем."""
    print(f"{datetime.now().strftime('%H:%M:%S')} {message}")

def sftp_sync_dir(sftp: paramiko.SFTPClient, local_dir: str, remote_dir: str) -> None:
    """Рекурсивно синхронизирует локальную папку с удалённой (загрузка + удаление лишнего)."""
    try:
        sftp.chdir(remote_dir)
    except IOError:
        sftp.mkdir(remote_dir)
        sftp.chdir(remote_dir)

    # Получаем списки файлов/папок
    local_items = set(os.listdir(local_dir))
    try:
        remote_items = {f.filename for f in sftp.listdir_attr(remote_dir)}
    except IOError:
        remote_items = set()

    # Удаляем те, которых нет локально
    for remote_item in remote_items:
        if remote_item not in local_items:
            remote_path = os.path.join(remote_dir, remote_item).replace("\\", "/")
            try:
                # Проверим, папка это или файл
                try:
                    sftp.listdir(remote_path)
                    delete_remote_folder(sftp, remote_path)
                    log(f"Удалена папка на сервере: {remote_path}")
                except IOError:
                    sftp.remove(remote_path)
                    log(f"Удален файл на сервере: {remote_path}")
            except Exception as e:
                log(f"Не удалось удалить {remote_item}: {e}")

    # Загружаем или обновляем файлы
    for item in local_items:
        local_path = os.path.join(local_dir, item)
        remote_path = os.path.join(remote_dir, item).replace("\\", "/")

        if os.path.isdir(local_path):
            try:
                sftp.stat(remote_path)
            except FileNotFoundError:
                sftp.mkdir(remote_path)
            sftp_sync_dir(sftp, local_path, remote_path)
        else:
            sftp.put(local_path, remote_path)
            try:
                sftp.chmod(remote_path, 0o777)
            except Exception:
                log(f"Не удается установить права доступа для {remote_path}")

def delete_remote_folder(sftp: paramiko.SFTPClient, remote_path: str) -> None:
    """Рекурсивно удаляет папку на SFTP-сервере."""
    try:
        for entry in sftp.listdir_attr(remote_path):
            entry_path = os.path.join(remote_path, entry.filename).replace("\\", "/")
            try:
                sftp.listdir(entry_path)
                delete_remote_folder(sftp, entry_path)
            except IOError:
                sftp.remove(entry_path)
        sftp.rmdir(remote_path)
    except Exception as e:
        log(f"Ошибка при удалении папки {remote_path}: {e}")

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

            sftp_sync_dir(sftp, LOCAL_FOLDER, SFTP_SERVER_FOLDER_PATH)

            sftp.close()
            transport.close()
            log("Копирование успешно завершено")
        except Exception as e:
            log(f"Ошибка: {e}")
            traceback.print_exc()
        time.sleep(PERIOD_SEC)

if __name__ == "__main__":
    main()