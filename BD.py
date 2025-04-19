import sqlite3 as sq
import configparser

from botocore.response import StreamingBody
from face_recognition import compare_faces_bool, has_face_on_image
import io
import pandas as pd

from s3_service import s3_bucket_service_factory

config_for_minio = configparser.ConfigParser()
config_for_minio.read('default.ini')


class BD:
    def __init__(
        self,
        database_name: str,
    ) -> None:
        self.database_name = database_name
        self.s3 = s3_bucket_service_factory(config_for_minio)
        self.prefix = "users"

        # Создаем таблицу Users, если не существует
        connection = sq.connect(self.database_name)
        connection.cursor().execute('''
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            count_recognitions INTEGER NOT NULL,
            file_name TEXT NOT NULL
        )
        ''')
        connection.commit()
        connection.close()

    def add_user(
        self,
        username: str,
        source_file_name: str,
        content: bytes,
    ) -> list[str] | None:
        users_in_bd = self.user_recognize(content)
        if len(users_in_bd) != 0:
            return users_in_bd
        if not has_face_on_image(io.BytesIO(content)):
            return None
        connection = sq.connect(self.database_name)
        connection.cursor().execute('INSERT INTO Users (username, count_recognitions, file_name) VALUES (?, ?, ?)',
                       (username, 0, username + "/" + source_file_name))
        connection.commit()
        connection.close()
        self.s3.upload_file_object(self.prefix, username + "/" + source_file_name, content)
        return []

    def is_user_in_photo(
            self,
            user_photo: io.IOBase,
            photo_from_bd: io.IOBase
    ) -> bool :
        return compare_faces_bool(user_photo, photo_from_bd)

    def user_recognize(
        self,
        content: bytes,
    ) -> [str]:
        connection = sq.connect(self.database_name)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Users")
        users = cursor.fetchall()
        # TODO тут надо возвращать список пользователей
        recognized_users = []
        for user in users:
            user_photo = self.s3.get_file_object(self.prefix, user[3])
            if self.is_user_in_photo(io.BytesIO(content), user_photo):
                self.user_counter_increment(user[0])
                recognized_users.append(user[1])

        connection.close()
        return recognized_users

    def user_counter_increment(self, id: int) -> None:
        connection = sq.connect(self.database_name)
        connection.cursor().execute("UPDATE Users SET count_recognitions = count_recognitions + 1 WHERE id = ?", (id, ))
        connection.commit()
        connection.close()

    def form_bd(self) -> None:
        connection = sq.connect(self.database_name)
        cursor = connection.cursor()
        cursor.execute("SELECT username, count_recognitions FROM Users")
        user_data = cursor.fetchall()
        connection.close()
        data = pd.DataFrame(user_data)
        data.to_csv('bd.txt', index=False, header = ["Имя пользователя", "Количество распознаваний"])

