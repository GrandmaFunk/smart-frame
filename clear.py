#!/usr/bin/env python3
import time

from inky.inky_uc8159 import Inky, CLEAN


if __name__ == '__main__':

    inky = Inky()

    for _ in range(2):
        for y in range(inky.height - 1):
            for x in range(inky.width - 1):
                inky.set_pixel(x, y, CLEAN)

        inky.show()
        time.sleep(4.0)
