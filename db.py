# -*- coding: utf-8 -*-
import sqlite3
from itertools import chain
from os.path import exists
import json

class DB(object):
    """
        Any function can throw sqlite3.OperationalError if database is locked for too long.
    """

    # Indicates the version of the scheme the program currently uses.
    # Must be incremented every time the DB scheme is changed and the
    # appropriate upgrade function must be added to _upgrade_functions
    CURRENT_DB_SCHEME_VERSION = 0
    SETTINGS_FILENAME = 'settings.json'
    DB_FILENAME = 'lunch.db'

    _upgrade_functions = {
        #example:
        # 0 : upgrade_to_version_1
        # where upgrade_to_version_1 must take only the connection as a parameter
        }

    class DBException(Exception): pass # Temporary custom exception until error handling is well defined

    def __init__(self):
        db_exists = exists(DB.SETTINGS_FILENAME) and exists(DB.DB_FILENAME)

        self.con = sqlite3.connect(DB.DB_FILENAME)
        db_changed = False
        if not db_exists:
            self._create_empty_db()
            db_changed = True
        else:
            db_changed = self._upgrade_db()

        if db_changed:
            self._write_settings()

    # NOTE: if settings ever contain more stuff we might want to move it out of DB and closer to __main__
    def _write_settings(self):
        settings = json.dumps({'settings_version': 0, 'db_scheme_version': DB.CURRENT_DB_SCHEME_VERSION})
        with open(DB.SETTINGS_FILENAME, 'w') as f:
            f.write(settings)


    def _create_empty_db(self):
        print 'Create empty DB' #TODO: use logger
        with self.con:
            self.con.execute("""PRAGMA foreign_keys = ON;""")
            cur = self.con.cursor()
            with open("db.scheme") as f:
                cur.executescript(f.read())

    def _upgrade_db(self):
        with open(DB.SETTINGS_FILENAME) as f:
            settings = json.loads(f.read())
        if settings['db_scheme_version'] == DB.CURRENT_DB_SCHEME_VERSION:
            return False #no upgrade occurred

        #TODO: do we want to copy the DB before doing this? would help with debugging
        for upgrade_step in range(settings['db_scheme_version'], DB.CURRENT_DB_SCHEME_VERSION):
            print 'Upgrade DB from version %d to version %d' % (upgrade_step, upgrade_step + 1) #TODO: use logger
            _upgrade_functions[upgrade_step](self.conn)
        return True # we did actually upgrade


    def get_restaurants_for_person(self, person):
        with self.con:
            cur = self.con.execute("SELECT restaurant.name FROM restaurant "
                                   "JOIN person_to_restaurant ON restaurant.id = person_to_restaurant.restaurant_id "
                                   "JOIN person on person.id = person_to_restaurant.person_id "
                                   "WHERE person.name=?;", (person,))
            names = cur.fetchall()
        return list(chain(*names))

    def get_people_for_restaurant(self, restaurant):
        with self.con:
            cur = self.con.execute("SELECT person.name FROM restaurant "
                                   "JOIN person_to_restaurant ON restaurant.id = person_to_restaurant.restaurant_id "
                                   "JOIN person on person.id = person_to_restaurant.person_id "
                                   "WHERE restaurant.name=?;", (restaurant,))
            names = cur.fetchall()
        return list(chain(*names))

    def add_person_to_restaurants(self, person, restaurants_list):
        """
            Add a person to the restaurants in the given list.

            Throws DB.DBException if either the person name or one of the restaurant names is not found
            Thows sqlite3.IntegrityError if a mapping between person and one of the restaurants already exists
        """
        with self.con:
            question_marks = ", ".join("?" * len(restaurants_list))
            sql = "INSERT INTO person_to_restaurant(person_id, restaurant_id) " \
                                    "SELECT person.id, restaurant.id FROM person, restaurant " \
                                    "WHERE restaurant.name in (" + question_marks + ") AND person.name=?;"
            cur = self.con.execute(sql, list(chain(restaurants_list, [person])))
            if cur.rowcount != len(restaurants_list):
                print sql
                raise DB.DBException("Person (%s) or one or more restaurants (%s) don't exist" % (person, ', '.join(restaurants_list)))

    def change_person_name(self, old_name, new_name):
        with self.con:
            cur = self.con.execute("UPDATE person set name=? WHERE name=?", (new_name, old_name))
            if cur.rowcount != 1:
                raise DB.DBException("Person (%s) not found" % (old_name,))

    def update_restaurant(self, old_restaurant_name, new_restaurant_name, new_restaurant_comment):
        with self.con:
            cur = self.con.execute("UPDATE restaurant set name=?, comment=? WHERE name=?", (new_restaurant_name, new_restaurant_comment, old_restaurant_name))
            if cur.rowcount != 1:
                raise DB.DBException("Restaurant (%s) not found" % (old_restaurant_name,))

    def delete_all_restaurants_from_user(self, user_name):
        with self.con:
            self.con.execute("DELETE FROM person_to_restaurant WHERE person_id=(select id from person where name=?)", (user_name,))

    def add_restaurant(self, restaurant_name, restaurant_comment):
        """
            Throws sqlite3.IntegrityError if restaurant with that name already exists.
        """
        with self.con:
            self.con.execute("INSERT INTO restaurant(name, comment) VALUES(?, ?)", (restaurant_name,restaurant_comment))

    def get_restaurant_comment(self, restaurant_name):
        with self.con:
            comments = list(chain(*self.con.execute("SELECT comment FROM restaurant WHERE name=?", (restaurant_name,)).fetchall()))
            if len(comments) != 1:
                raise DB.DBException("Restaurant (%s) not found" % (restaurant_name,))
            return comments[0]

    def add_person(self, name):
        """
            Throws sqlite3.IntegrityError if person with that name already exists
        """
        with self.con:
            self.con.execute("INSERT INTO person(name) VALUES(?)", (name,))

    def get_all_people(self):
        with self.con:
            return list(chain(*self.con.execute("SELECT name FROM person ORDER BY name ASC").fetchall()))

    def get_all_restaurants(self):
        with self.con:
            return list(chain(*self.con.execute("SELECT name FROM restaurant ORDER BY name ASC").fetchall()))

    def delete_restaurant(self, name):
        with self.con:
            cur = self.con.execute("DELETE FROM restaurant WHERE name=?", (name,))
            if cur.rowcount != 1:
                raise DB.DBException("Restaurant %s is not in database" % (name,))

    def delete_person(self, name):
        with self.con:
            cur = self.con.execute("DELETE FROM person WHERE name=?", (name,))
            if cur.rowcount != 1:
                raise DB.DBException("Person %s is not in database" % (name,))

    def get_extramum_restaurant(self, minimum):
        with self.con:
            cur = self.con.execute("SELECT name, result FROM restaurant "
                                   "LEFT OUTER JOIN (SELECT restaurant_id, COUNT(*) AS result "
                                   "FROM person_to_restaurant "
                                   "GROUP BY restaurant_id) "
                                   "ON restaurant_id=restaurant.id "
                                   "ORDER BY result %s LIMIT 1" % ('ASC' if minimum else 'DESC',))
            res = cur.fetchone()
            if not res:
                raise DB.DBException("Can't fetch data")
            return res[0], res[1] if res[1] else 0


    def get_extramum_person(self, minimum):
        with self.con:
            cur = self.con.execute("SELECT name, result FROM person "
                                   "LEFT OUTER JOIN (SELECT person_id, COUNT(*) AS result "
                                   "FROM person_to_restaurant "
                                   "GROUP BY person_id) "
                                   "ON person_id=person.id "
                                   "ORDER BY result %s LIMIT 1" % ('ASC' if minimum else 'DESC',))
            res = cur.fetchone()
            if not res:
                raise DB.DBException("Can't fetch data")
            return res[0], res[1] if res[1] else 0
