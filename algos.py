import robot
import numpy as np

class DFS(robot.Robot):
    """
    Depth-first search (uninformed)
    How it works:      Arbitrarily choose a route until blocked. Then backtrack until finding an unvisited neighbour and continue.
    Stop condition:    Arrived at destination
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def algo_exploration(self, neighbours):
        next_moves = list(filter(lambda move: move not in self.visited, neighbours))
        if len(next_moves) > 0:
            self.proceed(next_moves)
        else:
            self.backtrack()
        
    def algo_victory(self):
        self.move_here = self.victory_route.pop(0)

    def proceed(self, next_moves):
        self.move_here = next_moves[0]
        self.stack.append(self.position)

    def backtrack(self):
        self.move_here = self.stack.pop()
        if self.rotation_needed(self.move_here) is None:
            self.stack.append(self.move_here)
            
    def check_reset_condition(self):
        if self.position in self.goals:
            self.victory_route = self.stack[1:].copy() + [self.position]
            self.reset = True
        
    def reset_round(self):
        super().reset_round()
        self.visited = {self.start}
        self.stack = list()


class BestFirst(DFS):
    """
    Best-first search (Informed edition)
    How it works:      DFS algorithm with heuristic function to navigate to the center of the maze more efficiently.
                       Use manhattan distance or euclidean distance to choose a route until blocked. Then backtrack until finding an unvisited neighbour and continue.
    Stop condition:    Arrived at destination
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dist_func = self.manhattan

    def proceed(self, next_moves):
        moves_sorted = sorted(next_moves, key=lambda move: self.dist_to_goal(move))
        self.move_here = moves_sorted[0]
        self.stack.append(self.position)

    def dist_to_goal(self, position):
        return min([self.dist_func(position, goal) for goal in self.goals])

    def manhattan(self, source, destination):
        return abs(source[0] - destination[0]) + abs(source[1] - destination[1])
    
    def euclidean(self, source, destination):
        return ((source[0] - destination[0])**2 + (source[1] + destination[1])**2)**0.5


class Dijkstra(DFS):
    """
    Dijstra's algorithm (Uninformed)
    How it works:   Use DFS to map the entire maze on the first run. Assign a score of distance from start to each cell to find the optimal path after exploration
    Stop condition: Mapped the entire maze on first run and reached the center on second run
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maze_data = np.ones((self.maze_dim, self.maze_dim, 3), dtype=np.uint16) * 9999  # (score, parent_x, parent_y)
        self.maze_data[0,0] = (0, 0, 0)

    def proceed(self, next_moves):
        super().proceed(next_moves)
        self.update_neighbours(self.position)

    def update_neighbours(self, start_pos):
        queue = [(start_pos, self.get_score(self.position))]
        while len(queue) > 0:
            pos, score = queue.pop(0)
            for neighbour in self.get_neighbours(pos):
                neighbour_score = self.get_score(neighbour)
                if neighbour_score > score+1:
                    self.maze_data[neighbour] = (score+1 ,pos[0], pos[1])
                    if neighbour in self.visited:
                        queue.append((neighbour, score+1))

    def check_reset_condition(self):
        if (self.visited_all()) or ((len(self.stack) == 0) and (self.goals[0] in self.visited)):
            node = self.goals[0]
            while node != (0,0):
                self.victory_route.insert(0, node)
                node = self.get_parent(node)
            self.reset = True

    def get_score(self, position):
        return self.maze_data[position][0]
    
    def get_parent(self, position):
        return tuple(self.maze_data[position][1:])

    def visited_all(self):
        return len(self.visited) == self.maze_dim ** 2


class FloodFill(robot.Robot):
    """
    FloodFill algorithm
    How it works:   Assign the value 0 to the target cell (usually the goal) and add +1 to each available neighbour not blocked by a wall. 
                    As the maze is being revealed, re-perform the calculation and find a route to the goal using the lowest number of any of the unblocked neighbours.
    Stop condition: The first run is consisted of a path from the start to the goal and another path back from the goal to the start
                    The second run is a path from the start to the goal using all the information from the 2 paths.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def algo_next_move(self, possible_moves):
        return self.algo_exploration(possible_moves)
    
    def algo_exploration(self, new_moves):
        next_moves = sorted(new_moves, key=lambda move: self.get_value(move))
        self.proceed(next_moves)

    def proceed(self, next_moves):
        self.move_here = next_moves[0]

    def reset_round(self):
        super().reset_round()
        self.halfway = False
        self.set_new_goals(self.goals)

    def check_reset_condition(self):
        if self.position in self.ff_goals:
            if self.halfway:
                self.reset = True
            else:
                self.halfway = True
                self.set_new_goals([self.start])

    def set_new_goals(self, new_goals):
        self.ff_goals = new_goals
        self.reset_maze_data()
        self.floodfill_maze(self.ff_goals[0])
    
    def reset_maze_data(self):
        self.maze_data = np.ones((self.maze_dim, self.maze_dim), dtype=np.uint16) * 9999

    def get_value(self, position):
        return self.maze_data[position]
    
    def floodfill_maze(self, start_pos):
        queue = [start_pos]
        while len(queue) > 0:
            pos = queue.pop(0)
            neighbours = self.get_neighbours(pos)
            new_score = min([self.get_value(neighbour) for neighbour in neighbours]) + 1 if pos not in self.ff_goals else 0
            my_score = self.get_value(pos)
            if my_score != new_score:
                self.maze_data[pos] = new_score
                queue += neighbours
    
    def init_new_step(self, sensors):
        super().init_new_step(sensors)
        self.set_new_goals(self.ff_goals)


class FloodFillExploratory(FloodFill):
    """
    FloodFill optimized algorithm
    How it works:    Same as the above FloodFill algorithm, only the robot performs the route from start to finish and back more than twice until it is sure the path is available.
    Stop condition:  No unvisited cells in the optimal route from the start to the goal
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def check_reset_condition(self):
        if self.position in self.ff_goals:
            self.set_new_goals(self.goals)
            route = self.simulate_route(self.start)
            unvisited = list(filter(lambda cell: cell not in self.visited, route))
            if len(unvisited) == 0:
                self.reset = True
                return

            if self.halfway:
                self.halfway = False
                self.set_new_goals([unvisited[0]])
            else:
                self.halfway = True
                self.set_new_goals([unvisited[0]])
    
    def simulate_route(self, start_pos):
        route = list()
        pos = start_pos
        while pos not in self.ff_goals:
            pos = min(self.get_neighbours(pos), key=lambda neighbour: self.get_value(neighbour))
            route.append(pos)
        return route

ALGOS = {
    'dfs': DFS,
    'bfs': BestFirst,
    'dijkstra': Dijkstra,
    'floodfill': FloodFill,
    'floodfillexploratory': FloodFillExploratory
    }
