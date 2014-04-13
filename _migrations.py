import os
import re
import time

from django.conf import settings
from django.db import connection

DB_TABLE = 'migrations'

migration_message_regex = re.compile(r'[^\w_]')
normalize_migration_filename_regex = re.compile(r'\.(up|down)\.sql$')
migrations_dir = os.path.join(settings.BASE_DIR, 'migrations')


def get_normalized_migration_name(migration_name):
    return normalize_migration_filename_regex.sub('', migration_name)


def get_applied_migrations():
    # let's get applied migrations
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM {}".format(DB_TABLE))
    applied_migrations = [get_normalized_migration_name(_res[0]) for _res in cursor.fetchall()]
    return applied_migrations


def get_content_for_up_migrations(applied_migrations):
    filenames = [filename for filename in os.listdir(migrations_dir) if filename.endswith('.up.sql')]
    files_content = {}
    for filename in filenames:
        if get_normalized_migration_name(filename) in applied_migrations:
            continue
        with file('{}/{}'.format(migrations_dir, filename)) as f:
            files_content[filename] = re.sub(r"\n", "", f.read())
    return files_content


def get_content_for_down_migrations(to, applied_migrations):
    filenames = reversed([filename for filename in os.listdir(migrations_dir) if filename.endswith('.down.sql')])
    files_content = {}
    for filename in filenames:
        normalized_migration_name = get_normalized_migration_name(filename)
        if normalized_migration_name not in applied_migrations:
            continue
        with file('{}/{}'.format(migrations_dir, filename)) as f:
            files_content[filename] = re.sub(r"\n", "", f.read())
        if to == normalized_migration_name:
            break
    return files_content


def insert_applied_migration(migration_name):
    cursor = connection.cursor()
    cursor.execute('INSERT INTO {} (name) VALUES (%s)'.format(DB_TABLE), [migration_name])


def delete_applied_migration(migration_name):
    cursor = connection.cursor()
    cursor.execute("DELETE FROM {} WHERE name = %s".format(DB_TABLE), [migration_name])


class Migrations(object):

    @staticmethod
    def apply(to=None, **kwargs):
        if to:
            Migrations.down_to(to)
        else:
            Migrations.apply_all()

    @staticmethod
    def down_to(to):
        applied_migrations = get_applied_migrations()
        migrations_to_down = get_content_for_down_migrations(to, applied_migrations)
        cursor = connection.cursor()
        for migration_name, migration in migrations_to_down.iteritems():
            cursor.execute(migration)
            delete_applied_migration(get_normalized_migration_name(migration_name))
            print "Downgraded migration {}".format(migration_name)

    @staticmethod
    def apply_all():
        applied_migrations = get_applied_migrations()
        migrations_to_apply = get_content_for_up_migrations(applied_migrations)
        cursor = connection.cursor()
        for migration_name, migration in migrations_to_apply.iteritems():
            cursor.execute(migration)
            insert_applied_migration(get_normalized_migration_name(migration_name))
            print "Applied migration {}".format(migration_name)

    @staticmethod
    def create(m=None, **kwargs):
        m_for_file = migration_message_regex.sub('', m)
        file_name = '{}_{}'.format(int(time.time()), m_for_file)
        file_up_name = '{}/{}.up.sql'.format(migrations_dir, file_name)
        file_down_name = '{}/{}.down.sql'.format(migrations_dir, file_name)
        message = "/*\n{}\n*/".format(re.sub(r'_', ' ', m))
        with open(file_up_name, 'w') as file_up, open(file_down_name, 'w') as file_down:
            file_up.write(message)
            file_down.write(message)

        print "Migrations files created:"
        print file_up_name
        print file_down_name
