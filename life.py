#!/usr/bin/env python
#
# Copyright (c) 2015 Adam Heins
#
# This file is part of the Multicell project, which is distributed under the MIT
# license. For the full terms, see the included LICENSE file.
#

import argparse
import curses
import os.path
import random
import signal
import sys
import time

PADDING = 5
DEAD_CHAR = '.'
FILL_CHAR = ' '
INTERVAL = 0.05

class Life:

    def __init__(self, seed_file, padding):
        self.dead_char = DEAD_CHAR
        self.padding = padding
        self.parse_seed(seed_file)

    def parse_seed(self, seed_file):
        """ Parse the Game starting layout from the seed file. """
        with open(seed_file, 'r') as seed:
            lines = seed.readlines()

        # Dimensions of grid that get displayed.
        self.disp_rows = len(lines)
        self.disp_cols = len(lines[0].strip())

        # Internal dimensions of grid after accounting for padding.
        self.rows = self.disp_rows + self.padding * 2
        self.cols = self.disp_cols + self.padding * 2

        # Make a new grid where the Game with take place.
        self.grid = self.make_empty_grid()

        # Copy the contents of the file into their proper places in the grid.
        for row in range(self.disp_rows):
            for col in range(self.disp_cols):
                self.grid[row + self.padding][col + self.padding] = lines[row][col]

    def get_neighbours(self, row, col):
        """ Gathers all the live neighbours of the cell. """
        neighbours = []

        # Positions of all neighbouring cells.
        neighbour_indices = [(row - 1, col - 1), (row - 1, col),
                (row - 1, col + 1), (row, col - 1), (row, col + 1),
                (row + 1, col - 1), (row + 1, col), (row + 1, col + 1)]

        # Add live neighbours to the list.
        for (row, col) in neighbour_indices:
            try:
                char = self.grid[row][col]
                if char != self.dead_char:
                    neighbours.append(char)
            except IndexError:
                pass
        return neighbours

    def generate_cell(self, row, col):
        """ Generates a the next state of a cell based on its neighbours. """
        neighbours = self.get_neighbours(row, col)
        num_neighbours = len(neighbours)
        # Live cells continue to survive if they have only two or three
        # neighbours.
        if self.grid[row][col] != self.dead_char:
            if num_neighbours < 2:
                return self.dead_char
            if num_neighbours > 3:
                return self.dead_char
            return self.grid[row][col]

        # If the cell is dead and surrounding be three live cells, it gets
        # 'born'.
        if num_neighbours == 3:
            if neighbours[0] == neighbours[1]  == neighbours[2]:
                return neighbours[0]
            if neighbours[0] == neighbours[1] or neighbours[0] == neighbours[2]:
                return neighbours[0]
            if neighbours[1] == neighbours[2]:
                return neighbours[1]
            return neighbours[random.randint(0, 2)]

        return self.dead_char

    def next_generation(self):
        """ Updates the grid with a new generation of cells. """
        new_grid = self.make_empty_grid()
        for row in range(self.rows):
            for col in range(self.cols):
                new_grid[row][col] = self.generate_cell(row, col)
        self.grid = new_grid

    def display(self, stdscr):
        """ Print the grid to the screen. """
        hor_border = '{c:{b}<{w}}{c}'.format(c='+', b='-', w=self.disp_cols+1)

        stdscr.addstr(hor_border + '\n')
        for row in range(self.padding, self.rows - self.padding):
            row_str = '|'
            for col in range(self.padding, self.cols - self.padding):
                char = self.grid[row][col]
                if char == self.dead_char:
                    row_str = row_str + FILL_CHAR
                else:
                    row_str = row_str + char
            stdscr.addstr(row_str + '|\n')
        stdscr.addstr(hor_border + '\n')

    def make_empty_grid(self):
        """ Makes a grid for the Game initialized with the dead character. """
        return [[self.dead_char for col in range(self.cols)]
                for row in range(self.rows)]

def handle_keys(stdscr, pause):
    """ Handles key presses that occur during the Game loop. """
    c = stdscr.getch()
    if c == ord('q'):
        sys.exit(0)
    elif c == ord('p') or pause:
        pause = True
        stdscr.nodelay(False)
        while True:
            c = stdscr.getch()
            if c == ord('q'):
                sys.exit(0)
            elif c == ord('p'):
                pause = False
                break
            elif c == ord('s'):
                break
        stdscr.nodelay(True)
    return pause

def game(stdscr):
    """ Main game loop. """
    stdscr.nodelay(True)

    # Create a new instance of Game of Life.
    life = Life(args.seed, args.padding)

    # Display title and instructions.
    stdscr.addstr("Multicell\nConway's Game of Life with a twist.")
    stdscr.move(life.disp_rows + 4, 0)
    stdscr.addstr("Press 'q' to quit, 'p' to pause/unpause, and 's' to step "
                  "when paused.\n")

    pause = False

    # Game loop.
    while True:
        stdscr.move(2, 0)
        life.display(stdscr)
        stdscr.refresh()
        stdscr.move(life.disp_rows + 5, 0)
        life.next_generation()
        pause = handle_keys(stdscr, pause)
        time.sleep(args.interval)

def main():
    """ Setup. """

    # Parse command line arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument('seed', help='Seed file for the Game.')
    parser.add_argument('-p', '--padding', help='Amount of padding outside of '
                        'visible area.', dest='padding', type=int,
                        default=PADDING, metavar='padding')
    parser.add_argument('-t', '--time-interval', help='Time in seconds between '
                        'each generation.', dest='interval', type=float,
                        default=INTERVAL, metavar='time-interval')
    args = parser.parse_args()

    # Argument error checking.
    if not os.path.exists(args.seed):
        raise IOError('Seed file {} does not exist!'.format(args.seed))
    if args.padding < 0:
        raise ValueError('--padding must not be negative.')
    if args.interval < 0:
        raise ValueError('--time-interval must not be negative.')

    curses.wrapper(game)

if __name__ == '__main__':
    main()
