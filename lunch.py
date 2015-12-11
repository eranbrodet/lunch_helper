from db import DB


class FoodFinder(object):
    #TODO Eran consider canceling and moving the logic to the ui functions
    def __init__(self):
        self._db = DB()
        #TODO see why moving this to the find_food function fails
        self.restaurants = self._db.get_all_restaurants()
        self.nameGroups = [set(self._db.get_people_for_restaurant(x)) for x in self.restaurants]

    def get_all_people(self):
        return self._db.get_all_people()

    def get_all_restaurants(self):
        return self._db.get_all_restaurants()

    def find_food(self, peopleSet):
        final = []
        for i, nameGroup in enumerate(self.nameGroups):
            if peopleSet <= nameGroup:
                final.append(self.restaurants[i])
        return final

    def add_user(self, user):
        self._db.add_person(user)

    def add_restaurant(self, name):
        self._db.add_restaurant(name)

    def add_user_to_restaurants(self, user, restaurants_list):
        self._db.add_person_to_restaurants(user, restaurants_list)