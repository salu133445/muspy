import muspy

from .utils import TEST_ABC_DIR, TEST_ABC_DIR_OUTPUT

import os

data_files = os.listdir(TEST_ABC_DIR)
print(data_files)

for file in data_files:
    print(file)
    abc_music1 = muspy.read_abc(TEST_ABC_DIR / file)

    muspy.write_abc(path= TEST_ABC_DIR_OUTPUT / file, music=abc_music1)

# file = "rest.abc"
# abc_music1 = muspy.read_abc(TEST_ABC_DIR / file)
# muspy.write_abc(path= TEST_ABC_DIR_OUTPUT / file, music=abc_music1)
