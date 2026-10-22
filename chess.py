import tkinter as tk
from tkinter import messagebox, ttk
import copy
import time
import random
from collections import Counter

# ============ CONSTANTS ============
BOARD_SIZE = 8
SQUARE_SIZE = 75
BOARD_PIXELS = BOARD_SIZE * SQUARE_SIZE

LIGHT_COLOR = "#F0D9B5"
DARK_COLOR = "#B58863"
SELECTED_COLOR = "#3FA34D"
VALID_MOVE_COLOR = "#A9D18E"
CAPTURE_COLOR = "#E8A0A0"
LAST_MOVE_COLOR = "#F5E6A8"
CHECK_COLOR = "#FF6B6B"
HINT_COLOR = "#87CEEB"
WHITE_PIECE_OUTLINE = "#1a1a1a"
BLACK_PIECE_OUTLINE = "#f0f0f0"

PIECE_UNICODE = {
    'wK': '♔', 'wQ': '♕', 'wR': '♖', 'wB': '♗', 'wN': '♘', 'wP': '♙',
    'bK': '♚', 'bQ': '♛', 'bR': '♜', 'bB': '♝', 'bN': '♞', 'bP': '♟'
}


# ============ PIECE MOVEMENT LOGIC ============
def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def clone_board(board):
    return [row[:] for row in board]


def initial_board():
    board = [[None] * 8 for _ in range(8)]
    order = ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
    for c in range(8):
        board[0][c] = 'b' + order[c]
        board[1][c] = 'bP'
        board[6][c] = 'wP'
        board[7][c] = 'w' + order[c]
    return board


def find_king(board, color):
    for r in range(8):
        for c in range(8):
            if board[r][c] == color + 'K':
                return (r, c)
    return None


def is_attacked(board, r, c, by_color):
    pr = r + 1 if by_color == 'w' else r - 1
    for dc in (-1, 1):
        if in_bounds(pr, c + dc) and board[pr][c + dc] == by_color + 'P':
            return True
    for dr, dc in [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]:
        nr, nc = r + dr, c + dc
        if in_bounds(nr, nc) and board[nr][nc] == by_color + 'N':
            return True
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and board[nr][nc] == by_color + 'K':
                return True
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        while in_bounds(nr, nc):
            p = board[nr][nc]
            if p is not None:
                if p[0] == by_color and p[1] in ('R', 'Q'):
                    return True
                break
            nr += dr
            nc += dc
    for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        nr, nc = r + dr, c + dc
        while in_bounds(nr, nc):
            p = board[nr][nc]
            if p is not None:
                if p[0] == by_color and p[1] in ('B', 'Q'):
                    return True
                break
            nr += dr
            nc += dc
    return False


def is_in_check(board, color):
    k = find_king(board, color)
    if k is None:
        return False
    opp = 'b' if color == 'w' else 'w'
    return is_attacked(board, k[0], k[1], opp)


def pseudo_moves(board, r, c, castling_rights=None, en_passant=None):
    piece = board[r][c]
    if piece is None:
        return []
    color = piece[0]
    kind = piece[1]
    moves = []
    opp = 'b' if color == 'w' else 'w'

    def add(tr, tc, special=None):
        if not in_bounds(tr, tc):
            return
        target = board[tr][tc]
        if target is not None and target[0] == color:
            return
        moves.append((tr, tc, special))

    if kind == 'P':
        direction = -1 if color == 'w' else 1
        start_row = 6 if color == 'w' else 1
        promo_row = 0 if color == 'w' else 7
        nr = r + direction
        if in_bounds(nr, c) and board[nr][c] is None:
            if nr == promo_row:
                for p in ('Q', 'R', 'B', 'N'):
                    moves.append((nr, c, 'promo' + p))
            else:
                add(nr, c)
            if r == start_row and board[r + 2 * direction][c] is None:
                add(r + 2 * direction, c, 'double')
        for dc in (-1, 1):
            nc = c + dc
            if in_bounds(nr, nc):
                target = board[nr][nc]
                if target is not None and target[0] == opp:
                    if nr == promo_row:
                        for p in ('Q', 'R', 'B', 'N'):
                            moves.append((nr, nc, 'promo' + p))
                    else:
                        add(nr, nc)
                elif en_passant is not None and en_passant == (nr, nc):
                    add(nr, nc, 'ep')

    elif kind == 'N':
        for dr, dc in [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                       (1, -2), (1, 2), (2, -1), (2, 1)]:
            add(r + dr, c + dc)

    elif kind == 'B':
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            nr, nc = r + dr, c + dc
            while in_bounds(nr, nc):
                target = board[nr][nc]
                if target is None:
                    moves.append((nr, nc, None))
                else:
                    if target[0] == opp:
                        moves.append((nr, nc, None))
                    break
                nr += dr
                nc += dc

    elif kind == 'R':
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            while in_bounds(nr, nc):
                target = board[nr][nc]
                if target is None:
                    moves.append((nr, nc, None))
                else:
                    if target[0] == opp:
                        moves.append((nr, nc, None))
                    break
                nr += dr
                nc += dc

    elif kind == 'Q':
        for dr, dc in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1),
                       (1, -1), (1, 0), (1, 1)]:
            nr, nc = r + dr, c + dc
            while in_bounds(nr, nc):
                target = board[nr][nc]
                if target is None:
                    moves.append((nr, nc, None))
                else:
                    if target[0] == opp:
                        moves.append((nr, nc, None))
                    break
                nr += dr
                nc += dc

    elif kind == 'K':
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                add(r + dr, c + dc)
        if castling_rights:
            row = 7 if color == 'w' else 0
            if r == row and c == 4:
                if castling_rights.get(color + 'K') and board[row][5] is None and board[row][6] is None:
                    if not is_attacked(board, row, 4, opp) and not is_attacked(board, row, 5, opp) and not is_attacked(board, row, 6, opp):
                        moves.append((row, 6, 'castleK'))
                if castling_rights.get(color + 'Q') and board[row][3] is None and board[row][2] is None and board[row][1] is None:
                    if not is_attacked(board, row, 4, opp) and not is_attacked(board, row, 3, opp) and not is_attacked(board, row, 2, opp):
                        moves.append((row, 2, 'castleQ'))
    return moves


def legal_moves(board, r, c, castling_rights=None, en_passant=None):
    piece = board[r][c]
    if piece is None:
        return []
    color = piece[0]
    result = []
    for (tr, tc, special) in pseudo_moves(board, r, c, castling_rights, en_passant):
        nb = clone_board(board)
        nb[tr][tc] = nb[r][c]
        nb[r][c] = None
        if special == 'ep':
            cap_r = tr + (1 if color == 'w' else -1)
            nb[cap_r][tc] = None
        if special == 'castleK':
            nb[tr][5] = nb[tr][7]
            nb[tr][7] = None
        if special == 'castleQ':
            nb[tr][3] = nb[tr][0]
            nb[tr][0] = None
        if special and special.startswith('promo'):
            nb[tr][tc] = color + special[5]
        if not is_in_check(nb, color):
            result.append((tr, tc, special))
    return result


def all_legal_moves(board, color, castling_rights, en_passant):
    moves = []
    for r in range(8):
        for c in range(8):
            if board[r][c] and board[r][c][0] == color:
                for m in legal_moves(board, r, c, castling_rights, en_passant):
                    moves.append((r, c, m[0], m[1], m[2]))
    return moves


def has_any_legal_move(board, color, castling_rights, en_passant):
    for r in range(8):
        for c in range(8):
            if board[r][c] and board[r][c][0] == color:
                if legal_moves(board, r, c, castling_rights, en_passant):
                    return True
    return False


# ============ AI ENGINE ============
PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

PAWN_TABLE = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [5, 5, 10, 25, 25, 10, 5, 5],
    [0, 0, 0, 20, 20, 0, 0, 0],
    [5, -5, -10, 0, 0, -10, -5, 5],
    [5, 10, 10, -20, -20, 10, 10, 5],
    [0, 0, 0, 0, 0, 0, 0, 0],
]
KNIGHT_TABLE = [
    [-50, -40, -30, -30, -30, -30, -40, -50],
    [-40, -20, 0, 0, 0, 0, -20, -40],
    [-30, 0, 10, 15, 15, 10, 0, -30],
    [-30, 5, 15, 20, 20, 15, 5, -30],
    [-30, 0, 15, 20, 20, 15, 0, -30],
    [-30, 5, 10, 15, 15, 10, 5, -30],
    [-40, -20, 0, 5, 5, 0, -20, -40],
    [-50, -40, -30, -30, -30, -30, -40, -50],
]
BISHOP_TABLE = [
    [-20, -10, -10, -10, -10, -10, -10, -20],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-10, 0, 5, 10, 10, 5, 0, -10],
    [-10, 5, 5, 10, 10, 5, 5, -10],
    [-10, 0, 10, 10, 10, 10, 0, -10],
    [-10, 10, 10, 10, 10, 10, 10, -10],
    [-10, 5, 0, 0, 0, 0, 5, -10],
    [-20, -10, -10, -10, -10, -10, -10, -20],
]
ROOK_TABLE = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [5, 10, 10, 10, 10, 10, 10, 5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [0, 0, 0, 5, 5, 0, 0, 0],
]
QUEEN_TABLE = [
    [-20, -10, -10, -5, -5, -10, -10, -20],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-10, 0, 5, 5, 5, 5, 0, -10],
    [-5, 0, 5, 5, 5, 5, 0, -5],
    [0, 0, 5, 5, 5, 5, 0, -5],
    [-10, 5, 5, 5, 5, 5, 0, -10],
    [-10, 0, 5, 0, 0, 0, 0, -10],
    [-20, -10, -10, -5, -5, -10, -10, -20],
]
KING_TABLE = [
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-20, -30, -30, -40, -40, -30, -30, -20],
    [-10, -20, -20, -20, -20, -20, -20, -10],
    [20, 20, 0, 0, 0, 0, 20, 20],
    [20, 30, 10, 0, 0, 10, 30, 20],
]
TABLES = {'P': PAWN_TABLE, 'N': KNIGHT_TABLE, 'B': BISHOP_TABLE,
          'R': ROOK_TABLE, 'Q': QUEEN_TABLE, 'K': KING_TABLE}


def evaluate(board):
    score = 0
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p is None:
                continue
            color = p[0]
            kind = p[1]
            val = PIECE_VALUES[kind]
            table = TABLES[kind]
            if color == 'w':
                val += table[r][c]
                score += val
            else:
                val += table[7 - r][c]
                score -= val
    return score


def make_move(board, fr, fc, tr, tc, special, castling_rights, en_passant):
    piece = board[fr][fc]
    color = piece[0]
    board[tr][tc] = piece
    board[fr][fc] = None
    new_ep = None
    if special == 'ep':
        cap_r = tr + (1 if color == 'w' else -1)
        board[cap_r][tc] = None
    if special == 'double':
        new_ep = ((fr + tr) // 2, fc)
    if special == 'castleK':
        board[tr][5] = board[tr][7]
        board[tr][7] = None
    if special == 'castleQ':
        board[tr][3] = board[tr][0]
        board[tr][0] = None
    if special and special.startswith('promo'):
        board[tr][tc] = color + special[5]

    new_cr = dict(castling_rights) if castling_rights else {}
    if piece[1] == 'K':
        new_cr[color + 'K'] = False
        new_cr[color + 'Q'] = False
    if piece[1] == 'R':
        if fc == 0 and fr == (7 if color == 'w' else 0):
            new_cr[color + 'Q'] = False
        if fc == 7 and fr == (7 if color == 'w' else 0):
            new_cr[color + 'K'] = False
    if (tr, tc) == (7, 0):
        new_cr['wQ'] = False
    if (tr, tc) == (7, 7):
        new_cr['wK'] = False
    if (tr, tc) == (0, 0):
        new_cr['bQ'] = False
    if (tr, tc) == (0, 7):
        new_cr['bK'] = False
    return new_cr, new_ep


def order_moves(board, moves):
    def score(m):
        fr, fc, tr, tc, sp = m
        s = 0
        target = board[tr][tc]
        if target:
            s += 10 * PIECE_VALUES[target[1]] - PIECE_VALUES[board[fr][fc][1]]
        if sp and sp.startswith('promo'):
            s += PIECE_VALUES[sp[5]]
        return -s
    return sorted(moves, key=score)


def minimax(board, depth, alpha, beta, maximizing, castling_rights, en_passant, color_to_move):
    if depth == 0:
        return evaluate(board), None
    moves = all_legal_moves(board, color_to_move, castling_rights, en_passant)
    if not moves:
        if is_in_check(board, color_to_move):
            return (-99999 + (10 - depth)) if maximizing else (99999 - (10 - depth)), None
        return 0, None
    moves = order_moves(board, moves)
    best_move = moves[0]
    if maximizing:
        max_eval = -float('inf')
        for (fr, fc, tr, tc, sp) in moves:
            nb = clone_board(board)
            ncr, nep = make_move(nb, fr, fc, tr, tc, sp, castling_rights, en_passant)
            ev, _ = minimax(nb, depth - 1, alpha, beta, False, ncr, nep,
                            'b' if color_to_move == 'w' else 'w')
            if ev > max_eval:
                max_eval = ev
                best_move = (fr, fc, tr, tc, sp)
            alpha = max(alpha, ev)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for (fr, fc, tr, tc, sp) in moves:
            nb = clone_board(board)
            ncr, nep = make_move(nb, fr, fc, tr, tc, sp, castling_rights, en_passant)
            ev, _ = minimax(nb, depth - 1, alpha, beta, True, ncr, nep,
                            'b' if color_to_move == 'w' else 'w')
            if ev < min_eval:
                min_eval = ev
                best_move = (fr, fc, tr, tc, sp)
            beta = min(beta, ev)
            if beta <= alpha:
                break
        return min_eval, best_move


# ============ TUTORIAL DATA ============
TUTORIALS = {
    "Welcome to Chess": (
        "Chess is played on an 8x8 board between White and Black.\n\n"
        "• White always moves first.\n"
        "• Each player starts with 16 pieces.\n"
        "• The goal is to checkmate the opponent's King — put it under attack with no escape.\n\n"
        "Click on a piece to see its legal moves highlighted.\n"
        "Click a highlighted square to move.\n\n"
        "Each piece type moves differently — check the other lessons!"
    ),
    "The Pawn ♙": (
        "Pawns move forward one square.\n"
        "• From their starting row they may move two squares.\n"
        "• Pawns capture diagonally (one square forward-left or forward-right).\n"
        "• They cannot capture forward.\n"
        "• If a pawn reaches the far side, it promotes — usually to a Queen.\n\n"
        "Special: En Passant — if an enemy pawn moves two squares past yours, you can capture it as if it had moved only one."
    ),
    "The Knight ♘": (
        "Knights move in an 'L' shape: two squares in one direction, then one square perpendicular.\n\n"
        "• Knights are the only piece that can jump over others.\n"
        "• They alternate landing on light and dark squares.\n\n"
        "Try moving a knight from the starting position — see how it jumps!"
    ),
    "The Bishop ♗": (
        "Bishops move diagonally any number of squares.\n\n"
        "• Each bishop stays on its original color forever.\n"
        "• They are blocked by any piece in the way.\n"
        "• Two bishops together are very powerful — they cover all squares."
    ),
    "The Rook ♖": (
        "Rooks move horizontally or vertically any number of squares.\n\n"
        "• They are blocked by pieces in the way.\n"
        "• Rooks are very powerful on open files (columns with no pawns).\n"
        "• They participate in castling with the King."
    ),
    "The Queen ♕": (
        "The Queen is the most powerful piece.\n\n"
        "• She combines the Rook and Bishop movements: any number of squares horizontally, vertically, or diagonally.\n"
        "• Protect your Queen — losing her is usually a big disadvantage!"
    ),
    "The King ♔": (
        "The King moves one square in any direction.\n\n"
        "• The King can NEVER move into check (a square attacked by an enemy).\n"
        "• If the King is attacked, you must respond — move, block, or capture.\n"
        "• If the King has no legal escape, that's checkmate — game over!\n\n"
        "Special: Castling — King moves two squares toward a Rook, and the Rook jumps over to the other side. Only if neither has moved and squares are clear & safe."
    ),
    "Check & Checkmate": (
        "CHECK: The King is under attack but can escape.\n"
        "You must respond immediately.\n\n"
        "CHECKMATE: The King is under attack and has no legal escape.\n"
        "The game ends immediately.\n\n"
        "STALEMATE: The player to move has no legal move but is NOT in check.\n"
        "This is a draw — no winner."
    ),
    "Special Moves": (
        "1. CASTLING\n"
        "   King moves 2 squares toward a Rook; Rook jumps over.\n"
        "   Requirements: neither piece moved, squares clear, King not in/through check.\n\n"
        "2. EN PASSANT\n"
        "   Capture a pawn that just moved two squares as if it moved one.\n\n"
        "3. PROMOTION\n"
        "   A pawn reaching the far side becomes a Queen, Rook, Bishop, or Knight.\n\n"
        "Use these! They are essential at higher levels."
    ),
    "Strategy Tips": (
        "• CONTROL THE CENTER — pieces in the center are stronger.\n"
        "• DEVELOP YOUR PIECES — get knights and bishops out early.\n"
        "• KEEP YOUR KING SAFE — castle early!\n"
        "• DON'T MOVE THE SAME PIECE TWICE in the opening without reason.\n"
        "• CONNECT YOUR ROOKS — move them to open files.\n"
        "• THINK BEFORE YOU MOVE — check if a piece can be captured.\n"
        "• LOOK FOR FORKS, PINS, and DISCOVERED ATTACKS.\n\n"
        "Practice against the AI on Easy to apply what you've learned!"
    ),
}

# Extended strategy tips
EXTENDED_TIPS = [
    "🎯 PRINCIPLE OF TWO WEAKNESSES: A single weakness can be defended; two often cannot. Attack where the defender cannot cover both.",
    "🔒 THE PIN: Attack a piece that cannot move because it shields a more valuable piece. Pins win material.",
    "🍴 THE FORK: One piece attacks two or more enemy pieces simultaneously. Knights fork best.",
    "💥 THE SKEWER: Attack a valuable piece so it must move, exposing a lesser piece behind it.",
    "🪄 DISCOVERED ATTACK: Move one piece to unleash another's attack on the enemy. Very powerful.",
    "🚪 DISCOVERED CHECK: Move a piece (often with tempo) to reveal check from a queen/bishop/rook. Often wins material.",
    "🐴 KNIGHT ON THE RIM IS DIM: Knights on the edge (a/h files) cover half the squares of central knights. Keep them central.",
    "🔍 THE 7TH RANK: Rooks on the 7th rank are devastating — they attack pawns on their starting squares and trap the king.",
    "📏 ACTIVITY OVER MATERIAL: In many positions, active piece play beats a small material advantage.",
    "👑 DO NOT TRADE QUEENS BLINDLY: Keeping queens on often means more attacking chances, even when down material.",
    "🏰 PAWN STRUCTURE: Avoid doubled/isolated/backward pawns. They are permanent weaknesses.",
    "🗼 CONNECT YOUR ROOKS: Rooks on the back rank should 'see' each other — no piece between them.",
    "🧱 THE FIANCHETTO: Bishops placed on b2/g2 (or b7/g7) behind pawns control long diagonals. Often very strong.",
    "⏱️ TEMPO MATTERS: Every move should develop, attack, or defend. Don't waste moves in the opening.",
    "🚫 BLOCKADING: A passed pawn is best blockaded by a KNIGHT, not a bishop or rook — knights stand on squares pawns can't attack.",
    "🔀 OPPOSITE-SIDED CASTLING: When you and your opponent castle on opposite sides, ATTACK the enemy king with your pawns — don't waste time defending.",
    "✂️ THE EXCHANGE SACRIFICE: Trading a rook for a bishop/knight (2 pieces) is often good when it destroys the enemy pawn structure or exposes their king.",
    "🌊 THE MINORITY ATTACK: Push two pawns against three on one side to create a passed pawn later.",
    "🐘 TWO BISHOPS: The 'bishop pair' is worth ~50 extra points in an open position — avoid trading one bishop too early.",
    "🎪 BACK RANK MATE: Always watch for back-rank weakness — leave a king a flight square (luft).",
    "🛡️ PROPHYLAXIS: Prevent your opponent's plan before executing yours. A move that stops a threat is often better than one that creates a smaller threat.",
]


# ============ MAIN GAME CLASS ============
class ChessGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Chess — Learn & Play")
        self.root.configure(bg="#2b2b2b")
        self.root.resizable(False, False)

        self.board = initial_board()
        self.turn = 'w'
        self.selected = None
        self.valid_moves = []
        self.castling_rights = {'wK': True, 'wQ': True, 'bK': True, 'bQ': True}
        self.en_passant = None
        self.last_move = None
        self.difficulty = tk.StringVar(value="Easy")
        self.mode = tk.StringVar(value="vs AI")  # vs AI or Two Players
        self.competitive = tk.BooleanVar(value=False)
        self.game_over = False
        self.ai_thinking = False
        self.move_history = []
        self.piece_widgets = {}
        self.animating = False
        self.hint_move = None
        self.show_hints = tk.BooleanVar(value=True)
        self.board_history = [clone_board(self.board)]

        # Competitive mode timing
        self.white_time = 0.0
        self.black_time = 0.0
        self.turn_start = None
        self.move_times = []  # list of (color, notation, seconds)
        self.timer_running = False

        self.build_ui()
        self.draw_board()
        self.update_status()
        self.start_turn_clock()

    # ----- UI BUILD -----
    def build_ui(self):
        main = tk.Frame(self.root, bg="#2b2b2b")
        main.pack(padx=10, pady=10)

        left = tk.Frame(main, bg="#2b2b2b")
        left.pack(side=tk.LEFT, padx=(0, 10))

        # Top bar
        topbar = tk.Frame(left, bg="#2b2b2b")
        topbar.pack(fill=tk.X, pady=(0, 6))
        tk.Label(topbar, text="Difficulty:", bg="#2b2b2b", fg="white",
                 font=("Arial", 11, "bold")).pack(side=tk.LEFT)
        diff_menu = ttk.Combobox(topbar, textvariable=self.difficulty,
                                  values=["Easy", "Medium", "Hard"],
                                  state="readonly", width=8, font=("Arial", 10))
        diff_menu.pack(side=tk.LEFT, padx=5)

        tk.Label(topbar, text="Mode:", bg="#2b2b2b", fg="white",
                 font=("Arial", 11, "bold")).pack(side=tk.LEFT, padx=(10, 0))
        mode_menu = ttk.Combobox(topbar, textvariable=self.mode,
                                  values=["vs AI", "Two Players"],
                                  state="readonly", width=11, font=("Arial", 10))
        mode_menu.pack(side=tk.LEFT, padx=5)
        mode_menu.bind("<<ComboboxSelected>>", lambda e: self.reset_game())

        tk.Button(topbar, text="↩ Undo", command=self.undo_move,
                  bg="#555", fg="white", font=("Arial", 10), relief=tk.FLAT,
                  padx=8).pack(side=tk.RIGHT, padx=2)
        tk.Button(topbar, text="🔄 New Game", command=self.reset_game,
                  bg="#4a7a4a", fg="white", font=("Arial", 10, "bold"),
                  relief=tk.FLAT, padx=8).pack(side=tk.RIGHT, padx=2)

        # Clock panel (competitive)
        clock_frame = tk.Frame(left, bg="#1e1e1e", bd=0)
        clock_frame.pack(fill=tk.X, pady=(0, 6))

        self.white_clock_label = tk.Label(clock_frame, text="⬜ White: 00:00.0",
                                           bg="#1e1e1e", fg="#ffffff",
                                           font=("Consolas", 14, "bold"), anchor=tk.W,
                                           padx=10, pady=4)
        self.white_clock_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.black_clock_label = tk.Label(clock_frame, text="⬛ Black: 00:00.0",
                                           bg="#1e1e1e", fg="#bbbbbb",
                                           font=("Consolas", 14, "bold"), anchor=tk.E,
                                           padx=10, pady=4)
        self.black_clock_label.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        # Board canvas
        self.canvas = tk.Canvas(left, width=BOARD_PIXELS, height=BOARD_PIXELS,
                                 highlightthickness=0, bg=DARK_COLOR)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_click)

        # Status bar
        self.status_label = tk.Label(left, text="", bg="#2b2b2b", fg="white",
                                      font=("Arial", 12, "bold"), pady=8)
        self.status_label.pack()

        # Right panel
        right = tk.Frame(main, bg="#2b2b2b")
        right.pack(side=tk.LEFT, fill=tk.BOTH)

        tk.Button(right, text="📖 Tutorials & Lessons", command=self.open_tutorials,
                  bg="#4a6fa5", fg="white", font=("Arial", 11, "bold"),
                  relief=tk.FLAT, pady=6).pack(fill=tk.X, pady=(0, 4))

        tk.Checkbutton(right, text="Show move hints", variable=self.show_hints,
                       bg="#2b2b2b", fg="white", selectcolor="#444",
                       activebackground="#2b2b2b", activeforeground="white",
                       font=("Arial", 10)).pack(anchor=tk.W, pady=2)

        tk.Checkbutton(right, text="⏱ Competitive timer", variable=self.competitive,
                       command=self.toggle_competitive,
                       bg="#2b2b2b", fg="white", selectcolor="#444",
                       activebackground="#2b2b2b", activeforeground="white",
                       font=("Arial", 10)).pack(anchor=tk.W, pady=2)

        tk.Button(right, text="💡 Show best move", command=self.show_best_move,
                  bg="#7a6a3a", fg="white", font=("Arial", 10),
                  relief=tk.FLAT, pady=4).pack(fill=tk.X, pady=4)

        tk.Button(right, text="🧠 Random Strategy Tip", command=self.show_random_tip,
                  bg="#5a3a7a", fg="white", font=("Arial", 10),
                  relief=tk.FLAT, pady=4).pack(fill=tk.X, pady=(0, 4))

        # Move history with times
        tk.Label(right, text="Move History", bg="#2b2b2b", fg="#ddd",
                 font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=(10, 2))
        hist_frame = tk.Frame(right, bg="#1e1e1e")
        hist_frame.pack(fill=tk.BOTH, expand=True)
        self.history_listbox = tk.Listbox(hist_frame, bg="#1e1e1e", fg="#eee",
                                           font=("Consolas", 9), width=28,
                                           height=16, borderwidth=0,
                                           highlightthickness=0)
        scroll = tk.Scrollbar(hist_frame, command=self.history_listbox.yview)
        self.history_listbox.config(yscrollcommand=scroll.set)
        self.history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Captured pieces
        self.captured_label = tk.Label(right, text="", bg="#2b2b2b", fg="#ccc",
                                        font=("Arial", 11), justify=tk.LEFT,
                                        wraplength=200)
        self.captured_label.pack(anchor=tk.W, pady=6)

    # ----- COMPETITIVE TIMER -----
    def toggle_competitive(self):
        if self.competitive.get():
            self.white_time = 0.0
            self.black_time = 0.0
            self.turn_start = time.time()
            self.timer_running = True
            self.update_clock_display()
        else:
            self.timer_running = False
            self.white_clock_label.config(text="⬜ White: --:--.-")
            self.black_clock_label.config(text="⬛ Black: --:--.-")

    def start_turn_clock(self):
        if self.competitive.get():
            self.turn_start = time.time()
            self.timer_running = True

    def _tick_clock(self):
        if not self.timer_running or self.game_over:
            return
        now = time.time()
        elapsed = now - self.turn_start if self.turn_start else 0
        wt = self.white_time + (elapsed if self.turn == 'w' else 0)
        bt = self.black_time + (elapsed if self.turn == 'b' else 0)
        self.white_clock_label.config(
            text=f"⬜ White: {self._fmt_time(wt)}",
            fg="#7CFC00" if self.turn == 'w' else "#888")
        self.black_clock_label.config(
            text=f"⬛ Black: {self._fmt_time(bt)}",
            fg="#7CFC00" if self.turn == 'b' else "#888")
        self.root.after(100, self._tick_clock)

    @staticmethod
    def _fmt_time(sec):
        m = int(sec // 60)
        s = sec - m * 60
        return f"{m:02d}:{s:04.1f}"

    def update_clock_display(self):
        if self.competitive.get():
            self.white_clock_label.config(text=f"⬜ White: {self._fmt_time(self.white_time)}")
            self.black_clock_label.config(text=f"⬛ Black: {self._fmt_time(self.black_time)}")
            if not hasattr(self, '_ticking'):
                self._ticking = True
                self._tick_clock()

    def _commit_turn_time(self):
        """Add elapsed time on current turn to the right player."""
        if self.competitive.get() and self.turn_start is not None:
            elapsed = time.time() - self.turn_start
            if self.turn == 'w':
                self.white_time += elapsed
            else:
                self.black_time += elapsed
            self.turn_start = time.time()

    # ----- BOARD DRAWING -----
    def draw_board(self):
        self.canvas.delete("all")

        last_squares = set()
        if self.last_move:
            fr, fc, tr, tc = self.last_move
            last_squares = {(fr, fc), (tr, tc)}

        check_king = None
        if is_in_check(self.board, self.turn):
            check_king = find_king(self.board, self.turn)

        hint_sq = set()
        if self.hint_move:
            hint_sq = {(self.hint_move[0], self.hint_move[1]),
                       (self.hint_move[2], self.hint_move[3])}

        for r in range(8):
            for c in range(8):
                x0 = c * SQUARE_SIZE
                y0 = r * SQUARE_SIZE
                x1 = x0 + SQUARE_SIZE
                y1 = y0 + SQUARE_SIZE
                base = LIGHT_COLOR if (r + c) % 2 == 0 else DARK_COLOR
                if (r, c) in last_squares:
                    base = LAST_MOVE_COLOR
                if check_king == (r, c):
                    base = CHECK_COLOR
                if (r, c) in hint_sq:
                    base = HINT_COLOR
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=base, outline="")

        # Coordinates
        for i in range(8):
            self.canvas.create_text(i * SQUARE_SIZE + 6, BOARD_PIXELS - 6,
                                     text=chr(ord('a') + i), fill="#333",
                                     font=("Arial", 9, "bold"), anchor=tk.SW)
            self.canvas.create_text(6, i * SQUARE_SIZE + 6,
                                     text=str(8 - i), fill="#333",
                                     font=("Arial", 9, "bold"), anchor=tk.NW)

        if self.selected:
            r, c = self.selected
            self.canvas.create_rectangle(c * SQUARE_SIZE, r * SQUARE_SIZE,
                                          (c + 1) * SQUARE_SIZE, (r + 1) * SQUARE_SIZE,
                                          outline=SELECTED_COLOR, width=4)

        for (tr, tc, special) in self.valid_moves:
            x = tc * SQUARE_SIZE
            y = tr * SQUARE_SIZE
            target = self.board[tr][tc]
            if target is not None or special == 'ep':
                self.canvas.create_oval(x + 6, y + 6, x + SQUARE_SIZE - 6,
                                         y + SQUARE_SIZE - 6,
                                         outline=CAPTURE_COLOR, width=4)
            else:
                cx = x + SQUARE_SIZE // 2
                cy = y + SQUARE_SIZE // 2
                self.canvas.create_oval(cx - 10, cy - 10, cx + 10, cy + 10,
                                         fill=VALID_MOVE_COLOR, outline="")

        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p is not None:
                    self._draw_piece(r, c, p)

    def _draw_piece(self, r, c, piece, offset_x=0, offset_y=0, tag="piece"):
        cx = c * SQUARE_SIZE + SQUARE_SIZE // 2 + offset_x
        cy = r * SQUARE_SIZE + SQUARE_SIZE // 2 + offset_y
        # White pieces: light fill + black outline
        # Black pieces: dark fill + light outline
        if piece[0] == 'w':
            fill = "#FFFFFF"
            outline = WHITE_PIECE_OUTLINE
            width = 2
        else:
            fill = "#1a1a1a"
            outline = BLACK_PIECE_OUTLINE
            width = 1.5
        piece_tag = f"{tag}_{r}_{c}"
        self.canvas.create_text(cx, cy, text=PIECE_UNICODE[piece],
                                 font=("Arial", 42, "bold"),
                                 fill=fill, tags=(piece_tag, tag, "piece"))
        # Outline via secondary text offset (hack for outline on unicode glyph)
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            self.canvas.create_text(cx + dx, cy + dy, text=PIECE_UNICODE[piece],
                                     font=("Arial", 42, "bold"),
                                     fill=outline, tags=(piece_tag, tag, "piece"))
        # Redraw fill on top so the outline sits behind
        self.canvas.create_text(cx, cy, text=PIECE_UNICODE[piece],
                                 font=("Arial", 42, "bold"),
                                 fill=fill, tags=(piece_tag, tag, "piece"))
        self.piece_widgets[(r, c)] = piece_tag

    # ----- CLICK HANDLING -----
    def on_click(self, event):
        if self.game_over or self.animating or self.ai_thinking:
            return
        # In AI mode, only White plays
        if self.mode.get() == "vs AI" and self.turn != 'w':
            return
        c = event.x // SQUARE_SIZE
        r = event.y // SQUARE_SIZE
        if not in_bounds(r, c):
            return

        for (tr, tc, special) in self.valid_moves:
            if (r, c) == (tr, tc):
                self.execute_move(self.selected[0], self.selected[1],
                                   tr, tc, special, animate=True)
                return

        piece = self.board[r][c]
        if piece is not None and piece[0] == self.turn:
            self.selected = (r, c)
            self.valid_moves = legal_moves(self.board, r, c,
                                           self.castling_rights, self.en_passant)
            self.hint_move = None
            self.draw_board()
            return

        if self.selected:
            self.selected = None
            self.valid_moves = []
            self.hint_move = None
            self.draw_board()

    # ----- MOVE EXECUTION -----
    def execute_move(self, fr, fc, tr, tc, special, animate=False):
        piece = self.board[fr][fc]
        captured = self.board[tr][tc]
        self.board_history.append(clone_board(self.board))
        prev_cr = dict(self.castling_rights)
        prev_ep = self.en_passant
        prev_last = self.last_move
        prev_turn = self.turn
        mover_color = self.turn

        notation = self._notate(fr, fc, tr, tc, special, piece, captured)

        # Record time BEFORE advancing turn
        if self.competitive.get() and self.turn_start is not None:
            elapsed = time.time() - self.turn_start
            if mover_color == 'w':
                self.white_time += elapsed
            else:
                self.black_time += elapsed
            self.move_times.append((mover_color, notation, elapsed))

        if animate:
            self.animating = True
            self._animate_piece(fr, fc, tr, tc, piece,
                                 lambda: self._finish_move(fr, fc, tr, tc, special,
                                                            piece, captured, notation,
                                                            prev_cr, prev_ep, prev_last, prev_turn,
                                                            mover_color))
        else:
            self._finish_move(fr, fc, tr, tc, special, piece, captured, notation,
                               prev_cr, prev_ep, prev_last, prev_turn, mover_color)

    def _animate_piece(self, fr, fc, tr, tc, piece, callback):
        self.draw_board()
        if (fr, fc) in self.piece_widgets:
            for item in self.canvas.find_withtag(self.piece_widgets[(fr, fc)]):
                self.canvas.delete(item)

        steps = 12
        dx = ((tc - fc) * SQUARE_SIZE) / steps
        dy = ((tr - fr) * SQUARE_SIZE) / steps
        fill = "#FFFFFF" if piece[0] == 'w' else "#1a1a1a"
        outline = WHITE_PIECE_OUTLINE if piece[0] == 'w' else BLACK_PIECE_OUTLINE
        tag = "anim_piece"

        def step(i):
            self.canvas.delete(tag)
            if i > steps:
                callback()
                return
            cx = fc * SQUARE_SIZE + SQUARE_SIZE // 2 + dx * i
            cy = fr * SQUARE_SIZE + SQUARE_SIZE // 2 + dy * i
            # Outline ghost behind
            for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                self.canvas.create_text(cx + ox, cy + oy, text=PIECE_UNICODE[piece],
                                         font=("Arial", 42, "bold"),
                                         fill=outline, tags=(tag,))
            self.canvas.create_text(cx, cy, text=PIECE_UNICODE[piece],
                                     font=("Arial", 42, "bold"),
                                     fill=fill, tags=(tag,))
            self.root.after(15, lambda: step(i + 1))

        step(0)

    def _finish_move(self, fr, fc, tr, tc, special, piece, captured, notation,
                      prev_cr, prev_ep, prev_last, prev_turn, mover_color):
        self.castling_rights, self.en_passant = make_move(
            self.board, fr, fc, tr, tc, special,
            self.castling_rights, self.en_passant)
        self.last_move = (fr, fc, tr, tc)
        self.move_history.append((notation, clone_board(self.board),
                                   prev_cr, prev_ep, prev_last, prev_turn))
        # Append notation with time if competitive
        if self.competitive.get() and self.move_times:
            secs = self.move_times[-1][2]
            self.history_listbox.insert(
                tk.END, f"{len(self.move_history):>2}. {notation:<8s} {secs:5.1f}s")
        else:
            self.history_listbox.insert(tk.END, f"{len(self.move_history):>3}. {notation}")
        self.history_listbox.see(tk.END)

        self.selected = None
        self.valid_moves = []
        self.hint_move = None
        self.animating = False
        self.draw_board()
        self.update_captured()

        # Advance turn
        self.turn = 'b' if self.turn == 'w' else 'w'
        self.turn_start = time.time()  # reset for next player
        self.update_status()

        if self._check_game_over():
            return

        # AI move only in vs AI mode
        if self.mode.get() == "vs AI" and self.turn == 'b':
            self.ai_thinking = True
            self.root.after(250, self.ai_move)

    def _notate(self, fr, fc, tr, tc, special, piece, captured):
        files = "abcdefgh"
        if special == 'castleK':
            return "O-O"
        if special == 'castleQ':
            return "O-O-O"
        sym = '' if piece[1] == 'P' else piece[1]
        cap = 'x' if (captured or special == 'ep') else ''
        promo = ''
        if special and special.startswith('promo'):
            promo = '=' + special[5]
        return f"{sym}{files[fc]}{8-fr}{cap}{files[tc]}{8-tr}{promo}"

    # ----- AI -----
    def ai_move(self):
        if self.game_over:
            self.ai_thinking = False
            return
        depth_map = {"Easy": 1, "Medium": 2, "Hard": 3}
        depth = depth_map[self.difficulty.get()]

        if self.difficulty.get() == "Easy" and random.random() < 0.5:
            moves = all_legal_moves(self.board, 'b', self.castling_rights, self.en_passant)
            if not moves:
                self.ai_thinking = False
                self._check_game_over()
                return
            m = random.choice(moves)
            self.ai_thinking = False
            self.execute_move(m[0], m[1], m[2], m[3], m[4], animate=True)
            return

        _, best = minimax(self.board, depth, -float('inf'), float('inf'),
                          False, self.castling_rights, self.en_passant, 'b')
        self.ai_thinking = False
        if best:
            self.execute_move(best[0], best[1], best[2], best[3], best[4], animate=True)

    # ----- HINTS & TIPS -----
    def show_best_move(self):
        if self.game_over or self.ai_thinking:
            return
        if self.mode.get() == "vs AI" and self.turn != 'w':
            return
        self.ai_thinking = True
        self.status_label.config(text="Thinking of best move...")
        self.root.update()

        def compute():
            color = self.turn
            maximizing = (color == 'w')
            _, best = minimax(self.board, 2, -float('inf'), float('inf'),
                              maximizing, self.castling_rights, self.en_passant, color)
            if best:
                self.hint_move = best
                self.selected = (best[0], best[1])
                self.valid_moves = legal_moves(self.board, best[0], best[1],
                                               self.castling_rights, self.en_passant)
                self.draw_board()
            self.ai_thinking = False
            self.update_status()

        self.root.after(50, compute)

    def show_random_tip(self):
        tip = random.choice(EXTENDED_TIPS)
        win = tk.Toplevel(self.root)
        win.title("Chess Strategy Tip")
        win.configure(bg="#1e1e1e")
        win.geometry("480x220")
        tk.Label(win, text="🧠 Strategy Tip", bg="#1e1e1e", fg="#7CC5FF",
                 font=("Arial", 14, "bold")).pack(pady=(12, 6))
        msg = tk.Message(win, text=tip, bg="#2b2b2b", fg="#e8e8e8",
                          font=("Arial", 11), width=440, padx=14, pady=14)
        msg.pack(padx=12, pady=6, fill=tk.BOTH, expand=True)
        tk.Button(win, text="Close", command=win.destroy,
                  bg="#4a6fa5", fg="white", relief=tk.FLAT,
                  font=("Arial", 10, "bold"), padx=16, pady=4).pack(pady=8)

    # ----- GAME OVER -----
    def _check_game_over(self):
        color = self.turn
        moves = all_legal_moves(self.board, color, self.castling_rights, self.en_passant)
        if not moves:
            self.game_over = True
            self.timer_running = False
            if is_in_check(self.board, color):
                winner = "Black" if color == 'w' else "White"
                self.status_label.config(text=f"CHECKMATE! {winner} wins!", fg="#7CFC00")
                messagebox.showinfo("Game Over", f"Checkmate!\n{winner} wins!")
            else:
                self.status_label.config(text="STALEMATE — Draw!", fg="#FFD700")
                messagebox.showinfo("Game Over", "Stalemate — it's a draw!")
            return True
        pieces = []
        for r in range(8):
            for c in range(8):
                if self.board[r][c]:
                    pieces.append(self.board[r][c][1])
        if len(pieces) <= 2 or (len(pieces) <= 3 and ('B' in pieces or 'N' in pieces)):
            self.game_over = True
            self.timer_running = False
            self.status_label.config(text="Draw — insufficient material", fg="#FFD700")
            return True
        return False

    # ----- STATUS -----
    def update_status(self):
        if self.game_over:
            return
        if is_in_check(self.board, self.turn):
            side = "White" if self.turn == 'w' else "Black"
            self.status_label.config(text=f"{side} is in CHECK!", fg="#FF6B6B")
        else:
            side = "White" if self.turn == 'w' else "Black"
            color = "#fff" if self.turn == 'w' else "#aaa"
            self.status_label.config(text=f"{side} to move", fg=color)

    def update_captured(self):
        start = initial_board()
        start_count = Counter()
        for r in range(8):
            for c in range(8):
                if start[r][c]:
                    start_count[start[r][c]] += 1
        curr_count = Counter()
        for r in range(8):
            for c in range(8):
                if self.board[r][c]:
                    curr_count[self.board[r][c]] += 1
        captured_w, captured_b = [], []
        for piece, n in start_count.items():
            diff = n - curr_count.get(piece, 0)
            if diff > 0:
                sym = PIECE_UNICODE[piece]
                if piece[0] == 'b':
                    captured_b.append(sym * diff)
                else:
                    captured_w.append(sym * diff)
        text = "White lost: " + "".join(captured_b) + "\nBlack lost: " + "".join(captured_w)
        self.captured_label.config(text=text)

    # ----- UNDO -----
    def undo_move(self):
        if self.ai_thinking or self.animating or not self.move_history:
            return
        self._undo_one()
        if (self.mode.get() == "vs AI" and self.move_history
                and self.turn == 'b'):
            self._undo_one()
        self.game_over = False
        self.selected = None
        self.valid_moves = []
        self.last_move = None
        self.turn_start = time.time() if self.competitive.get() else None
        self.draw_board()
        self.update_status()

    def _undo_one(self):
        if not self.move_history:
            return
        notation, board_before, prev_cr, prev_ep, prev_last, prev_turn = self.move_history.pop()
        self.board = board_before
        self.castling_rights = prev_cr
        self.en_passant = prev_ep
        self.last_move = prev_last
        self.turn = prev_turn
        self.history_listbox.delete(tk.END)
        if self.move_times:
            self.move_times.pop()

    # ----- RESET -----
    def reset_game(self):
        self.board = initial_board()
        self.turn = 'w'
        self.selected = None
        self.valid_moves = []
        self.castling_rights = {'wK': True, 'wQ': True, 'bK': True, 'bQ': True}
        self.en_passant = None
        self.last_move = None
        self.game_over = False
        self.ai_thinking = False
        self.move_history = []
        self.hint_move = None
        self.move_times = []
        self.history_listbox.delete(0, tk.END)
        self.white_time = 0.0
        self.black_time = 0.0
        self.turn_start = time.time()
        self.timer_running = self.competitive.get()
        if not self.competitive.get():
            self.white_clock_label.config(text="⬜ White: --:--.-", fg="#888")
            self.black_clock_label.config(text="⬛ Black: --:--.-", fg="#888")
        self.draw_board()
        self.update_status()
        self.update_captured()

    # ----- TUTORIALS -----
    def open_tutorials(self):
        win = tk.Toplevel(self.root)
        win.title("Chess Tutorials")
        win.configure(bg="#1e1e1e")
        win.geometry("780x560")

        left = tk.Frame(win, bg="#1e1e1e")
        left.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)

        tk.Label(left, text="Lessons", bg="#1e1e1e", fg="#fff",
                 font=("Arial", 13, "bold")).pack(anchor=tk.W, pady=(0, 6))

        lesson_list = tk.Listbox(left, bg="#2b2b2b", fg="#eee",
                                   font=("Arial", 11), width=22,
                                   height=18, borderwidth=0,
                                   selectbackground="#4a6fa5")
        lesson_list.pack(fill=tk.Y)

        for name in TUTORIALS:
            lesson_list.insert(tk.END, name)
        lesson_list.insert(tk.END, "── Extended Tips ──")

        right = tk.Frame(win, bg="#1e1e1e")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)

        title_var = tk.StringVar(value="Select a lesson")
        tk.Label(right, textvariable=title_var, bg="#1e1e1e", fg="#7CC5FF",
                 font=("Arial", 14, "bold")).pack(anchor=tk.W, pady=(0, 6))

        text = tk.Text(right, bg="#2b2b2b", fg="#e8e8e8", wrap=tk.WORD,
                        font=("Arial", 11), borderwidth=0, padx=10, pady=10,
                        relief=tk.FLAT)
        text.pack(fill=tk.BOTH, expand=True)

        # Progress indicator
        progress_frame = tk.Frame(right, bg="#1e1e1e")
        progress_frame.pack(fill=tk.X, pady=(6, 0))
        self.lesson_progress_label = tk.Label(progress_frame, text="",
                                               bg="#1e1e1e", fg="#888",
                                               font=("Arial", 9), anchor=tk.E)
        self.lesson_progress_label.pack(side=tk.RIGHT)

        def show_lesson(event=None):
            sel = lesson_list.curselection()
            if not sel:
                return
            name = lesson_list.get(sel[0])
            if name == "── Extended Tips ──":
                title_var.set("🧠 Extended Strategy Tips")
                text.delete("1.0", tk.END)
                text.insert("1.0", "\n\n".join(EXTENDED_TIPS))
                self.lesson_progress_label.config(
                    text=f"{len(EXTENDED_TIPS)} advanced tips")
                return
            title_var.set(name)
            text.delete("1.0", tk.END)
            text.insert("1.0", TUTORIALS[name])
            names = list(TUTORIALS.keys())
            idx = names.index(name) + 1
            self.lesson_progress_label.config(text=f"Lesson {idx} of {len(names)}")

        lesson_list.bind("<<ListboxSelect>>", show_lesson)
        lesson_list.selection_set(0)
        show_lesson()

        # Extra button for extended tips
        tk.Button(left, text="🎲 Random Tip", command=self.show_random_tip,
                  bg="#5a3a7a", fg="white", font=("Arial", 10, "bold"),
                  relief=tk.FLAT, pady=4).pack(fill=tk.X, pady=(8, 0))


def main():
    root = tk.Tk()
    game = ChessGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()