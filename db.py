# -*- coding: utf-8 -*-
import sqlite3
from itertools import chain


class DB(object):
    """
        Any function can throw sqlite3.OperationalError if database is locked for too long.
    """

    class DBException(Exception): pass # Temporary custom exception until error handling is well defined

    def __init__(self):
        self.con = sqlite3.connect('lunch.db')
        with self.con:
            self.con.execute("""PRAGMA foreign_keys = ON;""")
            cur = self.con.cursor()
            with open("db.scheme") as f:
                cur.executescript(f.read())

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

    def change_restaurant_name(self, old_restaurant_name, new_restaurant_name):
        with self.con:
            cur = self.con.execute("UPDATE restaurant set name=? WHERE name=?", (new_restaurant_name, old_restaurant_name))
            if cur.rowcount != 1:
                raise DB.DBException("Restaurant (%s) not found" % (old_restaurant_name,))

    def delete_all_restaurants_from_user(self, user_name):
        with self.con:
            self.con.execute("DELETE FROM person_to_restaurant WHERE person_id=(select id from person where name=?)", (user_name,))

    def add_restaurant(self, restaurant):
        """
            Throws sqlite3.IntegrityError if restaurant with that name already exists.
        """
        with self.con:
            self.con.execute("INSERT INTO restaurant(name) VALUES(?)", (restaurant,))

    def add_person(self, name):
        """
            Throws sqlite3.IntegrityError if person with that name already exists
        """
        with self.con:
            self.con.execute("INSERT INTO person(name) VALUES(?)", (name,))

    def get_all_people(self):
        with self.con:
            return list(chain(*self.con.execute("SELECT name FROM person").fetchall()))

    def get_all_restaurants(self):
        with self.con:
            return list(chain(*self.con.execute("SELECT name FROM restaurant").fetchall()))

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
