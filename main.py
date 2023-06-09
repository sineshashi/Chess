from enum import Enum
import abc
from typing import Optional, List, Tuple, Union
from copy import deepcopy


class PieceTypes(Enum):
    pawn = "Pawn"
    rook = "Rook"
    knight = "Knight"
    bishop = "Bishop"
    king = "King"
    queen = "Queen"


class Color(Enum):
    white = "White"
    black = "Black"


def revert_color(color: Color) -> Color:
    if color == Color.white:
        return Color.black
    if color == Color.black:
        return Color.white


class Player:
    def __init__(self, name: str, color: Color) -> None:
        self.name = name
        self.color = color

class Piece(abc.ABC):
    piece_type: PieceTypes = None

    def __init__(self, color: Color) -> None:
        self.color = color

    @abc.abstractmethod
    def is_valid_move(self, board: "Board", move: "Move") -> bool:
        ...

    def move(self, board: "Board", move: "Move") -> None:
        if not self.is_valid_move(board, move):
            raise ValueError("Invalid Move.")
        board.positions[move.start.row][move.end.column].update(board, None)
        board.positions[move.end.row][move.end.column].update(board, move.start.piece)
        move.clone_positions()

    @abc.abstractmethod
    def get_all_possible_moves(self, board: "Board", position: "Position") -> List["Move"]:
        '''
        Get all possible moves by the piece.
        Moves which can result the own king in check are also included.
        '''
        ...

    def clone(self) -> "Piece":
        '''Creates a deep copy of instance.'''
        return deepcopy(self)


class Pawn(Piece):
    piece_type = PieceTypes.pawn

    def __init__(self, color: Color) -> None:
        self.color = color
        self.has_moved = False

    def _is_en_passant(self, board: "Board") -> bool:
        last_move = board.get_last_move()
        if last_move is None or last_move.start.piece.piece_type != PieceTypes.pawn:
            return False
        if abs(last_move.end.row-last_move.start.row) == 2:
            return True
        return False

    def _can_capture(self, board: "Board", move: "Move") -> bool:
        if move.end.row-move.start.row == 1 and abs(move.end.column-move.start.column) == 1:
            if move.end.piece is not None:
                return True
            elif move.end.piece is None:
                en_passant_pos = board.positions[move.start.row][move.end.column]
                if en_passant_pos is not None and en_passant_pos.piece.piece_type == PieceTypes.pawn:
                    if self._is_en_passant() \
                            and self.color != en_passant_pos.piece.color:
                        return True
        return False

    def _black_move_valid(self, board: "Board", move: "Move") -> bool:
        if move.start.column == move.end.column:
            delta_rows = move.start.row - move.end.row
            if delta_rows == 1 or (delta_rows == 2 and not self.has_moved):
                for row_in_between in range(move.start.row-1, move.end.row-1, -1):
                    if board.positions[row_in_between][move.start.column].piece is not None:
                        return False
                return True
            else:
                return False
        else:
            return self._can_capture(board, move)

    def _white_move_valid(self, board: "Board", move: "Move") -> bool:
        if move.start.column == move.end.column:
            delta_rows = move.end.row - move.start.row
            if delta_rows == 1 or (delta_rows == 2 and not self.has_moved):
                for row_in_between in range(move.start.row+1, move.end.row+1):
                    if board.positions[row_in_between][move.start.column].piece is not None:
                        return False
                return True
            else:
                return False
        else:
            return self._can_capture(board, move)

    def is_valid_move(self, board: "Board", move: "Move") -> bool:
        '''Check if move is valid.'''

        if self.color == Color.black and not self._black_move_valid(board, move):
            return False
        elif self.color == Color.white and not self._white_move_valid(board, move):
            return False
        if move.can_result_in_check_of_own_king(board):
            return False
        return True

    def can_promote(self, move: "Move") -> bool:
        '''Check if pawn can be promoted.'''

        if (
            self.color == Color.white and move.end.row == 7
        ) or (
            self.color == Color.black and move.end.row == 0
        ):
            return True
        return False

    def move(self, board: "Board", move: "Move", promote: Optional[PieceTypes] = None) -> None:
        '''Move if valid.'''

        if not self.is_valid_move(board, move):
            raise ValueError("Invalid Move")

        can_promote = self.can_promote(move)
        if can_promote and (promote is None or promote == PieceTypes.pawn):
            raise ValueError("Invalid Input for promote.")
        if not can_promote and promote is not None:
            raise ValueError("Promote must be None.")

        board.positions[move.start.row][move.start.column].update(board, None)
        if not can_promote:
            board.positions[move.end.row][move.end.column].update(board, 
                move.start.piece)
            if self._is_en_passant(board):
                board.positions[move.start.row][move.end.column].update(board, 
                    None, True)
        else:
            board.positions[move.end.row][move.end.column].update(board, promote)
        self.has_moved = True
        move.clone_positions()

    def get_all_possible_moves(self, board: "Board", position: "Position") -> List["Move"]:
        '''
        Get all possible moves by the piece.
        Moves which can result the own king in check are also included.
        '''
        poss_moves = []
        i = 1 if self.color is Color.white else -1
        if board.positions[position.row+i][position.column].piece is None:
            poss_moves.append(Move(
                position,
                board.positions[position.row+i][position.column]
            ))
        capture_positions = [(position.row+i, position.column+1),
                             (position.row+i, position.column-1)]
        for row, col in capture_positions:
            if col >= 0 and col <= 7:
                cap_piece = board.positions[row-i][col].piece
                if cap_piece is not None and cap_piece.color != self.color:
                    poss_moves.append(Move(
                        position,
                        board.positions[row][col]
                    ))
                    continue
        if self._is_en_passant(board):
            last_move = board.get_last_move()
            poss_moves.append(Move(
                position,
                board.positions[position.row+i][last_move.start.column]
            ))
        if not self.has_moved and board.positions[position.row+i][position.column] is None and \
                board.positions[position.row+2*i][position.column] is None:
            poss_moves.append(Move(
                position,
                board.positions[position.row+2*i][last_move.start.column]
            ))
        return poss_moves


class Knight(Piece):
    piece_type = PieceTypes.knight

    def is_valid_move(self, board: "Board", move: "Move") -> bool:
        if (abs(move.start.row-move.end.row) == 2 and abs(move.start.column-move.end.column) == 1) or \
                (abs(move.start.row-move.end.row) == 1 and abs(move.start.column-move.end.column) == 2):
            if not move.can_result_in_check_of_own_king(board):
                return True
        return False

    def get_all_possible_moves(self, board: "Board", position: "Position") -> List["Move"]:
        possible_moves = []
        row, col = position.row, position.column
        for i in [2, -2]:
            for j in [1, -1]:
                try:
                    move = Move(
                        position,
                        board.positions[row+i][col+j]
                    )
                    if move.is_possibly_valid():
                        possible_moves.append(move)
                except IndexError:
                    continue
                try:
                    move = Move(
                        position,
                        board.positions[row+j][col+i]
                    )
                    if move.is_possibly_valid():
                        possible_moves.append(move)
                except IndexError:
                    continue
        return possible_moves


class Bishop(Piece):
    piece_type = PieceTypes.bishop

    def is_valid_move(self, board: "Board", move: "Move") -> bool:
        if abs(move.end.row-move.start.row) == abs(move.end.column-move.start.column) != 0:
            i, j = 1 if move.end.row > move.start.row else - \
                1, 1 if move.end.column > move.start.column else -1
            return board.check_if_move_valid(move, i, j)
        return False

    def get_all_possible_moves(self, board: "Board", position: "Position") -> List["Move"]:
        moves = []
        for i in [1, -1]:
            for j in [1, -1]:
                for move in board.get_all_possible_moves_in_given_dir(position, i, j):
                    if move.is_possibly_valid():
                        moves.append(move)
        return move


class Queen(Piece):
    piece_type = PieceTypes.queen

    def is_valid_move(self, board: "Board", move: "Move") -> bool:
        if abs(move.end.row-move.start.row) == abs(move.end.column-move.start.column) != 0:
            i, j = 1 if move.end.row > move.start.row else - \
                1, 1 if move.end.column > move.start.column else -1
            return board.check_if_move_valid(move, i, j)
        elif abs(move.end.row-move.start.row) != 0 and abs(move.end.column-move.start.column) != 0:
            return False
        elif abs(move.end.row-move.start.row) == 0 and abs(move.end.column-move.start.column) == 0:
            rowdel, coldel = move.end.row - move.start.row, move.end.column - move.start.column
            if rowdel == 0:
                i = 0
            if rowdel < 0:
                i = -1
            if rowdel > 0:
                i = 1
            if coldel == 0:
                j = 0
            if coldel < 0:
                j = -1
            if coldel > 0:
                j = 1
            return board.check_if_move_valid(move, i, j)
        return False

    def get_all_possible_moves(self, board: "Board", position: "Position") -> List["Move"]:
        moves = []
        for i in [1, -1, 0]:
            for j in [1, -1, 0]:
                if i == 0 and j == 0:
                    continue
                for move in board.get_all_possible_moves_in_given_dir(position, i, j):
                    if move.is_possibly_valid():
                        moves.append(move)
        return move


class Rook(Piece):
    piece_type = PieceTypes.rook

    def __init__(self, color: Color) -> None:
        super().__init__(color)
        self.has_moved = False

    def is_valid_move(self, board: "Board", move: "Move") -> bool:
        if not move.is_castle:
            if abs(move.end.row-move.start.row) == 0 and abs(move.end.column-move.start.column) == 0:
                rowdel, coldel = move.end.row - move.start.row, move.end.column - move.start.column
                if rowdel == 0:
                    i = 0
                if rowdel < 0:
                    i = -1
                if rowdel > 0:
                    i = 1
                if coldel == 0:
                    j = 0
                if coldel < 0:
                    j = -1
                if coldel > 0:
                    j = 1
                return board.check_if_move_valid(move, i, j)
            return False
        else:
            if move.start.piece.can_castle(board, move.start) and move.start1.piece.can_castle(board, move.start1):
                return not move.can_result_in_check_of_own_king(board)
            return False

    def can_castle(self, board: "Board", position: "Position") -> bool:
        if not self.has_moved:
            king_position = board.get_king_position(self.color)
            king: King = king_position.piece
            if not king.can_castle(board, king_position):
                return False
            i = 1 if position.column > king_position.column else -1
            col = king_position.column
            positions_should_not_be_under_attack = []
            for _ in range(3):
                positions_should_not_be_under_attack.append(board.positions[position.row][col])
                col += i
            for pos in positions_should_not_be_under_attack:
                if pos.piece is not None:
                    return False
            if board.are_positions_under_attack(positions_should_not_be_under_attack):
                return False
            return True
        return False

    def get_all_possible_moves(self, board: "Board", position: "Position") -> List["Move"]:
        moves = []
        for i, j in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
            for move in board.get_all_possible_moves_in_given_dir(position, i, j):
                if move.is_possibly_valid(): moves.append(move)
        if self.can_castle(board, position):
            king_pos = board.get_king_position(self.color)
            i = 1 if position.column > king_pos.column else -1
            moves.append(
                Move(
                    position,
                    board.positions[king_pos.row][king_pos.column+i],
                    True, 
                    king_pos,
                    board.positions[king_pos.row][king_pos.column+2*i]
                )
            )
        return moves
    
    def move(self, board: "Board", move: "Move") -> None:
        if not move.is_castle:
            super().move(board, move)
            self.has_moved = True
        else:
            if not self.is_valid_move(board, move):
                raise ValueError("Invalid Move.")
            board.positions[move.start.row][move.end.column].update(board, None)
            board.positions[move.end.row][move.end.column].update(board, move.start.piece)
            board.positions[move.start1.row][move.end1.column].update(board, None)
            board.positions[move.end1.row][move.end1.column].update(board, move.start1.piece)
            move.clone_positions()
            board.positions[move.end.row][move.end.column].piece.has_moved = True
            board.positions[move.end1.row][move.end1.column].piece.has_moved = True

class King(Piece):
    piece_type = PieceTypes.king

    def __init__(self, color: Color) -> None:
        super().__init__(color)
        self.has_moved = False
        self.has_been_checked = False

    def can_castle(self, board: "Board", position: "Position") -> bool:
        return not self.has_moved and not self.has_been_checked
    
    def is_valid_move(self, board: "Board", move: "Move") -> bool:
        if not move.is_castle:
            if abs(move.end.row-move.start.row) <= 1 and abs(move.end.column-move.start.column) <= 1:
                return board.check_if_move_valid(move, move.end.row, move.end.column)
            return False
        else:
            if move.start.piece.can_castle(board, move.start) and move.start1.piece.can_castle(board, move.start1):
                return not move.can_result_in_check_of_own_king(board)
            return False
    
    def get_all_possible_moves(self, board: "Board", position: "Position") -> List["Move"]:
        moves = []
        row = position.row
        col = position.column
        for i, j in [(1, 0), (1, 1), (1, -1), (0, 1), (0, -1), (-1, 0), (-1, -1), (-1, 1)]:
            if 0 <= row+i <= 7 and 0 <= col+j <= 7:
                move = Move(
                    position,
                    board.positions[row+i][col+j]
                )
                if move.is_possibly_valid():
                    moves.append(move)

        if self.can_castle:
            initial_rook_positions = [(0, 0), (0, 7)] if self.color == Color.white else [(7, 0), (7, 7)]
            for (x, y) in initial_rook_positions:
                rook_pos = board.positions[x][y]
                if rook_pos.piece is None or rook_pos.piece.piece_type != PieceTypes.rook:
                    continue
                if rook_pos.piece.has_moved or not rook_pos.piece.can_castle(board, rook_pos):
                    continue
                i = 1 if position.column < rook_pos.column else -1
                moves.append(
                    Move(
                        position,
                        board.positions[position.row][position.column+2*i],
                        True, 
                        rook_pos,
                        board.positions[position.row][position.column+i]
                    )
                )
                if move.is_possibly_valid(): moves.append(move)
        return moves
    
    def move(self, board: "Board", move: "Move") -> None:
        if not move.is_castle:
            super().move(board, move)
            self.has_moved = True
        else:
            if not self.is_valid_move(board, move):
                raise ValueError("Invalid Move.")
            board.positions[move.start.row][move.end.column].update(board, None)
            board.positions[move.end.row][move.end.column].update(board, move.start.piece)
            board.positions[move.start1.row][move.end1.column].update(board, None)
            board.positions[move.end1.row][move.end1.column].update(board, move.start1.piece)
            move.clone_positions()
            board.positions[move.end.row][move.end.column].piece.has_moved = True
            board.positions[move.end1.row][move.end1.column].piece.has_moved = True

class PieceFactory:
    @classmethod
    def create_piece(cls, piece: PieceTypes, color: Color) -> Piece:
        if piece == PieceTypes.pawn:
            return Pawn(color)
        if piece == PieceTypes.rook:
            return Rook(color)
        if piece == PieceTypes.knight:
            return Knight(color)
        if piece == PieceTypes.bishop:
            return Bishop(color)
        if piece == PieceTypes.king:
            return King(color)
        if piece == PieceTypes.queen:
            return Queen(color)


class Position:
    '''
    Could have made a simple dataclass but making it a class gives opportunity 
    to define further functions if needed.
    '''

    def __init__(
        self, row: int, column: int, color: Color, piece: Optional[Piece] = None
    ) -> None:
        '''
        x, y must be integers from 0 to 7.
        '''
        if row not in [0, 1, 2, 3, 4, 5, 6, 7] or column not in [0, 1, 2, 3, 4, 5, 6, 7]:
            raise ValueError(
                "x and y must be an integer between 0 to 7 (inclusive both)")
        self.row = row
        self.column = column
        self.piece = piece
        self.color = color

    def update(self, board: "Board", piece: Optional[Piece] = None, en_passant_capture: bool = False) -> None:
        self.piece = piece
        if self.piece.piece_type == PieceTypes.king:
            board.king_positions[self.piece.color] = self

    def clone(self) -> "Position":
        '''Clone the position.'''
        return self.clone()


class Board:
    def __init__(self, white_player: "Player", black_player: "Player"):
        self.positions: List[List[Optional[Position]]] = [
            [None for _ in range(8)] for _ in range(8)]

        self.positions[0] = [
            Position(0, 0, Color.black, PieceFactory.create_piece(
                PieceTypes.rook, Color.white)),
            Position(0, 1, Color.white, PieceFactory.create_piece(
                PieceTypes.knight, Color.white)),
            Position(0, 2, Color.black, PieceFactory.create_piece(
                PieceTypes.bishop, Color.white)),
            Position(0, 3, Color.white, PieceFactory.create_piece(
                PieceTypes.queen, Color.white)),
            Position(0, 4, Color.black, PieceFactory.create_piece(
                PieceTypes.king, Color.white)),
            Position(0, 5, Color.white, PieceFactory.create_piece(
                PieceTypes.bishop, Color.white)),
            Position(0, 6, Color.black, PieceFactory.create_piece(
                PieceTypes.knight, Color.white)),
            Position(0, 7, Color.white, PieceFactory.create_piece(
                PieceTypes.rook, Color.white)),
        ]
        self.positions[7] = [
            Position(7, 0, Color.white, PieceFactory.create_piece(
                PieceTypes.rook, Color.black)),
            Position(7, 1, Color.black, PieceFactory.create_piece(
                PieceTypes.knight, Color.black)),
            Position(7, 2, Color.white, PieceFactory.create_piece(
                PieceTypes.bishop, Color.black)),
            Position(7, 3, Color.black, PieceFactory.create_piece(
                PieceTypes.queen, Color.black)),
            Position(7, 4, Color.white, PieceFactory.create_piece(
                PieceTypes.king, Color.black)),
            Position(7, 5, Color.black, PieceFactory.create_piece(
                PieceTypes.bishop, Color.black)),
            Position(7, 6, Color.white, PieceFactory.create_piece(
                PieceTypes.knight, Color.black)),
            Position(7, 7, Color.black, PieceFactory.create_piece(
                PieceTypes.rook, Color.black)),
        ]
        cnt_color = Color.white
        for i in range(1, 7):
            for j in range(8):
                if i == 1:
                    self.positions[i][j] = Position(
                        i, j, cnt_color, PieceFactory.create_piece(
                            PieceTypes.pawn, Color.white)
                    )
                elif i == 6:
                    self.positions[i][j] = Position(
                        i, j, cnt_color, PieceFactory.create_piece(
                            PieceTypes.pawn, Color.black)
                    )
                else:
                    self.positions[i][j] = Position(
                        i, j, cnt_color, None
                    )
                cnt_color = revert_color(cnt_color)
            cnt_color = revert_color(cnt_color)

        self.king_positions = {
            Color.white: self.positions[0][4], Color.black: self.positions[7][4]}
        self.white = white_player
        self.black = black_player
        self._last_move = None

    def are_positions_under_attack(self, positions: List["Position"], color: "Color") -> bool:
        '''Check if any of given positions under attack by pieces of given color.'''
        coords = [(pos.row, pos.col) for pos in positions]
        for i in range(8):
            for j in range(8):
                cntpos = self.positions[i][j]
                if cntpos.piece is not None and cntpos.piece.color != color:
                    if cntpos.piece.piece_type != PieceTypes.pawn:
                        for move in cntpos.piece.get_all_possible_moves(self, cntpos):
                            if (move.end.row, move.end.column) in coords:
                                return True
                    else:
                        if color == Color.white:
                            if (cntpos.row+1, cntpos.column+1) in coords or (cntpos.row+1, cntpos.column-1) in coords:
                                return True
                        else:
                            if (cntpos.row-1, cntpos.column+1) in coords or (cntpos.row-1, cntpos.column-1) in coords:
                                return True
        return False

    def is_king_in_check(self, color: Color) -> bool:
        '''Checks if given color king is in check.'''
        king_pos = self.king_positions[color]
        return self.are_positions_under_attack(positions=[king_pos], color = revert_color(color))

    def clone(self) -> "Board":
        return deepcopy(self)

    def get_last_move(self) -> "Union[Move, None]":
        return self._last_move

    def get_king_position(self, color:"Color") -> Position:
        return self.king_positions[color]

    def get_all_possible_moves_in_given_dir(self, position: "Position", i: int, j: int) -> List["Move"]:
        if i < -1 or i > 1 or j < -1 or j > 1:
            raise ValueError("Invalid Value of i and j.")
        cntrow = position.row
        cntcol = position.column
        cntrow += i
        cntcol += j
        moves = []
        while True:
            if 0 <= cntrow <= 7 and 0 <= cntcol <= 7:
                cntpos = self.positions[cntrow][cntcol]
                moves.append(Move(position, cntpos))
                if cntpos.piece is not None:
                    break
            else:
                break
        return moves

    def check_if_move_valid(self, move: "Move", i: int, j: int) -> bool:
        if i < -1 or i > 1 or j < -1 or j > 1:
            raise ValueError("Invalid Value of i and j.")
        i, j = 1 if move.end.row > move.start.row else - \
            1, 1 if move.end.column > move.start.column else -1
        row, col = move.start.row, move.start.column
        row += i
        col += j
        while row != move.end.row and col != move.end.column:
            if self.positions[row][col].piece is not None:
                return False
            row += i
            col += j
        if not move.can_result_in_check_of_own_king(self):
            return True
        return False


class Move:
    def __init__(
        self,
        start: Position,
        end: Position,
        is_castle=False,
        start1: Optional[Position] = None,
        end1: Optional[Position] = None
    ) -> None:
        if is_castle and (start1 is None or end1 is None):
            raise ValueError(
                "In case of castling, start1 and end1 must be given.")
        if not is_castle and (start1 is not None or end1 is not None):
            raise ValueError(
                "in case of simple move, start1 and end1 need not be given.")
        self.start = start
        self.end = end
        self.is_castle = is_castle
        self.start1 = start1
        self.end1 = end1

    def is_possibly_valid(self) -> bool:
        if self.start.piece is None or (
            self.end.piece is not None and self.end.piece.color==self.start.piece.color
        ):
            return False
        if self.is_castle and self.start1.piece is None or self.end1.piece is not None or \
            {self.start.piece.piece_type, self.start1.piece.piece_type} != {PieceTypes.rook, PieceTypes.king}\
                or self.start.piece.color != self.start1.piece.color:
            return False
        return True

    def clone_positions(self) -> None:
        '''Clones the pieces saved in the positions and saves them in the self.'''
        self.start = self.start.clone()
        self.end = self.end.clone()
        self.start1 = self.start1.clone() if self.start1 is not None else None
        self.end1 = self.end1.clone() if self.end1 is not None else None

    def can_result_in_check_of_own_king(self, board: "Board") -> bool:
        temp_board = board.clone()
        return temp_board.is_king_in_check(color=self.start.piece.color)


class MoveObserver:
    def __init__(self):
        self._moves = []

    def add(self, move: Move) -> None:
        self._moves.append(move)


class Chess:
    def __init__(self, player1_name: str, player2_name: str) -> None:
        self.white = Player(player1_name, Color.white)
        self.black = Player(player2_name, Color.black)
        self.turn = Color.white
        self.board = Board(self.white, self.black)
        self.move_observer = MoveObserver()

    def _change_turn(self):
        self.turn = revert_color(self.turn)

    def _verify_coord(self, coords: List[int]) -> None:
        for c in coords:
            if c<0 or c>7:
                raise ValueError("Wrong Coordinates.")
        
    def _get_pos(self, x: int, y: int) -> Position:
        return self.board.positions[x][y]

    def get_all_possible_moves(self, x: int, y: int) -> List[Move]:
        '''x and y considering left corner of white as 0, 0'''
        self._verify_coord([x, y])
        position = self._get_pos(x, y)
        if position.piece is None or position.piece.color != self.turn:
            raise ValueError("Only the player with his turn can access this function.")
        return position.piece.get_all_possible_moves(self.board, position)
    
    def move(self, move: Move) -> None:
        if move.start.piece is None or move.start.piece.color != self.turn or not move.is_possibly_valid:
            raise ValueError("Only player with current turn can move.")
        move.start.piece.move(self.board, move)
        self._change_turn()
        if self.board.is_king_in_check(self.turn):
            self.board.king_positions[self.turn].has_been_checked = True
        self.move_observer.add(move)