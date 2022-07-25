# Initially I came up with a solution with hard-coded logic for vehicles to
# prioritize certain zones to park in. Then I realized that it would be possible
# to create an abstraction where `vehicles` are of a certain "size" or "weight"
# and are able to fit into `spots` of a certain "size" within zones.

# To allow for vans to fit into three regular spots, a zone has a property that
# allows for vehicles of greater size than a single spot to be fit into adjacent spots.

# In the other direction, it would be possible to create a function for fitting
# multiple vehicles into a single spot.

import bisect
from collections import defaultdict
from enum import Enum
import logging
import math
from typing import List
import uuid


class ZoneType(Enum):
    CYCLE = "motorcycle"
    COMPACT = "compact"
    REGULAR = "regular"
    LARGE = "large"


class Zone:
    """
    Each `zone` has a `type`, parking spot `size`, and a `number of spots`.
    A `Lot` may have multiple `zones` of the same `type`.

    `Zones` must be created before creating a `Lot`.
    """
    def __init__(self, type_: ZoneType, size: float, num_spots: int, adjacent=False):
        self.type_ = type_
        self.size = size
        self.adjacent = adjacent  # if vehicle bigger than zone spot size, use adjacent spots to fit
        self.spots = [None for _ in range(num_spots)]  # contains None or Vehicle
        self.free = [x for x in range(num_spots)]  # list of free spots
        logging.debug(f"New zone: {vars(self)}")


class VehicleType(Enum):
    CYCLE = "motorcycle"
    CAR = "car"
    VAN = "van"


class Vehicle:
    """
    A `vehicle` has an `id`, `type`, `size`, zone parking `priority`, and `location`.
    """
    def __init__(self, type_: VehicleType):
        self.id_ = str(uuid.uuid4())  # used to lookup vehicles within the parking lot
        self.type_ = type_
        self.location: tuple[ZoneType, int, List[int]] = tuple()  # zone, zone_index, list of spot_index
        self.size = -1.0
        self.priority = []

        match type_:
            case VehicleType.CYCLE:
                self.size = 0.3
                self.priority = [ZoneType.CYCLE, ZoneType.COMPACT, ZoneType.REGULAR, ZoneType.LARGE]
                logging.debug(f"Created {type_}")
            case VehicleType.CAR:
                self.size = 0.8
                self.priority = [ZoneType.COMPACT, ZoneType.REGULAR, ZoneType.LARGE]
                logging.debug(f"Created {type_}")
            case VehicleType.VAN:
                self.size = 3.0
                self.priority = [ZoneType.LARGE, ZoneType.REGULAR]
                logging.debug(f"Created {type_}")
            case _:
                logging.error(f"New vehicle type not yet handled.")
        logging.debug(f"New vehicle: {vars(self)}")

# I initially extended the vehicle class as below, but it was more cumbersome to use.
# ie: While extending the class is more explicit, a vehicle has a `type` and
# when using the different types of vehicles, more code is required for each new vehicle in some cases.
#
# class Motorcycle(Vehicle):
#     def __init__(self):
#         super(self.__class__, self)\
#             .__init__(type_=VehicleType.CYCLE,
#                       size=0.3,
#                       priority=[ZoneType.CYCLE, ZoneType.COMPACT, ZoneType.REGULAR, ZoneType.LARGE])
#
#
# class Car(Vehicle):
#     def __init__(self):
#         super(self.__class__, self) \
#             .__init__(type_=VehicleType.CAR,
#                       size=0.8,
#                       priority=[ZoneType.COMPACT, ZoneType.REGULAR, ZoneType.LARGE])
#
#
# class Van(Vehicle):
#     def __init__(self):
#         super(self.__class__, self) \
#             .__init__(type_=VehicleType.VAN,
#                       size=3.0,
#                       priority=[ZoneType.LARGE, ZoneType.REGULAR])


class Lot:
    """
    A parking `lot` has multiple `zones`, organized by `type`.
    For each `type`, there is a list of zones.

    Multiple `zones` per `type` allows the constructor to be passed a list of any `type` of `zone`,
    and overall makes for a better abstraction.

    A `lot` also keeps track of `vehicle` objects currently parked
    as well as an overall count of each `type` of `vehicle`.
    """
    def __init__(self, zones: List[Zone]):
        self.zones: defaultdict[str, List[Zone]] = defaultdict(list)
        for zone in zones:
            self.zones[zone.type_.name].append(zone)
            logging.debug(f"Zone {zone.type_.name} added: {vars(zone)}")
        logging.debug(f"Zones: {self.zones}")

        # Count of each VehicleType
        self.count = defaultdict(int)  # key: VehicleType, value: total number of vehicles in lot

        # Vehicles currently parked
        self.vehicles = defaultdict(Vehicle)

    # Status functions
    def zone_spots_string(self, zone: Zone) -> str:
        spots = ""
        for vehicle in zone.spots:
            if vehicle is None:
                spots += "O"
            else:
                vehicle_type = getattr(vehicle, 'type_')
                match vehicle_type:
                    case VehicleType.CYCLE:
                        spots += "M"
                    case VehicleType.CAR:
                        spots += "C"
                    case VehicleType.VAN:
                        spots += "V"
        return spots

    def print_all_zones(self):
        for zone_type in self.zones:
            for (zone_index, zone) in enumerate(self.zones[zone_type]):
                zone_header = f"{zone_type} {zone_index}"
                whitespace_to_append = 10 - len(zone_header)
                zone_header += " " * whitespace_to_append
                print(f"{zone_header} | {self.zone_spots_string(zone)}")

    # Lot availability functions
    def vehicle_availability(self, type_: VehicleType) -> int:
        vehicle = Vehicle(type_=type_)
        num_spots = 0
        match type_:
            case VehicleType.CYCLE | VehicleType.CAR:
                # Check each zone types in vehicle priority list
                for zone_type in vehicle.priority:
                    # Count number of free spots in each zone of type
                    for (zone_index, zone) in enumerate(self.zones[zone_type.name]):
                        num_spots += len(zone.free)
            case VehicleType.VAN:
                # Count spots in all large zones
                large_zones = self.zones[ZoneType.LARGE.name]
                for zone in large_zones:
                    num_spots += len(zone.free)
                # Count adjacent spots of appropriate size in all regular zones
                regular_zones = self.zones[ZoneType.REGULAR.name]
                num_spots_for_van_in_regular = math.ceil(vehicle.size / regular_zones[0].size)
                for zone in regular_zones:
                    num_spots += len(self.find_adjacent_free_spots(free=zone.free, num_spots=num_spots_for_van_in_regular))
            case _:
                logging.warning(f"Vehicle availability for {type_.name} not handled.")

        return num_spots

    # Lot occupancy functions
    def num_parked_vehicle(self, type_: VehicleType) -> int:
        """
        A helper function to get the count of parked vehicles of valid types.

        :return: The count of parked vehicles of a certain type.
        """
        # Check if vehicle exists, there may be none of this type yet
        if type_.name in self.count:
            num_vehicles = self.count[type_.name]
        else:
            num_vehicles = 0

        logging.debug(f"Number of {type_.name}: {num_vehicles}")
        return num_vehicles

    # Add vehicle helper functions
    def park_single(self, zone: Zone, zone_index: int, vehicle: Vehicle):
        # We know there is at least one spot, take the first one and remove from free list
        spot_index = zone.free.pop(0)

        # Set vehicle at spot
        zone.spots[spot_index] = vehicle

        # Set vehicle location
        vehicle.location = (zone.type_, zone_index, [spot_index])

        # Keep track of the number of vehicles
        self.count[vehicle.type_.name] += 1

        logging.debug(f"Parked vehicles: {self.count}")
        logging.debug(f"Parking {vehicle} at spot index {spot_index}")
        logging.debug(f"Remaining spots in zone {zone.type_.name}: {zone.free}")

    def find_adjacent_free_spots(self, free: list[int], num_spots: int, first=False) -> list[int]:
        logging.debug(f"Need {num_spots} spots to park.")
        free_indexes = []
        index = 0
        last_index = len(free)-1
        end = last_index-(num_spots-1)  # end search early (ie: don't look at last two spots if we need three)

        while index <= end:
            # Look at number of spots required to fit this size vehicle
            potential_adjacent_spots = [free[x] for x in range(index, index+num_spots)]
            logging.debug(f"Potential adjacent spots: {potential_adjacent_spots}")

            # Check for adjacency
            first_spot = potential_adjacent_spots[0]
            last_spot = potential_adjacent_spots[len(potential_adjacent_spots)-1]
            difference_between_spots = last_spot-first_spot
            all_spots_adjacent = (difference_between_spots+1) == num_spots

            if not all_spots_adjacent:
                # We could optimize how far to skip by looking at the right end of our potential spots.
                # eg: If only the first spot is not adjacent, but every other spot is, we only need to move over one.
                # eg: If all spots are adjacent except right most, we need to skip the maximum number of spots.
                # Either way, this is on the order of O(n) when lot is empty.
                # We at least skip `num_spots` when finding a successful spot.
                index += 1  # skip to spot in free list
            else:
                spot_to_park = potential_adjacent_spots[0]
                free_indexes.append(index)
                if first:
                    return free_indexes
                spots_to_skip = num_spots + 1
                index += spots_to_skip
                logging.debug(f"Found spot to park: {spot_to_park}")

        return free_indexes

    def park_adjacent(self, zone: Zone, zone_index: int, vehicle: Vehicle):
        num_adjacent = math.ceil(vehicle.size / zone.size)
        adjacent_spots_to_park = self.find_adjacent_free_spots(zone.free, num_adjacent, first=True)
        logging.debug(f"Attempting to park size {vehicle.size} vehicle in {num_adjacent} size {zone.size} spots.")
        logging.debug(f"Indexes of adjacent spots in free list to park: {adjacent_spots_to_park}")
        if adjacent_spots_to_park:
            # Helper variables
            first_spot_index_to_park = adjacent_spots_to_park[0]
            last_spot_index_to_park = first_spot_index_to_park + (num_adjacent - 1)
            logging.debug(f"First index: {first_spot_index_to_park}, last index: {last_spot_index_to_park}")

            # Set vehicle at spots, remove spots from free list
            occupied_spots = []
            for s in range(first_spot_index_to_park, last_spot_index_to_park + 1):
                spot_index = zone.free.pop(first_spot_index_to_park)
                zone.spots[spot_index] = vehicle
                occupied_spots.append(spot_index)
                logging.debug(f"Occupying spot: {spot_index}")

            # Set vehicle location
            vehicle.location = (zone.type_, zone_index, occupied_spots)
            logging.debug(f"Occupied spots: {occupied_spots}.")

            # Keep track of the number of vehicles
            self.count[vehicle.type_.name] += num_adjacent

    def park_first_available(self, vehicle: Vehicle) -> Vehicle:
        parked = False
        # Check if vehicle fits in order of type of zone
        for zone_type in vehicle.priority:
            # Check each zone within zone type
            for (zone_index, zone) in enumerate(self.zones[zone_type.name]):
                logging.debug(f"Attempting to park in {zone_type.name} zone {zone_index}: {vars(zone)}")

                # If no free spots in this zone, go to next zone of same type
                free_spots_exist = len(zone.free)
                if not free_spots_exist:
                    continue

                # Attempt to park in a single spot (we checked above that there is one)
                vehicle_fits_in_single_spot = vehicle.size <= zone.size
                if vehicle_fits_in_single_spot:
                    self.park_single(zone, zone_index, vehicle)
                    parked = True
                    break

                # Or if zone allows for bigger vehicles to park in adjacent spots
                elif zone.adjacent:
                    self.park_adjacent(zone, zone_index, vehicle)
                    parked = True
                    break

                else:
                    # Vehicle is returned without location assignment.
                    logging.warning(f"No room to park in {zone_type.name} {zone_index}.")

            if parked:
                break

        return vehicle

    # Add vehicle functions
    def add_vehicle(self, type_: VehicleType) -> Vehicle:
        """
        A helper function to park a vehicle of valid types.

        :return: The parked vehicle or None (if no room to park).
        """
        logging.debug(f"Parking {type_.name}")
        if not (isinstance(type_, VehicleType)):
            logging.error(f"Invalid vehicle type: {type_.name}")
            raise TypeError
        else:
            vehicle = self.park_first_available(Vehicle(type_=type_))

            if vehicle.location == ():
                logging.warning(f"No room to park {type_.name}.")
            else:
                self.vehicles[vehicle.id_] = vehicle
                logging.info(f"Parked {type_.name}: {vars(vehicle)}")
            return vehicle

    def add_vehicles(self, type_: VehicleType, quantity: int) -> List[Vehicle]:
        vehicles = []
        for _ in range(quantity):
            vehicle = self.add_vehicle(type_)
            vehicles.append(vehicle)
        return vehicles

    # Remove vehicle functions
    def remove_vehicle(self, vehicle: Vehicle):
        if vehicle.id_ in self.vehicles:
            location = vehicle.location
            logging.debug(f"Location to remove from: {location}")
            zone_type, zone_index, spot_indices = location

            zone_to_remove_from = self.zones[zone_type.name][zone_index]

            # Set spots to None, restore spots to free list
            for spot_index in spot_indices:
                zone_to_remove_from.spots[spot_index] = None
                bisect.insort(zone_to_remove_from.free, spot_index)

            # Decrement count for vehicle type
            self.count[vehicle.type_.name] -= 1

            # Remove from currently parked vehicles
            del self.vehicles[vehicle.id_]
        else:
            logging.warning(f"Vehicle is not in parking lot: {vehicle}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format="%(levelname)s | %(message)s")

    # Define parking zones
    cycle = Zone(type_=ZoneType.CYCLE, size=0.3, num_spots=10)
    compact = Zone(type_=ZoneType.COMPACT, size=0.8, num_spots=10)
    regular = Zone(type_=ZoneType.REGULAR, size=1.0, num_spots=20, adjacent=True)
    large = Zone(type_=ZoneType.LARGE, size=3.0, num_spots=10)
    zones = [cycle, compact, regular, large]

    # Create parking lot
    lot = Lot(zones=zones)
    lot.print_all_zones()

    # Availability
    type_available = VehicleType.CYCLE
    print(f"{type_available.name} availability: {lot.vehicle_availability(type_=type_available)}")
    type_available = VehicleType.CAR
    print(f"{type_available.name} availability: {lot.vehicle_availability(type_=type_available)}")
    type_available = VehicleType.VAN
    print(f"{type_available.name} availability: {lot.vehicle_availability(type_=type_available)}")

    print("START\n")

    # Park my motorcycle
    antons_bike = lot.add_vehicle(type_=VehicleType.CYCLE)
    type_available = VehicleType.CYCLE
    print(f"Removed my bike: {vars(antons_bike)}")
    print(f"{type_available.name} availability: {lot.vehicle_availability(type_=type_available)}")
    # Fill remaining cycle spots plus overflow into compact zone
    lot.add_vehicles(type_=VehicleType.CYCLE, quantity=10)
    # Fill remaining compact spots with cars
    lot.add_vehicles(type_=VehicleType.CAR, quantity=9)
    # Fill large lot with vans
    lot.add_vehicles(type_=VehicleType.VAN, quantity=10)

    # Remove my motorcycle
    lot.remove_vehicle(antons_bike)

    # Fill regular lot with cars
    regular_cars = lot.add_vehicles(type_=VehicleType.CAR, quantity=20)

    # Test finding adjacent spots for van
    lot.remove_vehicle(regular_cars[0])
    lot.remove_vehicle(regular_cars[1])
    lot.remove_vehicle(regular_cars[2])

    lot.remove_vehicle(regular_cars[3])

    lot.remove_vehicle(regular_cars[5])
    lot.remove_vehicle(regular_cars[6])

    lot.remove_vehicle(regular_cars[8])
    lot.remove_vehicle(regular_cars[10])

    lot.remove_vehicle(regular_cars[12])
    lot.remove_vehicle(regular_cars[13])
    lot.remove_vehicle(regular_cars[14])

    lot.remove_vehicle(regular_cars[17])
    lot.remove_vehicle(regular_cars[18])
    lot.remove_vehicle(regular_cars[19])

    # Add vans to regular zone
    regular_vans = lot.add_vehicles(type_=VehicleType.VAN, quantity=3)

    # Fill remaining spots with motorcycles until no more locations can be assigned
    lot.add_vehicles(type_=VehicleType.CYCLE, quantity=20)

    print("\nFINISH")
    lot.print_all_zones()
    print()

    # Occupancy
    vehicle_type = VehicleType.CYCLE
    print(f"Number of {vehicle_type.name}: {lot.num_parked_vehicle(vehicle_type)}")
    vehicle_type = VehicleType.CAR
    print(f"Number of {vehicle_type.name}: {lot.num_parked_vehicle(vehicle_type)}")
    vehicle_type = VehicleType.VAN
    print(f"Number of {vehicle_type.name}: {lot.num_parked_vehicle(vehicle_type)}")
