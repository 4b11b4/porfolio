from timeit import default_timer as timer

from Generator import *


def get_duplicates(test: list) -> list:
    dupes = []
    for item in test:
        if test.count(item):
            dupes.append(item)
    return dupes


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format="%(levelname)s | %(message)s")

    # Set up test
    digits = 6  # Anton's computer can't handle 8 digits
    gen = Generator(num_hex_digits=digits, num_sections=1024*2)

    start = timer()
    # Generate all possible codes
    codes = gen.generate_codes(16**digits)
    print(f"time: {timer()-start} sec")

    # Create set from list of codes for checking if unique
    codes_unique = set(codes)
    #print(codes)
    #print(codes_unique)
    #print(f"# of codes: {len(codes)}")
    print(f"# unique: {len(codes_unique)}")

    # Get a list of duplicates (debugging)
    #dupes = get_duplicates(codes)
    #print(f"dupes {len(dupes)}: {dupes}")
