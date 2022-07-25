from enum import Enum
import logging
import math
import uuid

logging.basicConfig(level=logging.DEBUG)


class VehicleType(Enum):
    CYCLE = "motorcycle"
    CAR = "car"
    VAN = "van"


class Vehicle:
    type_ = None
    location = None
    id = ""

    def __init__(self, type_: VehicleType):
        self.type_ = type_
        self.id = str(uuid.uuid4())
        logging.debug(f"New vehicle: {vars(self)}")


class SpotType(Enum):
    CYCLE = "motorcycle"
    COMPACT = "compact"
    REGULAR = "regular"
    LARGE = "large"


class Spot:
    type_ = None
    occupied = None

    def __init__(self, type_: SpotType):
        self.type_ = type_
        self.occupied = None


class Zone:
    type_ = None
    spots = []

    def __init__(self, type_: SpotType, count: int):
        if not (isinstance(type_, SpotType)):
            logging.error(f"Invalid type for zone: {type_}")
        else:
            self.type_ = type_
            for i in range(0, count):
                self.spots.append(Spot(type_))


class Lot:
    spotTypes = {
        "cycle": [],
        "compact": [],
        "regular": [],
        "large": []
    }

    cycleSpots = []
    compactSpots = []
    regularSpots = []
    largeSpots = []

    def __init__(self, num_cycles, num_compact, num_regular, num_large):
        # Populate parking spots
        for i in range(0, num_cycles):
            self.cycleSpots.append(Spot(SpotType.CYCLE))
            self.spotTypes["cycle"].append(Spot(SpotType.CYCLE))
        for i in range(0, num_compact):
            self.compactSpots.append(Spot(SpotType.COMPACT))
            self.spotTypes["compact"].append(Spot(SpotType.COMPACT))
        for i in range(0, num_regular):
            self.regularSpots.append(Spot(SpotType.REGULAR))
            self.spotTypes["regular"].append(Spot(SpotType.REGULAR))
        for i in range(0, num_large):
            self.largeSpots.append(Spot(SpotType.LARGE))
            self.spotTypes["large"].append(Spot(SpotType.LARGE))

        # Print properties of spots
        #for i in range(0, len(self.cycleSpots)):
        #    print(vars(self.cycleSpots[i]))

    def getOpenSpotsForVehicle(self, vehicle: VehicleType) -> int:
        # First, check for valid vehicle type
        if not (isinstance(vehicle, VehicleType)):
            print(f"Invalid vehicle type: {vehicle}")
            return -1  # better error, or API exposing function is responsible
            # alternatively, raise TypeError

        # Determine available spots for vehicle type
        else:
            available = 0

            # Motorcycle fits anywhere
            if vehicle == VehicleType.CYCLE:
                for i in range(0, len(self.cycleSpots)):
                    if self.cycleSpots[i].occupied is None:
                        available += 1
                for i in range(0, len(self.compactSpots)):
                    if self.compactSpots[i].occupied is None:
                        available += 1
                for i in range(0, len(self.regularSpots)):
                    if self.regularSpots[i].occupied is None:
                        available += 1
                for i in range(0, len(self.largeSpots)):
                    if self.largeSpots[i].occupied is None:
                        available += 1
                #for type, spots in self.spotTypes.items():
                #    for i in range(0, len(spots)):
                #        if spots[i].occupied == None:
                #            available += 1
                return available

            # Car fits anywhere except cycle 
            elif vehicle == VehicleType.CAR:
                for type, spots in self.spotTypes.items():
                    if type == "cycle":
                        continue
                    for i in range(0, len(spots)):
                        if spots[i].occupied is None:
                            available += 1
                return available

            # Van fits in large space or 3 regular spaces
            elif vehicle == VehicleType.VAN:
                #for type, spots in self.spotTypes.items():
                #    if type == "cycle" or type == "compact":
                #        continue
                #    for i in range(0, len(spots)):
                #        if spots[i].occupied == None:
                #            available += 1
                carSpots = 0
                for i in range(0, len(self.regularSpots)):
                    if self.regularSpots[i].occupied is None:
                        carSpots += 1
                vanSpots = math.floor(carSpots/3)
                available += vanSpots
                for i in range(0, len(self.largeSpots)):
                    if self.largeSpots[i].occupied == None:
                        available += 1
                return available

    def getNumParkedVehiclesOfType(self, vehicle: VehicleType) -> int:
        pass

    def parkVehicle(self, vehicle: VehicleType) -> bool:
        if not (isinstance(vehicle, VehicleType)):
            print(f"Invalid vehicle type: {vehicle}")
            return -1  # better error, or API exposing function is responsible
            # alternatively, raise TypeError

        else:
            print(f"Trying to park {vehicle}...")
            match vehicle:
                case VehicleType.CYCLE:
                    for i in range(0, len(self.cycleSpots)):
                        if self.cycleSpots[i].occupied == None:
                            self.cycleSpots[i].occupied = Vehicle(vehicle)
                            #TODO "Parking Zone" class, tracks num open
                            return True
                    # try park cycle in other spots
                    return False
                case other:
                    pass


if __name__ == "__main__":
    lot = Lot(num_cycles=2, num_compact=1, num_regular=3, num_large=1)
    print(f"Cycle spots: {lot.getOpenSpotsForVehicle(VehicleType.CYCLE)}")
    print(f"Car spots: {lot.getOpenSpotsForVehicle(VehicleType.CAR)}")
    print(f"Van spots: {lot.getOpenSpotsForVehicle(VehicleType.VAN)}")
    print(f"Cycle parked: {lot.parkVehicle(VehicleType.CYCLE)}")
    print(f"Cycle spots: {lot.getOpenSpotsForVehicle(VehicleType.CYCLE)}")
