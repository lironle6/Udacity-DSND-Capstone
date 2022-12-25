import numpy as np

class Robot(object):
    """
    Base class that handles all common actions for all algorithms:
    Initialize rounds and mazes
    Update step counter and log previous steps for future analysis and visualizations
    Update position, rotation and maze memory as discovered
    Filter moves blocked by walls for the chosen algorithm and handle reset responses
    """
    
    def __init__(self, maze_dim):
        self.dir_int = {'u': 1, 'r': 2, 'd': 4, 'l': 8}
        self.dir_int_opposite = {'u': 4, 'r': 8, 'd': 1, 'l': 2}
        self.dir_to_coords = {'u': (0,1), 'r': (1,0), 'd': (0,-1), 'l': (-1,0)}
        self.maze_dim = maze_dim
        self.start = (0, 0)
        self.journey = list()
        self.run_num = -1
        self.steps = -1
        self.victory_route = list()
        self.sensor_rotation = [-90, 0, 90]
        self.rot_to_coords = {0: (0,1), 90: (1,0), 180: (0,-1), 270: (-1,0)}
        self.coords_to_rot = {(0,1):0, (1,0):90, (0,-1):180, (-1,0):270}
        self.rotation_dict = {0:0, 90:90, 270:-90, 180:None}
        self.goals = [
            (self.maze_dim // 2, self.maze_dim // 2),
            (self.maze_dim // 2 - 1, self.maze_dim // 2),
            (self.maze_dim // 2, self.maze_dim // 2 - 1),
            (self.maze_dim // 2 - 1, self.maze_dim // 2 - 1)
        ]
        self.move_here = None
        self.visited = {self.start}
        self.init_maze()
        self.reset_round()

    def algo_next_move(self, neighbours):
        """
        Chosen algorithm will decide next move.
        possible moves: list of tuples. 
        A few examples: 
            [(11, 0)] - there are 11 available cells forward
            [(1, 90), (2, -90)] - there is 1 availble cell to the right and 2 available cells to the left
        """
        if self.run_num == 0:
            self.algo_exploration(neighbours)
        else:
            self.algo_victory()

    def algo_exploration(self, possible_moves):
        return 'Reset', 'Reset'

    def algo_victory(self):
        return 'Reset', 'Reset'

    def next_move(self, sensors):
        self.init_new_step(sensors)
        
        neighbours = self.get_neighbours(self.position)
        self.algo_next_move(neighbours)
        if self.run_num == 0:
            self.check_reset_condition()
        if self.reset:
            self.reset_round()
            return 'Reset', 'Reset'
        
        self.next_rotation, self.next_movement = self.rotation_needed(self.move_here), 1
        if self.next_rotation == None:
            self.next_rotation, self.next_movement = 90, 0
        
        self.update_position()
        self.update_rotation()
        return self.next_rotation, self.next_movement


    def init_new_step(self, sensors):
        self.steps += 1
        self.journey.append((self.position, self.maze.copy(), self.run_num))
        self.update_memory_map(sensors)
        self.visited.add(self.position)

    def update_rotation(self):
        self.rotation = self.get_new_rotation(self.next_rotation)
    
    def get_new_rotation(self, rotation):
        return (self.rotation + rotation) % 360
        
    def update_position(self):
        self.position = self.get_next_position(self.next_rotation, self.next_movement)
    
    def get_next_position(self, rotation, movement):
        new_rotation = self.get_new_rotation(rotation)
        x_move, y_move = self.rot_to_coords[new_rotation]
        return self.position[0] + x_move * movement, self.position[1] + y_move * movement

    def update_memory_map(self, sensors):
        directions = ['l', 'u', 'r', 'd']
        rot = self.rotation // 90
        directions = directions[rot:] + directions[:rot]  # Align according to robot rotation
        detected_walls = 0
        for direction, sensor in zip(directions, sensors):
            if sensor == 0:
                self.maze[self.position] &= ~self.dir_int[direction]
                try:
                    adjacent_pos = self.get_neighbour(self.position, direction)
                    self.maze[adjacent_pos] &= ~self.dir_int_opposite[direction]
                except IndexError:
                    pass

    def init_maze(self):
        self.maze = np.ones((self.maze_dim, self.maze_dim), dtype=np.uint8) * 15
        self.maze[0,:] &= 15 - self.dir_int['l']
        self.maze[self.maze_dim-1,:] &= 15 - self.dir_int['r']
        self.maze[:,0] &= 15 - self.dir_int['d']
        self.maze[:,self.maze_dim-1] &= 15 - self.dir_int['u']
    
    def reset_round(self):
        self.run_num += 1
        self.rotation = 0
        self.position = self.start
        self.next_rotation = 0
        self.next_movement = 0
        self.reset = False
    
    def check_reset_condition(self):
        pass
    
    def rotation_for_pos(self, new_pos):
        delta_x = (new_pos[0] - self.position[0])
        delta_y = (new_pos[1] - self.position[1])
        return self.coords_to_rot[(delta_x, delta_y)]

    def filter_visited(self, possible_move):
        sensor, rot = possible_move
        next_pos = self.get_next_position(rot, min(sensor, 1))
        return next_pos not in self.visited
    
    def get_neighbours(self, pos):
        neighbours = list()
        dir_to_letter = {0:'u', 90:'r', 270:'l', 180:'d'}
        directions = [0, 90, 270, 180] #  forward -> right -> left -> back
        for direction in directions:
            dir_letter = dir_to_letter[(direction + self.rotation) % 360]
            if self.is_permissible(pos, dir_letter):
                delta = self.dir_to_coords[dir_letter]
                neighbours.append((pos[0] + delta[0], pos[1] + delta[1]))
        return neighbours

    def get_neighbour(self, pos, direction):
        delta = self.dir_to_coords[direction]
        return pos[0] + delta[0], pos[1] + delta[1]
   
    def is_permissible(self, cell, direction):
        return (self.maze[tuple(cell)] & self.dir_int[direction] != 0)

    def rotation_needed(self, pos):
        rotation = self.rotation_for_pos(self.move_here)
        needed_rotation = (rotation - self.rotation) % 360
        return self.rotation_dict[needed_rotation]