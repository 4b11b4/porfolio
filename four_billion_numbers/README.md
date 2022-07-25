# 2FA Code Generation: 8 Hex Digits (~4 billion numbers)
## Requirements
The requirements for this code are:
1. The program should emit an 8-digit hexadecimal code when ran.
2. The program should emit every possible code before repeating.
3. The program should emit codes in an apparently random order.

## Run: Generate Code
- Run `generate_code.py` to generate a single 8 digit hex code.
The program will create a `numpy` binary containing the state of the program.

## Test: Generate Multiple Codes
- Run `test_unique.py` to generate all possible codes in a single run.

## Implementation
The generator splits up the possible range of values into sections and picks
a section at random to retrieve a code. Each section is additionally offset
by a value based on a modulus of the index of the section and the number of
sections.

For example:
- For simplicity, let's say we wanted to generate codes between 0 and 100.
- Split into sections of size 10. The first section is from 0-9, the second
section from 10-19, and so on.
- To increase the apparent randomness: each section is offset by a modulus of the section index and the number of
sections. In this case, our first section offset is 0 (ie: index 0 % 10), and
our section section offset is 1 (ie: index 1 % 10). Thus our first section
begins counting at 0 (0+0), the second at 11 (10+1), the third at 22 (20+2),
etc.

Then we simply pick a section index at random for the code to be emitted and
then increment that section. When a section goes beyond it's range, it is
started again at the minimum. Continuing on with this pattern, we will emit
all values once before repeating.
