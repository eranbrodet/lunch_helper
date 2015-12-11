# -*- coding: utf-8 -*-
import sqlite3
from itertools import chain

#TODO Add ui for adding stuff
#TODO delete excel


class DB(object):
    """Any function can throw sqlite3.OperationalError if database is locked for too long."""

    # temporary custom exception until error handling is well defined
    class DBException(Exception): pass

    def __init__(self):
        self.con = sqlite3 .connect('lunch.db')
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
        """Add a person to the restaurants in the given list.

        Throws DB.DBException if either the person name or one of the restaurant names is not found
        Thows sqlite3.IntegrityError if a mapping between person and one of the restaurants already exists
        """
        with self.con:
            question_marks = ", ".join("?" * len(restaurants_list))
            cur = self.con.execute("INSERT INTO person_to_restaurant(person_id, restaurant_id) "
                                    "SELECT person.id, restaurant.id FROM person, restaurant "
                                    "WHERE restaurant.name in (" + question_marks + ") AND person.name=?;",
                                    list(chain(restaurants_list, [person])))
            if cur.rowcount != len(restaurants_list):
                raise DB.DBException("Person (%s) or one or more restaurants (%s) don't exist" % (person, ', '.join(restaurants_list)))

    def add_restaurant(self, restaurant):
        """Throws sqlite3.IntegrityError if restaurant with that name already exists."""
        with self.con:
            self.con.execute("INSERT INTO restaurant(name) VALUES(?)", (restaurant,))

    def add_person(self, name):
        """Throws sqlite3.IntegrityError if person with that name already exists"""
        with self.con:
            self.con.execute("INSERT INTO person(name) VALUES(?)", (name,))

    def get_all_people(self):
        with self.con:
            return list(chain(*self.con.execute("SELECT name FROM person").fetchall()))

    def get_all_restaurants(self):
        with self.con:
            return list(chain(*self.con.execute("SELECT name FROM restaurant").fetchall()))
