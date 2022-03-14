#!/usr/local/bin/python3
# /usr/bin/python3
# Set the path to your python3 above

import numpy as np
from gtp_connection import GtpConnection
from board_util import GoBoardUtil
from board import GoBoard
from board_util import GoBoardUtil, BLACK, WHITE, EMPTY, BORDER, PASS, coord_to_point
import sys
from pattern_util import PatternUtil
from ucb import runUcb
import linecache


MAXSIZE = 25


class Go0:
    def __init__(self):
        """
        NoGo player that selects moves randomly from the set of legal moves.

        Parameters
        ----------
        name : str
            name of the player (used by the GTP interface).
        version : float
            version number (used by the GTP interface).
        """
        self.name = "Go0"
        self.version = 1.0
        self.policy = "random"  # random or pattern
        self.num_sim = 100
        self.limit = 100
        self.use_ucb = False

    def simulate_move(self, state, move, toplay):
        # this function only evaluates a single move from all legal moves
        winRound = 0
        for _ in range(self.num_sim):
            winner = self.simulate(state, move, toplay)
            if winner == toplay:
                winRound += 1
        return winRound

    # TODO: delete this block, just saving original version of simulate function
    # def simulate(self, state, move, toplay):
    #     if self.policy == 'random':
    #         cboard = state.copy()
    #         cboard.play_move(move, toplay)
    #         opp = GoBoardUtil.opponent(toplay)
    #         return self.playGame(cboard, opp)
    #     else:
    #         # TODO
    #         return self.pattern_simulation(state, move, toplay)

    def simulate(self, state, move, toplay):
        cboard = state.copy()
        cboard.play_move(move, toplay)
        opp = GoBoardUtil.opponent(toplay)
        return self.playGame(cboard, opp)

    def playGame(self, board, color):
        """
        Run a simulation game.
        """
        nuPasses = 0
        for _ in range(self.limit):
            color = board.current_player
            if self.policy == "random":
                move = GoBoardUtil.generate_random_move(board, color, True)
            else:
                values_str = self.policy_moves_pattern(board, color)
                if values_str is None:
                    move = PASS
                else:
                    coord_prob = values_str.split(' ')
                    size = len(coord_prob) // 2
                    coord = coord_prob[:size]
                    prob_str = coord_prob[size:]
                    prob_v = [float(x) for x in prob_str]
                    indices = [index for index, item in enumerate(prob_v) if item == max(prob_v)]
                    move = coord[indices[0]]
                    row, column = move_to_coord(move, board.size)
                    move = coord_to_point(row, column, board.size)
            board.play_move(move, color)
            if move == PASS:
                nuPasses += 1
            else:
                nuPasses = 0
            if nuPasses >= 2:
                break
        return self.evaluate(board.current_player)

    def evaluate(self, current_player):
        return BLACK + WHITE - current_player

    # run this to start

    def get_move(self, board, color):
        """
        Run one-ply MC simulations to get a move to play.
        """
        cboard = board.copy()
        # emptyPoints = board.get_empty_points()
        # moves = []
        # for p in emptyPoints:
        #     if board.is_legal(p, color):
        #         moves.append(p)
        moves = GoBoardUtil.generate_legal_moves(board, color)
        if not moves:
            return None
        if self.use_ucb:
            C = 0.4  # sqrt(2) is safe, this is more aggressive
            best = runUcb(self, cboard, C, moves, color)
            return best
        else:
            moveWins = []
            coord_moves = []
            for move in moves:
                wins = self.simulate_move(cboard, move, color)
                moveWins.append(wins)
            #writeMoves(cboard, moves, moveWins, self.sim)
            for move in moves:
                coord_moves.append(format_point(
                    point_to_coord(move, board.size)))
            testReturn = writeMoves(cboard, moves, moveWins, self.num_sim)
            # return testReturn
            return select_best_move(board, moves, moveWins)

    def policy_moves(self, board, color):
        if self.policy == "random":
            return self.policy_moves_random(board, color)
        else:
            return self.policy_moves_pattern(board, color)

    def policy_moves_random(self, board, color):
        # emptyPoints = board.get_empty_points()
        # moves = []
        return_list = []
        # for p in emptyPoints:
        #     if board.is_legal(p, color):
        #         moves.append(p)
        moves = GoBoardUtil.generate_legal_moves(board, color)
        if not moves:
            return None

        floating = round(1/len(moves), 3)
        for move in moves:
            return_list.append(format_point(point_to_coord(move, board.size)))
        return_list.sort(key=lambda x: x[0])
        return_string = ''
        for ele in return_list:
            return_string += ele+" "

        for i in range(len(return_list)):
            return_string += str(floating)+" "
        return return_string

    def policy_moves_pattern(self, board, color):
        coord_list = []
        weight_line_number = []
        moves = GoBoardUtil.generate_legal_moves(board, color)
        if not moves:
            return None

        for move in moves:
            weight_index = PatternUtil.find_weight_index(board, move)
            weight_line_number.append(weight_index + 1)
            coord_list.append(format_point(point_to_coord(move, board.size)))

        weights = []
        for i in weight_line_number:
            x = linecache.getline(r"weights.txt", i).strip()
            weights.append(float(x.split(' ')[1]))

        weight_sum = sum(weights)
        probability_list = [round(x / weight_sum, 3) for x in weights]

        coord_str = ''
        prob_str = ''
        zipped_result = sorted(zip(coord_list, probability_list))
        for coord, prob in zipped_result:
            coord_str = coord_str + coord + ' '
            prob_str = prob_str + str(prob) + ' '
        result_str = coord_str + prob_str
        return result_str[:-1]

    # def get_move(self, board, color):
    #     return GoBoardUtil.generate_random_move(board, color,
    #                                             use_eye_filter=False)


def select_best_move(board, moves, moveWins):
    """
    Move select after the search.
    """
    max_child = np.argmax(moveWins)
    return moves[max_child]


def percentage(wins, numSimulations):
    return float(wins) / float(numSimulations)


def writeMoves(board, moves, count, numSimulations):
    """
    Write simulation results for each move.
    """
    gtp_moves = []
    for i in range(len(moves)):
        move_string = "Pass"
        if moves[i] != None:
            x, y = point_to_coord(moves[i], board.size)
            move_string = format_point((x, y))
        gtp_moves.append((move_string,
                          percentage(count[i], numSimulations)))
    return gtp_moves


def point_to_coord(point, boardsize):
    """
    Transform point given as board array index
    to (row, col) coordinate representation.
    Special case: PASS is not transformed
    """
    if point == PASS:
        return PASS
    else:
        NS = boardsize + 1
        return divmod(point, NS)


def format_point(move):
    """
    Return move coordinates as a string such as 'A1', or 'PASS'.
    """
    assert MAXSIZE <= 25
    column_letters = "abcdefghijklmnopqrstuvwxyz"
    if move == PASS:
        return "PASS"
    row, col = move
    if not 0 <= row < MAXSIZE or not 0 <= col < MAXSIZE:
        raise ValueError
    return column_letters[col - 1] + str(row)


def move_to_coord(point_str, board_size):
    """
    Convert a string point_str representing a point, as specified by GTP,
    to a pair of coordinates (row, col) in range 1 .. board_size.
    Raises ValueError if point_str is invalid
    """
    if not 2 <= board_size <= MAXSIZE:
        raise ValueError("board_size out of range")
    s = point_str.lower()
    if s == "pass":
        return PASS
    try:
        col_c = s[0]
        if (not "a" <= col_c <= "z") or col_c == "i":
            raise ValueError
        col = ord(col_c) - ord("a")
        if col_c < "i":
            col += 1
        row = int(s[1:])
        if row < 1:
            raise ValueError
    except (IndexError, ValueError):
        raise ValueError("invalid point: '{}'".format(s))
    if not (col <= board_size and row <= board_size):
        raise ValueError("point off board: '{}'".format(s))
    return row, col


def run():
    """
    start the gtp connection and wait for commands.
    """
    board = GoBoard(7)
    con = GtpConnection(Go0(), board)
    con.start_connection()


if __name__ == "__main__":
    run()
