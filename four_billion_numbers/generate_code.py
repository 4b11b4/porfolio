from timeit import default_timer as timer

from Generator import *


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s | %(message)s")

    # Set up test
    digits = 8
    num_sections = 1024*2  # number of sections that the max value is divided into
    gen = Generator(num_hex_digits=digits, num_sections=1024*2)

    start = timer()
    # Generate a single code
    print(f"code: {gen.generate_code()}")
    print(f"time: {timer()-start} sec")
