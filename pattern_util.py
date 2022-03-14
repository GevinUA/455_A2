"""
pattern_util.py
Utility functions for rule based simulations.
"""

from board_util import GoBoardUtil, EMPTY, PASS, BORDER


class PatternUtil(object):
    @staticmethod
    def find_weight_index(board, point):
        """
        Get the pattern around point.
        Returns
        -------
        pattern:
        A pattern in the same format as in michi pattern base. 
        Refer to pattern.py for documentation of this format.
        """
        positions = [
            point - board.NS - 1,
            point - board.NS,
            point - board.NS + 1,
            point - 1,
            point,
            point + 1,
            point + board.NS - 1,
            point + board.NS,
            point + board.NS + 1,
        ]

        pattern = ""
        for index in range(len(positions)):
            d = positions[index]
            if index == 4:
                continue
            if board.board[d] == board.current_player:
                pattern += str(board.current_player)
            elif board.board[d] == GoBoardUtil.opponent(board.current_player):
                pattern += str(GoBoardUtil.opponent(board.current_player))
            elif board.board[d] == EMPTY:
                pattern += "0"
            elif board.board[d] == BORDER:
                pattern += "3"
        weight_index = 0
        for index in range(len(pattern)):
            weight_index += int(pattern[index]) * (4 ** index)
        return weight_index
