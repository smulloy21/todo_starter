from contextlib import contextmanager
import logging
import os

from psycopg2 import connect
from psycopg2.extras import DictCursor


LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


class DatabasePersistence():
    def __init__(self):
        self._setup_schema()

    @contextmanager
    def _database_connect(self):
        if os.environ.get('FLASK_ENV') == 'production':
            connection = connect(os.environ['DATABASE_URL'])
        else:
            connection = connect(dbname="todos")

        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _setup_schema(self):
        with self._database_connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'lists';
                """)
                if cursor.fetchone()[0] == 0:
                    cursor.execute("""
                        CREATE TABLE lists (
                            id serial PRIMARY KEY,
                            title text NOT NULL UNIQUE
                        );
                    """)

                cursor.execute("""
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'todos';
                """)
                if cursor.fetchone()[0] == 0:
                    cursor.execute("""
                        CREATE TABLE todos (
                            id serial PRIMARY KEY,
                            title text NOT NULL,
                            completed boolean NOT NULL DEFAULT false,
                            list_id integer NOT NULL
                                            REFERENCES lists (id)
                                            ON DELETE CASCADE
                        );
                    """)

    def all_lists(self):
        query = """
            SELECT lists.*,
                    COUNT(todos.id) AS todos_count,
                    COUNT(NULLIF(todos.completed, False)) AS todos_completed
            FROM lists
            LEFT JOIN todos ON todos.list_id = lists.id
            GROUP BY lists.id
            ORDER BY lists.title
        """
        logger.info("Executing query: %s", query)
        with self._database_connect() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query)
                results = cursor.fetchall()

        lists = [dict(result) for result in results]
        return lists

    def create_new_list(self, title):
        query = "INSERT INTO lists (title) VALUES (%s)"
        logger.info("Executing query: %s with title: %s", query, title)
        with self._database_connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (title,))

    def delete_list(self, list_id):
        query = "DELETE FROM lists WHERE id = %s"
        logger.info("Executing query: %s with list_id: %s", query, list_id)
        with self._database_connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (list_id,))

    def find_list(self, list_id):
        query = """
            SELECT lists.*,
                    COUNT(todos.id) AS todos_count,
                    COUNT(NULLIF(todos.completed, False)) AS todos_completed
            FROM lists
            LEFT JOIN todos ON todos.list_id = lists.id
            WHERE lists.id = %s
            GROUP BY lists.id
            ORDER BY lists.title;
        """
        logger.info("Executing query: %s with list_id: %s", query, list_id)
        with self._database_connect() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, (list_id,))
                lst = dict(cursor.fetchone())

        todos = self.find_todos_for_list(list_id)
        lst.setdefault('todos', todos)
        return lst

    def find_todos_for_list(self, list_id):
        query = "SELECT * from todos WHERE list_id = %s"
        logger.info("Executing query: %s with list_id: %s", query, list_id)
        with self._database_connect() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, (list_id,))
                return cursor.fetchall()

    def update_list_by_id(self, list_id, updated_title):
        query = "UPDATE lists SET title = %s WHERE id = %s"
        logger.info("Executing query: %s with title %s and list_id: %s",
                    query, updated_title, list_id)
        with self._database_connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (updated_title, list_id,))

    def create_new_todo(self, list_id, todo_title):
        query = "INSERT INTO todos (title, list_id) VALUES (%s, %s)"
        logger.info("Executing query: %s with title: %s and list_id: %s",
                    query, todo_title, list_id)
        with self._database_connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (todo_title, list_id,))

    def delete_todo(self, list_id, todo_id):
        query = "DELETE FROM todos WHERE list_id = %s AND id = %s"
        logger.info("Executing query: %s with list_id: %s and id: %s",
                    query, list_id, todo_id)
        with self._database_connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (list_id, todo_id,))

    def mark_all_todos_completed(self, list_id):
        query = "UPDATE todos SET completed = TRUE WHERE list_id = %s"
        logger.info("Executing query: %s with list_id %s", query, list_id)
        with self._database_connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (list_id,))

    def update_todo_status(self, list_id, todo_id, status):
        query = """
            UPDATE todos SET completed = %s
            WHERE list_id = %s AND id = %s
        """
        logger.info("Executing query: %s with completed: %s, "
                    "list_id: %s and id: %s",
                    query, status, list_id, todo_id)
        with self._database_connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (status, list_id, todo_id,))
