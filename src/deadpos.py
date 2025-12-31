#!/usr/bin/python3

from subprocess import Popen, PIPE, STDOUT
from copy import deepcopy
from colorama import Fore, Back, Style
import chess
import os
import sys
import time
from solver import is_dead, is_legal, is_zombie, explain_dead, \
    explain_alive, retract, is_illegal_sherlock

PROGRESS_BAR = not "--no-progress-bar" in sys.argv
SHOW_ALL = "--show-all" in sys.argv
SOLVER_ARGS = ["--progress-bar"] if PROGRESS_BAR else []
SOLVER_ARGS += ["--show-all"] if SHOW_ALL else []
UCI_NOTATION = "--uci" in sys.argv
SHERLOCK = "--sherlock" in sys.argv

CPP_SOLVER = Popen(["./solver.exe"] + SOLVER_ARGS, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
CPP_SOLVER.stdout.readline().strip().decode("utf-8")

PYTHON_SOLVER = Popen(["./solver.py"] + SOLVER_ARGS, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
PYTHON_SOLVER.stdout.readline().strip().decode("utf-8")

RETRACTION_SYMBOL = "↶"

class Position:
    def __init__(self, fen, history = []):
        words = fen.split(" ")
        self.board = words[0]
        self.turn = words[1]
        self.castling = words[2]
        self.ep = words[3]
        self.halfmove_clock = words[4]
        self.fullmove_counter = words[5]
        self.is_valid = True
        self.history = history

    def fen(self):
        return " ".join([self.board, self.turn, self.castling, self.ep, \
                         self.halfmove_clock, self.fullmove_counter])

    def __str__(self):
        tab = " " if self.history != [] else ""
        s = "%s%s%s" % (" ".join([m for (m, fen) in self.history]), tab, self.fen())

        if "illegal dead" in s:
            color = Fore.LIGHTMAGENTA_EX
        elif "illegal" in s:
            color = Fore.LIGHTRED_EX
        elif "zombie" in s:
            color = Fore.LIGHTBLUE_EX
        elif "dead" in s:
            color = Fore.LIGHTYELLOW_EX
        else:
            color = Fore.LIGHTGREEN_EX

        if not PROGRESS_BAR:
            return s.ljust(80)

        s = s.replace("(", Style.RESET_ALL + "(", 1)
        ss = s.split(")")
        ss[-1] = color + ss[-1]
        s = ")".join(ss)
        return color + s.ljust(80) + Style.RESET_ALL

def format_time(seconds):
    hours = seconds // 3600
    seconds = seconds - hours * 3600
    minutes = seconds // 60
    seconds = seconds - minutes * 60
    return "%02d:%02d:%02d" % (hours, minutes, seconds)

class ProgressBar:
    def __init__(self, nb_goals, nb_steps):
        self.t0 = time.time()
        self.bar = [[0, nb_goals]] + [[0, 0]] * nb_steps

    def get_progress(self):
        acc = 0
        den = 1
        for (analyzed, total) in self.bar:
            if total == 0:
                break
            den = den * total
            acc += max(analyzed-1, 0) / den
        return acc

    def __str__(self):
        completed = self.get_progress()
        remaining = 1 if completed < 0.00001 else (1 - completed) / completed
        processing_time = time.time() - self.t0
        remaining_time = int((time.time() - self.t0) * remaining)
        timer = "[" + format_time(processing_time) + " / " + format_time(remaining_time) + "]"
        n = int(40 * completed)
        bar = "|" + "■" * n + " " * (40 - n) + "| "
        return bar + "{:.2%} ".format(completed) + timer

def complete_fen(fen):
    fen_parts = fen.split(" ")
    board = chess.Board(fen_parts[0] + " w - - 0 1")

    def exists(piece_symbol, square):
        return board.piece_at(square) == chess.Piece.from_symbol(piece_symbol)

    def set_fen_argv(fen, i, value):
        fen_parts = fen.split(" ")
        fen_parts[i] = value
        return " ".join(fen_parts)

    def set_turn(fen, turn):
        return set_fen_argv(fen, 1, turn)

    def set_castling(fen, cr):
        return set_fen_argv(fen, 2, cr)

    def set_ep(fen, ep):
        return set_fen_argv(fen, 3, ep)

    fens = [fen]

    # Complete turns
    turns = ["w", "b"] if fen_parts[1] == "?" else [fen_parts[1]]
    fens = [set_turn(fen, turn) for fen in fens for turn in turns]

    # Complete castlings
    wL = exists('R', chess.A1) and exists('K', chess.E1)
    wS = exists('R', chess.H1) and exists('K', chess.E1)
    bL = exists('r', chess.A8) and exists('k', chess.E8)
    bS = exists('r', chess.H8) and exists('k', chess.E8)
    new_fens = []
    for f in fens:
        if fen_parts[2] != "?":
            new_fens.append(f)
            continue
        crs = [""]
        crs = [cr + flag for cr in crs for flag in (["K", ""] if wS else [""])]
        crs = [cr + flag for cr in crs for flag in (["Q", ""] if wL else [""])]
        crs = [cr + flag for cr in crs for flag in (["k", ""] if bS else [""])]
        crs = [cr + flag for cr in crs for flag in (["q", ""] if bL else [""])]
        crs = crs[:-1] + ["-"]
        new_fens += [set_castling(f, cr) for cr in crs]
    fens = new_fens

    # Complete en-passant
    new_fens = []
    for f in fens:
        if fen_parts[3] != "?":
            new_fens.append(f)
            continue
        wtm = f.split(" ")[1] == "w"
        south, our_pawn, their_pawn = (-1, 'P', 'p') if wtm else (1, 'p', 'P')
        ep_sqs = range(16, 24) if not wtm else range(40, 48)
        ep_sqs = [s for s in ep_sqs if
                  exists(their_pawn, s + south * 8) and
                  board.piece_at(s) == None and
                  board.piece_at(s - south * 8) == None]
        ep_sqs = [s for s in ep_sqs if
                  ((s % 8 > 0 and exists(our_pawn, s + south * 8 - 1)) or
                   (s % 8 < 7 and exists(our_pawn, s + south * 8 + 1)))]
        ep_sqs = ["-"] + [chess.square_name(s) for s in ep_sqs]
        new_fens += [set_ep(f, s) for s in ep_sqs]

    return new_fens

def legal(pos, flush):
    if not pos.is_valid:
        return [pos]

    history = pos.history + [("legal", pos.fen())]
    flag = []
    for i in range(len(history)):
        (m, fen) = history[i]
        if fen:
            if not is_legal(fen, depth = 2):
                flag += [("illegal (unretractable)", None)]
            elif SHERLOCK:
                (illegal, reason) = is_illegal_sherlock(fen)
                if illegal:
                    flag += [("illegal " + reason, None)]

            if is_zombie(fen, depth = 2):
                flag += [("zombie", None)]
            elif RETRACTION_SYMBOL in m and is_dead(fen):
                flag += [("dead", None)]

        if flag != []:
            pos.is_valid = False
            break
    pos.history = pos.history[:i+1] + flag + pos.history[i+1:]
    if flush == "with-legal":
        print(pos)

    return [pos]

def lan(board, m):
    s = board.lan(m)
    if board.is_en_passant(m):
        if s.endswith('+'):
            return s[:-1] + 'ep+'

        elif s.endswith('#'):
            return s[:-1] + 'ep#'

        return s + 'ep'

    return s

def solver_call(cmd, pos, progress_bar, flush):
    global CPP_SOLVER, PYTHON_SOLVER, UCI_NOTATION

    solver = CPP_SOLVER if "#" in cmd or "--fast" in sys.argv else PYTHON_SOLVER

    fen = pos.fen()
    inp = (cmd.split(" ")[0] + " " + fen + "\n").encode("utf-8")
    solver.stdin.write(inp)
    solver.stdin.flush()
    solutions = []
    nb_solutions = 0
    while True:
        output = solver.stdout.readline().strip().decode("utf-8")
        if "solution" in output:
            variation = output.split("solution")[1].strip()
            b = chess.Board(fen.replace("?", "0"))
            if "(" in cmd:
                pt = cmd.split("(")[1][0]
                sol = variation.split(" ")
                for m in sol[:-1]:
                    b.push_uci(m)
                if str(b.piece_at(chess.parse_square(sol[-1][:2]))).lower() != pt.lower():
                    nb_solutions -= 1
                    continue

            moves = variation.split(" ")
            b = chess.Board(fen.replace("?", "0"))
            history = []

            for i in range(len(moves)):
                try:
                    move_added = False
                    m = moves[i].replace("#", "")
                    m_str = str(moves[i]) if UCI_NOTATION else lan(b, b.parse_uci(m))
                    history += [m_str]
                    move_added = True
                    b.push_uci(moves[i])
                    if moves[i+1] != "DP" and not b.is_stalemate() and is_dead(b.fen()):
                        history += ["dead"] + ["(" + explain_dead(b) + ")"]
                        break
                except:
                    if not move_added:
                        history += moves[i:]
                    break

            if not "dead" in history and cmd[:2] == "h=" and cmd[:5] != "h=0.5":
                b.pop()
                alive_reason = explain_alive(b.fen())
                if len(alive_reason) > 50:
                    alive_reason = " ".join(alive_reason.split(" ")[:6]) + "..."
                history = history[:-1] + ["(" + alive_reason + ")"] + history[-1:]
            elif "DP" in history:
                history += ["(" + explain_dead(b) + ")"]

            history_token = [(" ".join(history), None)]
            new_pos = Position(b.fen(), history = pos.history + history_token)
            if flush != None:
                if "legal" in flush:
                    print(legal(new_pos, None)[0])
                else:
                    print(new_pos)
            solutions.append(new_pos)

        elif "progress" in output and not "nsols" in output:
            words = output.split(" ")
            level = int(words[2])
            next_level_size = int(words[4])
            progress_bar.bar[level + 1] = [0, next_level_size]
            if level > 0:
                progress_bar.bar[level][0] += 1
                print(progress_bar, flush = True, end = '\r')
        elif not "progress" in output and "nsols" in output:
            nb_solutions += int(output[5:])
            break
        elif "RuntimeError:" in output:
            print(output)
            exit()

    return (solutions, nb_solutions)

def solve(cmd, positions, flush):
    # The convention says that White should make the last move in a puzzle.
    # If "half-duplex" appears in the stip, the roles of W and B are flipped.
    # Therefore, the player expected to make the first move can be determined
    # as follows.
    help_factor = -1 if "h" in cmd else 1
    p5_factor = -1 if ".5" in cmd else 1
    hd_factor = -1 if "half-duplex" in cmd else 1
    expected_turn = "w" if help_factor * p5_factor * hd_factor == 1 else "b"

    # Unless "duplex" is specified, we discard all positions whose turn does
    # not coincide with the expected turn.

    if " duplex" not in cmd:
        positions = [pos for pos in positions if pos.turn == expected_turn]

    progress_bar = ProgressBar(len(positions), 30)

    nb_solutions = 0
    all_solutions = []
    for pos in positions:
        progress_bar.bar[0][0] += 1
        (solutions, n) = solver_call(cmd, pos, progress_bar, flush)
        all_solutions += solutions
        nb_solutions += n

    if len(all_solutions) < nb_solutions:
        print("A total of %d solutions were found, not all were printed" % nb_solutions)

    return (all_solutions, len(all_solutions))

def backwards(pos):
    global UCI_NOTATION

    retractions = []
    fen = pos.fen()
    if not UCI_NOTATION:
        board = chess.Board(fen.replace("?", "0"))
    for (retracted_fen, retraction) in retract(fen):
        retraction_str = retraction.strip()
        if not UCI_NOTATION:
            retraction_str = retraction_str.replace("prom", "").replace("ep", "")
            source = retraction_str[:2]
            target = retraction_str[-2:]
            prom = ""
            if "prom" in retraction:
                prom = str(board.piece_at(chess.parse_square(target))).lower()
            retracted_board = chess.Board(retracted_fen.replace("?", "0"))
            move = retracted_board.parse_uci(source + target + prom)
            retraction_str = lan(retracted_board, move)
            if "ep" in retraction:
                retraction_str += "ep"
            if "x" in retraction:
                captured = str(retracted_board.piece_at(chess.parse_square(target))).upper()
                retraction_str = retraction_str.replace("x", "x" + captured)
        history_token = (RETRACTION_SYMBOL + retraction_str, retracted_fen)
        new_pos = Position(retracted_fen, pos.history + [history_token])
        retractions.append(new_pos)
    return retractions

def forwards(pos):
    global UCI_NOTATION

    positions = []
    board = chess.Board(pos.fen().replace("?", "0"))
    for m in board.legal_moves:
        dead_token = [("dead", None)] if is_dead(board.fen()) else []
        m_str = str(m) if UCI_NOTATION else lan(board, m)
        board.push(m)
        history_token = (m_str, board.fen())
        new_pos = Position(board.fen(), pos.history + dead_token + [history_token])
        positions.append(new_pos)
        board.pop()
    return positions

def flip(pos):
    pos = deepcopy(pos)
    pos.turn = "w" if pos.turn == "b" else "b"
    pos.ep = "?"
    pos.halfmove_clock = "?"
    return [Position(fen, pos.history) for fen in complete_fen(pos.fen())]

def turn(pos):
    return [pos.turn]

def castling(pos):
    return [pos.castling]

def en_passant(pos):
    return [pos.ep]

def dp(pos):
    pos = deepcopy(pos)
    if is_dead(pos.fen()):
        explanation = explain_dead(chess.Board(pos.fen().replace("?", "0")))
        pos.history += [("DP", None)] + [("(" + explanation + ")", None)]
    else:
        pos.history += [("alive", None)]
    return [pos]

def bind(elements, function):
    return [b for el in elements for b in function(el)]

def dedup(elements):
    output = []
    for el in elements:
        if not el in output:
            output.append(el)
    return output

def process_cmd(positions, cmd, flush = None):
    positions = [pos for pos in positions if pos.is_valid]

    if cmd == "retract" or cmd == "r":
        positions = bind(positions, backwards)
        return (positions, len(positions))

    elif cmd == "move" or cmd == "m":
        positions = bind(positions, forwards)
        return (positions, len(positions))

    elif cmd == "flip":
        positions = bind(positions, flip)
        return (positions, len(positions))

    elif cmd == "turn":
        turns = dedup(bind(positions, turn))
        return (turns, len(turns))

    elif cmd == "castling":
        castling_rights = dedup(bind(positions, castling))
        return (castling_rights, len(castling_rights))

    elif cmd == "ep":
        eps = dedup(bind(positions, en_passant))
        return (eps, len(eps))

    elif cmd == "DP" or cmd == "dp":
        positions = bind(positions, dp)
        return (positions, len(positions))

    elif cmd == "legal":
        positions = [r for pos in positions for r in legal(pos, flush)]
        return (positions, len([pos for pos in positions if pos.is_valid]))

    else:
        return solve(cmd, positions, flush)


def main():
    print("Deadpos Analyzer version 2.4.1")

    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == "quit":
            break

        if line[:2] == "//":
            print(line)

        line = line.split("//")[0]
        if len(line) < 2:
            continue

        print(">>>", line)
        words = line.split(">>=")
        fen = words[0].strip()

        fen_parts = fen.split(" ")
        fen_board = fen_parts[0]
        valid = False
        for turn in fen_parts[1].replace("?", "w b").split(" "):
            if chess.Board(fen_board + " " + turn + " - - 0 1").is_valid():
                valid = True
                break

        if not valid:
            print("Invalid FEN")
            continue

        nb_tokens = len(fen.split(" "))
        if nb_tokens < 6:
            fen += " ?" * (5 - nb_tokens) + " 1"
        cmds = [w.strip() for w in words[1:]]

        positions = [Position(fen, []) for fen in complete_fen(fen)]
        n = len(positions)

        def is_solve_cmd(cmd):
            # This is a bit hacky, but does the job for now
            return "#" in cmd or cmd[0] == "h" or "=" in cmd

        flush = "plain" if len(cmds) > 0 and is_solve_cmd(cmds[-1]) else None
        if len(cmds) > 1 and cmds[-1] == "legal":
            flush = "with-legal"
            if is_solve_cmd(cmds[-2]):
                cmds = cmds[:-1]

        for cmd in cmds:
            positions, n = process_cmd(positions, cmd, flush)

        if flush == None:
            for pos in positions:
                print(pos)

        print("nsols %d".ljust(80) % n, end = "\n\n")

if __name__ == '__main__':
    main()
