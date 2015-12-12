from db import DB


class CrossReferencer(object):
    @staticmethod
    def find_restaurants(peopleSet):
        final = []
        db = DB()
        restaurants = db.get_all_restaurants()
        for restaurant in restaurants:
            restaurant_goers = set(db.get_people_for_restaurant(restaurant))
            if peopleSet <= restaurant_goers:
                final.append(restaurant)
        return final
