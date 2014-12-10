__author__ = 'Federico Milano'

import sys


class Place:

    def __init__(self, x, y, dict_fingerprint):
        self.x = x
        self.y = y
        self.dict_fingerprint = dict_fingerprint

    def distance(self, dict_fingerprint):
        sum = 0.
        for mac in dict_fingerprint.keys():
            if self.dict_fingerprint.has_key(mac):
                sum += pow(dict_fingerprint[mac] - self.dict_fingerprint[mac], 2)
            else:
                # We get here when a network is sensed that was not sensed during the mapping of the room
                # Si la red ya estaba en la lista de redes, devolvemos un valor muy grande para que no se tome en cuenta
                # Si la red es nueva, podemos ignorarla.
                return sys.float_info.max

        return sum


class Location:

    def __init__(self):
        self.places = []

    def find_closest_place(self, dict_fingerprint):
        min_dist = sys.float_info.max
        closest_place = None

        for place in self.places:
            dist = place.distance(dict_fingerprint)
            if dist < min_dist:
                min_dist = dist
                closest_place = place

        return closest_place

    def add_place(self, place):
        self.places.append(place)



