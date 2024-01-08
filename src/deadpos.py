#!/usr/bin/python3

from subprocess import Popen, PIPE, STDOUT
from copy import deepcopy
import chess
import os
import sys
import time
from solver import is_dead, is_legal, retract

PBAR_ARG = ["--progress-bar"] if not "--no-progress-bar" in sys.argv else []

CPP_SOLVER = Popen(["./solver.exe"] + PBAR_ARG, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
CPP_SOLVER.stdout.readline().strip().decode("utf-8")

PYTHON_SOLVER = Popen(["./solver.py"] + PBAR_ARG, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
PYTHON_SOLVER.stdout.readline().strip().decode("utf-8")

class Position:
    def __init__(self, fen, info = [], check_legality = True):
        words = fen.split(" ")
        self.board = words[0]
        self.turn = words[1]
        self.castling = words[2]
        self.ep = words[3]
        self.halfmove_clock = words[4]
        self.fullmove_counter = words[5]
        self.is_legal = True if not check_legality else is_legal(fen)
        self.is_dead_and_retracted = False
        self.info = info

    def fen(self):
        return " ".join([self.board, self.turn, self.castling, self.ep, \
                         self.halfmove_clock, self.fullmove_counter])

    def __str__(self):
        flag = " (illegal)" if not self.is_legal else \
               " (dead)" if self.is_dead_and_retracted else ""
        return "%s%s %s" % (self.fen(), flag, " ".join(self.info))

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

def solver_call(cmd, pos, progress_bar):
    global CPP_SOLVER, PYTHON_SOLVER

    solver = CPP_SOLVER if "#" in cmd or "--fast" in sys.argv else PYTHON_SOLVER
    if len(pos.info) > 0:
        pos.info += ["then"]

    fen = pos.fen()
    inp = (cmd.split(" ")[0] + " " + fen + "\n").encode("utf-8")
    solver.stdin.write(inp)
    solver.stdin.flush()
    nb_solutions = 0
    while True:
        output = solver.stdout.readline().strip().decode("utf-8")
        if "solution" in output:
            variation = output.split("solution")[1].strip()
            if "(" in cmd:
                pt = cmd.split("(")[1][0]
                b = chess.Board(fen.replace("?", "0"))
                sol = variation.split(" ")
                for m in sol[:-1]:
                    b.push_uci(m)
                if str(b.piece_at(chess.parse_square(sol[-1][:2]))).lower() != pt.lower():
                    nb_solutions -= 1
                    continue
            print(" ".join(pos.info + [variation]).ljust(80))
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

    return nb_solutions

def solve(cmd, positions):
    n = 0
    progress_bar = ProgressBar(len(positions), 30)
    for pos in positions:
        progress_bar.bar[0][0] += 1
        n += solver_call(cmd, pos, progress_bar)
    return n

def backwards(pos):
    retractions = []
    fen = pos.fen()
    fen_is_dead = is_dead(fen)
    for (retracted_fen, retraction) in retract(fen):
        new_pos = Position(retracted_fen, pos.info + [retraction.strip()])
        if new_pos.is_legal and fen_is_dead and is_dead(retracted_fen):
            new_pos.is_dead_and_retracted = True
        retractions.append(new_pos)
    return retractions

def forwards(pos):
    positions = []
    board = chess.Board(pos.fen().replace("?", "0"))
    for m in board.legal_moves:
        board.push(m)
        new_pos = Position(board.fen(), pos.info + [str(m)])
        positions.append(new_pos)
        board.pop()
    return positions

def flip(pos):
    pos = deepcopy(pos)
    pos.turn = "w" if pos.turn == "b" else "b"
    pos.ep = "?"
    pos.halfmove_clock = "?"
    return [Position(fen, pos.info, False) for fen in complete_fen(pos.fen())]

def turn(pos):
    return [pos.turn]

def castling(pos):
    return [pos.castling]

def en_passant(pos):
    return [pos.ep]

def bind(elements, function):
    return [b for el in elements for b in function(el)]

def is_valid(pos):
    return pos.is_legal and not pos.is_dead_and_retracted

def count_valid(positions):
    return len([pos for pos in positions if is_valid(pos)])

def dedup(elements):
    output = []
    for el in elements:
        if not el in output:
            output.append(el)
    return output

def process_cmd(positions, cmd):
    positions = [pos for pos in positions if is_valid(pos)]

    if cmd == "retract" or cmd == "r":
        positions = bind(positions, backwards)
        return (positions, count_valid(positions))

    elif cmd == "move" or cmd == "m":
        positions = bind(positions, forwards)
        return (positions, count_valid(positions))

    elif cmd == "flip":
        positions = bind(positions, flip)
        return (positions, count_valid(positions))

    elif cmd == "turn":
        turns = dedup(bind(positions, turn))
        return (turns, len(turns))

    elif cmd == "castling":
        castling_rights = dedup(bind(positions, castling))
        return (castling_rights, len(castling_rights))

    elif cmd == "ep":
        eps = dedup(bind(positions, en_passant))
        return (eps, len(eps))

    elif cmd == "legal":
        positions = [pos for pos in positions if is_legal(pos.fen(), depth = 2)]
        return (positions, count_valid(positions))

    else:
        n = solve(cmd, positions)
        return ([], n)

def main():
    print("Deadpos Analyzer version 2.1")

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
        nb_tokens = len(fen.split(" "))
        if nb_tokens < 6:
            fen += " ?" * (5 - nb_tokens) + " 1"
        cmds = [w.strip() for w in words[1:]]

        positions = [Position(fen) for fen in complete_fen(fen)]
        n = len(positions)

        for cmd in cmds:
            positions, n = process_cmd(positions, cmd)

        for pos in positions:
            print(pos)

        print("nsols %d".ljust(80) % n)

if __name__ == '__main__':
    main()
