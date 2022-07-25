import bisect
from collections import defaultdict
from enum import Enum
import logging
import math
from typing import List
import uuid


class VehicleType(Enum):
    CYCLE = "motorcycle"
    CAR = "car"
    VAN = "van"


class Vehicle:
    def __init__(self, type_: VehicleType):
        self.type_ = type_
        self.id_ = str(uuid.uuid4())
        logging.debug(f"New vehicle: {vars(self)}")


class ZoneType(Enum):
    CYCLE = "motorcycle"
    COMPACT = "compact"
    REGULAR = "regular"
    LARGE = "large"


class Zone:
    def __init__(self, type_: ZoneType, num_spots: int):
        if isinstance(type_, ZoneType):
            self.type_ = type_
            self.spots = [None for _ in range(num_spots)]  # contains None or Vehicle
            self.free = [x for x in range(num_spots)]
            self.available = num_spots
            logging.debug(f"New zone: {vars(self)}")
        else:
            logging.error(f"Invalid type for zone: {type_}")


class Lot:
    def __init__(self, num_cycles, num_compact, num_regular, num_large):
        # [Parking] Zones, and the logic for parking vehicles within them
        # could be made more extensible by allowing the user to add zones manually (eg: to a dictionary).
        # However, now the responsibility lies with the user to add the priority logic as well
        # and it _would_ be possible to abstract the priority rules to a user by simply adding properties to a vehicle
        # (eg: vehicle.priority[list of ZoneTypes], vehicle.size=3 *** but only size 3 in "regular" zone ***).
        # Thus, vans have a special parking rule that is best expressed using Python... and thus
        # below, the zones are given, along with the logic for parking a vehicle (see park_car(), park_van(), etc).
        self.cycles = Zone(type_=ZoneType.CYCLE, num_spots=num_cycles)
        self.compact = Zone(type_=ZoneType.COMPACT, num_spots=num_compact)
        self.regular = Zone(type_=ZoneType.REGULAR, num_spots=num_regular)
        self.large = Zone(type_=ZoneType.LARGE, num_spots=num_large)

        # Count of each VehicleType
        self.parked = defaultdict(int)  # key: VehicleType, value: total number of vehicles in lot

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
        print(f"Moto    | {self.zone_spots_string(self.cycles)}")
        print(f"Compact | {self.zone_spots_string(self.compact)}")
        print(f"Regular | {self.zone_spots_string(self.regular)}")
        print(f"Large   | {self.zone_spots_string(self.large)}")

    # Lot availability functions
    def vehicle_availability(self, type_: VehicleType) -> int:
        # TODO could be refactored to similar pattern as park_car, park_motorcycle, etc
        available = 0
        cycles = len(self.cycles.free)
        compact = len(self.compact.free)
        regular = len(self.regular.free)
        large = len(self.large.free)

        match type_:
            # Motorcycle fits anywhere
            case VehicleType.CYCLE:
                available = cycles + compact + regular + large
            # Car doesn't fit in motorcycle spot
            case VehicleType.CAR:
                available = compact + regular + large
            # Van fits in large or 3 adjacent regular spots
            case VehicleType.VAN:
                num_van_spots_in_regular = len(self.find_van_spots_in_regular_zone())
                available = large + num_van_spots_in_regular
            case _:
                logging.error(f"Vehicle type not handled: {type_}")

        return available

    # Lot occupancy functions
    def num_parked_vehicle(self, type_: VehicleType) -> int:
        """
        A helper function to get the count of parked vehicles of valid types.

        :return: The count of parked vehicles of a certain type.
        """
        if not (isinstance(type_, VehicleType)):
            logging.error(f"Invalid vehicle type: {type_}")
            raise TypeError
        else:
            num_vehicles = self.parked[type_.value]
        logging.debug(f"Number of {type_.name}: {num_vehicles}")
        return num_vehicles

    # Add vehicle helper functions
    def add_vehicle_in_zone(self, zone: Zone, vehicle: Vehicle):
        """
        Parks a vehicle at first spot in a zone's `free` list.

        :param zone: The zone to park in.
        :param vehicle: The vehicle to park.
        :return: Index of parking spot within zone.
        """
        # Rules for priority of zones to park vehicles reside in the add_car(), add_motorcycle(), etc functions.
        # The assignment of vehicles to certain zones doubles as a check for valid vehicles in specific zone.
        # However, a check that is not concerned with priority could also happen here for sanity.
        logging.debug(f"Free spots for {vehicle.type_.name} in zone {zone.type_.name}: {zone.free}")

        # Assign vehicle to spot first free spot
        first_free_spot = zone.free.pop(0)
        zone.spots[first_free_spot] = vehicle

        # Keep track of how many vehicles
        self.parked[vehicle.type_.value] += 1
        logging.debug(f"Parked vehicles: {self.parked}")

        # TODO set vehicle .zone and .spot

        logging.debug(f"Parking {vehicle} at spot index {first_free_spot}")
        logging.debug(f"Remaining spots in zone {zone.type_.name}: {zone.free}")

    def add_van_in_regular(self, vehicle: Vehicle, spot_index: int):
        center = spot_index
        left = center - 1
        right = center + 1
        logging.debug(f"L: {left}, C: {center}, R: {right}")

        # Assign van to spot.
        self.regular.spots[left] = vehicle
        self.regular.spots[center] = vehicle
        self.regular.spots[right] = vehicle

        # Keep track of how many vehicles.
        self.parked[vehicle.type_.value] += 1
        logging.debug(f"Parked vehicles: {self.parked}")

        # TODO set vehicle .zone and .spot

        # Remove newly occupied free spots.
        # Iterates from start to end of `free` array, but spots taken are first available (are close to beginning).
        # TODO take van spots from end
        num_spots_to_remove = 3
        free_index_to_check = 0
        spots_removed = False
        while not spots_removed:
            logging.debug(f"Regular free spots: {self.regular.free}")
            # Actual spot index not to be confused with free spot index.
            potential_occupied_spot = self.regular.free[free_index_to_check]
            logging.debug(f"Checking free spot index {free_index_to_check}: {potential_occupied_spot}")
            # Van spots are always added back to `free` list in a group of 3. Find the left one, then pop three.
            if potential_occupied_spot == left:
                logging.debug(f"Found left spot in free spots.")
                for _ in range(0, num_spots_to_remove):
                    removed = self.regular.free.pop(free_index_to_check)
                    logging.debug(f"Removed free spot at index {free_index_to_check}: {removed}")
                    logging.debug(f"Remaining free spots: {self.regular.free}")
                spots_removed = True
            free_index_to_check += 1

    # TODO take van spots from end
    def find_van_spots_in_regular_zone(self) -> list[int]:
        # TODO could only find single spot, but need to know all spots for vehicle_availability function
        # TODO thus, could create two functions, or one function that returns early based on parameter `first`: bool
        """
        A van can park in three consecutive regular spots.

        If all three spots are not open,
        the spots in question are checked from right to left.

        This function written originally when the list of Spots was implemented without tracking which are open (without the stack: a zones' `free` list property).
        It could be re-implemented to simply find three consecutive integers in the `free` property instead of looking through Spots.

        :return: indexes of spots for a van to park
        """

        free_indexes = []

        # Begin search for three adjacent spots starting at space #2 (array index #1)
        index = 1
        # End search one space before the end
        last_index = len(self.regular.spots)-1
        end = last_index-1

        while index <= end:
            left = self.regular.spots[index-1] is None
            center = self.regular.spots[index] is None
            right = self.regular.spots[index+1] is None

            # All three are open: increment count, skip 3
            if left and center and right:
                free_indexes.append(index)
                index += 3
            # Right not open (left & right don't care): skip 3
            elif not right:
                index += 3
            # Center not open (right open, left don't care):
            elif not center:
                index += 2
            # Right and center open, left not:
            elif not left:
                index += 1
            else:  # this covers all cases
                logging.warning(f"Else case in finding adjacent regular spots for van.")

        return free_indexes

    # Add vehicle functions
    def add_motorcycle(self) -> Vehicle:
        """
        Creates and attempts to park a motorcycle
        with specific zone priority.

        :return: The parked vehicle or None (if no room to park).
        """
        vehicle = Vehicle(VehicleType.CYCLE)

        num_free_cycle_spots = len(self.cycles.free)
        num_free_compact_spots = len(self.compact.free)
        num_free_regular_spots = len(self.regular.free)
        num_free_large_spots = len(self.large.free)

        if num_free_cycle_spots:
            self.add_vehicle_in_zone(zone=self.cycles, vehicle=vehicle)
        elif num_free_compact_spots:
            self.add_vehicle_in_zone(zone=self.compact, vehicle=vehicle)
        elif num_free_regular_spots:
            self.add_vehicle_in_zone(zone=self.regular, vehicle=vehicle)
        elif num_free_large_spots:
            self.add_vehicle_in_zone(zone=self.large, vehicle=vehicle)
        else:
            return None
        return vehicle

    def add_car(self) -> Vehicle:
        """
        Creates and attempts to park a car
        with specific zone priority.

        :return: The parked vehicle or None (if no room to park).
        """
        vehicle = Vehicle(VehicleType.CAR)

        num_free_compact_spots = len(self.compact.free)
        num_free_regular_spots = len(self.regular.free)
        num_free_large_spots = len(self.large.free)

        if num_free_compact_spots:
            self.add_vehicle_in_zone(zone=self.compact, vehicle=vehicle)
        elif num_free_regular_spots:
            self.add_vehicle_in_zone(zone=self.regular, vehicle=vehicle)
        elif num_free_large_spots:
            self.add_vehicle_in_zone(zone=self.large, vehicle=vehicle)
        else:
            return None
        return vehicle

    def add_van(self) -> Vehicle:
        """
        Creates and attempts to park a van
        with specific zone priority.
        :return: The parked vehicle or None (if no room to park).
        """
        vehicle = Vehicle(VehicleType.VAN)

        num_free_large_spots = len(self.large.free)

        if num_free_large_spots:
            self.add_vehicle_in_zone(zone=self.large, vehicle=vehicle)
        else:
            # Find spots for van in the regular zone. We must check every time, alternatively...
            # we could re-compute when a vehicle is parked in regular zone.
            # However, this would require the zone to keep another list (`free`, but for van spots).
            free_van_regular_spots = self.find_van_spots_in_regular_zone()
            logging.debug(f"Free locations for van in regular: {free_van_regular_spots}")
            num_free_van_regular_spots = len(free_van_regular_spots)
            if num_free_van_regular_spots:
                self.add_van_in_regular(vehicle=vehicle, spot_index=free_van_regular_spots[0])
            else:
                return None

        return vehicle

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
            vehicle = None
            match type_:
                case VehicleType.CYCLE:
                    vehicle = self.add_motorcycle()
                case VehicleType.CAR:
                    vehicle = self.add_car()
                case VehicleType.VAN:
                    vehicle = self.add_van()
                case _:
                    logging.error(f"Vehicle type not handled: {type_}")
            if vehicle is None:
                logging.warning(f"No room to park {type_.name}.")
            else:
                logging.info(f"Parked {type_.name}: {vars(vehicle)}")
            return vehicle

    def add_vehicles(self, type_: VehicleType, quantity: int) -> List[Vehicle]:
        vehicles = []
        for _ in range(quantity):
            vehicle = self.add_vehicle(type_)
            vehicles.append(vehicle)
        return vehicles

    # Remove vehicle functions
    def remove_vehicle_from_zone_at_spot(self, zone: Zone, spot_index: int) -> Vehicle:
        # TODO refactor in similar pattern as park_car, park_motorcycle, etc
        logging.debug(f"Removing vehicle from {zone.type_.name} at spot {spot_index}")
        logging.debug(f"Parked vehicles in {zone.type_.name}: {self.parked}")

        vehicle = zone.spots[spot_index]
        if vehicle is not None:
            # Remove vehicle from spot.
            if vehicle.type_ is VehicleType.VAN and zone.type_ is ZoneType.REGULAR:
                # Van is removed from three spots.
                left = spot_index - 1
                center = spot_index
                right = spot_index + 1
                # Set spots to None (remove vehicle).
                zone.spots[left] = None
                zone.spots[center] = None
                zone.spots[right] = None
                # Add freed spot back to free list. Append is O(1).
                bisect.insort(zone.free, left)
                bisect.insort(zone.free, center)
                bisect.insort(zone.free, right)
            else:
                # Set spot to None (remove vehicle).
                zone.spots[spot_index] = None
                # Add freed spot back to free list.
                bisect.insort(zone.free, spot_index)

            logging.debug(f"Vehicle was in {zone.type_.name} at spot {spot_index}: {vars(vehicle)}")
            logging.debug(f"Spot in {zone.type_.name} at spot {spot_index}: {zone.spots[spot_index]}")

            # Keep track of number of parked vehicles.
            self.parked[vehicle.type_.value] -= 1
            logging.debug(f"Remaining parked vehicles in {zone.type_.name}: {self.parked}")
            logging.info(f"Removed vehicle: {vars(vehicle)}")
        else:
            logging.warning(f"No vehicle to remove from {zone.type_.name} at spot {spot_index}.")
        return vehicle


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s | %(message)s")
    lot = Lot(num_cycles=7, num_compact=7, num_regular=7, num_large=7)
    lot.print_all_zones()
    print(f"BEGIN\n")

    print("Parking vehicles...")
    print(f"Parking cycles: {lot.add_vehicles(VehicleType.CYCLE, 2)}")
    print(f"Parking cars: {lot.add_vehicles(VehicleType.CAR, 2)}")
    print(f"Parking vans: {lot.add_vehicles(VehicleType.VAN, 2)}")
    print(f"Parking vans: {lot.add_vehicles(VehicleType.VAN, 1)}")
    print(f"Parking cycles: {lot.add_vehicles(VehicleType.CYCLE, 2)}")
    print(f"Parking cars: {lot.add_vehicles(VehicleType.CAR, 1)}")
    print(f"Parking cycles: {lot.add_vehicles(VehicleType.CYCLE, 2)}")
    print()
    print("Removing vehicles...")
    zone = lot.cycles
    spot = 0
    removed = lot.remove_vehicle_from_zone_at_spot(zone, spot)
    print(f"Removed from {zone.type_.name} at spot {spot}: {vars(removed) if (removed is not None) else removed}")
    removed = lot.remove_vehicle_from_zone_at_spot(lot.cycles, 0)
    print(f"Removed from {zone.type_.name} at spot {spot}: {vars(removed) if (removed is not None) else removed}")
    zone = lot.large
    spot = 0
    removed = lot.remove_vehicle_from_zone_at_spot(zone, spot)
    print(f"Removed from {zone.type_.name} at spot {spot}: {vars(removed) if (removed is not None) else removed}")

    print(f"\nFINISH")
    lot.print_all_zones()
    print()
    print(f"Parked cycles: {lot.num_parked_vehicle(VehicleType.CYCLE)}")
    print(f"Parked cars: {lot.num_parked_vehicle(VehicleType.CAR)}")
    print(f"Parked vans: {lot.num_parked_vehicle(VehicleType.VAN)}")
    print()
    print(f"Cycle spots: {lot.vehicle_availability(VehicleType.CYCLE)}")
    print(f"Car spots: {lot.vehicle_availability(VehicleType.CAR)}")
    print(f"Van spots: {lot.vehicle_availability(VehicleType.VAN)}")
    print()

    print(f"Free spots in zone {lot.cycles.type_.name}: {lot.cycles.free}")
    print(f"Free spots in zone {lot.compact.type_.name}: {lot.compact.free}")
    print(f"Free spots in zone {lot.regular.type_.name}: {lot.regular.free}")
    print(f"Free spots in zone {lot.large.type_.name}: {lot.large.free}")

