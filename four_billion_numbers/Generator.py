import logging
import numpy as np
import random
from typing import List


class Generator:
    def __init__(self, num_hex_digits=8, num_sections=1024):
        """
        This class can generate hexadecimal codes up to a certain number of digits
        in a random order without duplication until all possible codes have been generated.

        :param num_hex_digits: The number of digits in the code to be generated.
        :param num_sections: The number of sections between 0 and the maximum value represented by the number of digits above.
        """
        # Number of digits and the maximum value
        self.num_hex_digits = num_hex_digits
        self.max_val = (16 ** num_hex_digits) - 1
        logging.debug(f"Max: {self.max_val}")

        # The maximum value is broken up into "sections".
        # eg: If the max value was 100 and the number of sections was 10, each section would have a range of 10 values.
        self.num_sections = num_sections

        # Check that the num_sections breaks up the sections equally.
        if (self.max_val+1) % num_sections:
            logging.error("The range of values are not divided equally into sections.")

        # TODO check max_value > num_sections (by some factor) so there is room to count in each section (eg: don't divide by half of max value)

        # Determine the range of each section
        self.section_range = int((self.max_val+1) / self.num_sections)  # divides equally for any number of hex digits

        # Filename to be used based on the number of digits and sections
        self.filename = f"dig_{self.num_hex_digits}-div_{self.num_sections}.npz"
        logging.debug(f"{self.num_sections} sections, range: {self.section_range}")

        # Load the list of saved sections and list of section indexes to be incremented
        try:
            # Load section counts and section_indexes from file
            npz = np.load(self.filename)
            self.section_indexes = npz['section_indexes']
            self.sections = npz['sections']
            logging.debug(f"Loaded {len(self.section_indexes)} section indexes: {self.section_indexes}")
            logging.debug(f"Loaded {len(self.sections)} sections: {self.sections}")
        except FileNotFoundError:
            logging.warning("Previous file not found.")
            # Create section_indexes
            self.section_indexes = np.arange(0, stop=self.num_sections)
            # Create sections and their starting value
            # using for loop (more explicit and can debug)
            #temp = []
            #for x in range(0, self.num_sections):
            #    offset = x % self.section_range
            #    section_min = x * self.section_range
            #    val = section_min + offset
            #    temp.append(val)
            #    logging.debug(f"x: {x}, m: {section_min}, o: {offset}, v: {val}")
            # Create sections and their starting value
            # using list comprehension
            temp = [((x * self.section_range) + (x % self.section_range)) for x in range(0, self.num_sections)]

            # Create numpy array from list
            self.sections = np.asarray(temp)
            logging.debug(f"Created section indexes: {self.section_indexes}")
            logging.debug(f"Created sections: {self.sections}")
        finally:
            logging.info(f"Created generator for {num_hex_digits} hex digits.")

    def generate_code(self, save_state=True) -> str:
        # Get a random index from remaining section_indexes
        random_remaining_index = random.randint(0, len(self.section_indexes)-1)
        logging.debug(f"Random index for accessing section indexes: {random_remaining_index}")

        # Access section with random index from remaining section_indexes
        section_index = self.section_indexes[random_remaining_index]

        # Modulus for offset
        """
         This isn't used here because offsets are setup at creation of section values.
         Alternatively, instead of the sections storing their explicit value
         (because with 8 digits: the last section value is close to ~4B)...
         ...each section could simply count between 0 and the `section_range`
         and then the actual values (count*index + index%range) are calculated here.
         Why bother? Because the values you must store aren't as big: to get the size of the npz binary down.
         ...but I tried this once and the binary was still big
         and it may be simpler to add in the offsets when creating the sections.
        """
        #offset = section_index % self.section_range
        #logging.debug(f"Offset: {offset}")

        # Get value of section
        current_section_value = self.sections[section_index]
        logging.debug(f"Value of section {section_index}: {current_section_value}")

        # If used last index, generate new ones
        if len(self.section_indexes) == 1:
            logging.debug(f"Used last index #{random_remaining_index}: {section_index}")
            self.section_indexes = np.arange(0, stop=self.num_sections)
            logging.debug(f"New section indexes: {self.section_indexes}")
        # Remove used index
        else:
            self.section_indexes = np.delete(self.section_indexes, random_remaining_index)
            logging.debug(f"Remaining section indexes: {self.section_indexes}")

        # Extremes for section
        min_section_value = section_index*self.section_range
        max_section_value = ((section_index+1)*self.section_range)-1
        logging.debug(f"Section min: {min_section_value}, max: {max_section_value}")

        # Increment section
        self.sections[section_index] += 1
        logging.debug(f"New value of section counter {section_index}: {self.sections[section_index]}")

        # If section exceeds max, reset to min
        if self.sections[section_index] > max_section_value:
            self.sections[section_index] = min_section_value
            logging.debug(f"Section value restarted at {min_section_value}.")

        # Write sections and section indexes back to file
        if save_state:
            np.savez(self.filename, sections=self.sections, section_indexes=self.section_indexes)

        # Turn initially retrieved section value into hex string
        padded_hex = f"{current_section_value:08x}"

        logging.info(f"Generated code (hex): {padded_hex}")
        return padded_hex

    def generate_codes(self, quantity=2) -> List[int]:
        # This is slow because the npz binary is saved every time (only loaded once in constructor).
        # This is due to the requirement that a unique, random, non-duplicate (before reaching the max value) code
        # is emitted every time the program is run.
        # If we wanted this to be faster, we could keep the data in memory.
        save = False
        # With saving: ~45 sec for 4 hex digits
        # Without save: ~26 sec for 4 hex digits

        codes = []
        for _ in range(quantity):
            codes.append(self.generate_code(save_state=save))
        # Save state when we're done since we prevented it while generating codes
        if not save:
            np.savez(self.filename, sections=self.sections, section_indexes=self.section_indexes)
        return codes
