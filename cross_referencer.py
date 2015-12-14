from db import DB


class CrossReferencer(object):
    @staticmethod
    def find_restaurants(peopleSet):
        #TODO maybe loop the other way arounf (for each person get their restaurants
        db = DB() #TODO mayvbe should get it from outside
        restaurants = db.get_all_restaurants()
        if not peopleSet:
            return restaurants
        final = []
        for restaurant in restaurants:
            restaurant_goers = set(db.get_people_for_restaurant(restaurant))
            if peopleSet <= restaurant_goers:
                final.append(restaurant)
        return final
