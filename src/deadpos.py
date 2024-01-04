#!/usr/bin/python3

from subprocess import Popen, PIPE, STDOUT
import chess
import os
import sys
import time
from solver import is_dead

T0 = time.time()

def init_progress_bar(n):
    global T0
    T0 = time.time()
    return [[0, 0]] * n

def get_progress(progress_bar):
    acc = 0
    den = 1
    for (analyzed, total) in progress_bar:
        if total == 0:
            break
        den = den * total
        acc += max(analyzed-1, 0) / den
    return acc

def format_time(seconds):
    hours = seconds // 3600
    seconds = seconds - hours * 3600
    minutes = seconds // 60
    seconds = seconds - minutes * 60
    return "%02d:%02d:%02d" % (hours, minutes, seconds)

def print_bar(progress_bar):
    global T0
    completed = get_progress(progress_bar)
    remaining = 1 if completed < 0.00001 else (1 - completed) / completed
    processing_time = time.time() - T0
    remaining_time = int((time.time() - T0) * remaining)
    timer = "[" + format_time(processing_time) + " / " + format_time(remaining_time) + "]"
    n = int(40 * completed)
    bar = "|" + "■" * n + " " * (40 - n) + "| "
    print(bar + "{:.2%} ".format(get_progress(progress_bar)) + timer,\
          end = "\r", flush=True)

def set_turn(fen, turn):
    words = fen.split(" ")
    words[1] = turn
    return " ".join(words)

def set_castling(fen, castling):
    words = fen.split(" ")
    words[2] = castling
    return " ".join(words)

def set_ep(fen, ep):
    words = fen.split(" ")
    words[3] = ep
    return " ".join(words)

def retractor_worker():
    return Popen(["../lib/retractor/_build/default/retractor/retractor.exe"], \
                 stdout=PIPE, stdin=PIPE, stderr=STDOUT)

def create_solver(solver_path):
    progress_bar_flag = ["--progress-bar"] if not "--no-progress-bar" in sys.argv else []
    return Popen([solver_path] + progress_bar_flag,
                 stdout=PIPE, stdin=PIPE, stderr=STDOUT)

def retractor_call(cmd, fen, worker):
    fens = []
    inp = (cmd + " " + fen + "\n").encode("utf-8")
    worker.stdin.write(inp)
    worker.stdin.flush()
    # Shall we use a while true?
    while True:
        output = worker.stdout.readline().strip().decode("utf-8")
        if "nsols" in output or len(output) <= 1:
            break
        fens.append(output)
    return fens

def retract(fens, worker, dead_solver):
    retractions = []
    for (fen, aux) in fens:
        fen_is_dead = is_dead(chess.Board(fen.replace("?","0")))
        outputs = retractor_call("retract", fen, worker)
        for out in outputs:
            f, rmove = out.split('retraction')
            if fen_is_dead and is_dead(chess.Board(f.replace("?","0"))):
                continue
            # If en-passant flag is active in retracted fen, add it
            # to the auxiliary information
            ep = f.split(" ")[3]
            ep_info = ["(ep:" + ep + ")"] if ep != "-" else []
            retractions.append((f.strip(), aux + [rmove.strip()] + ep_info))
    return retractions

def solver_call(cmd, fen, aux, solver, progress_bar):
    # If en-passant flag is on in fen, but not en-passant move is
    # possible, do not solve this case.
    board = chess.Board(fen.replace("?", "0"))
    if board.ep_square:
        ep_possible = False
        for m in board.legal_moves:
            if board.is_en_passant(m):
                ep_possible = True
                break
        if not ep_possible:
            return 0

    if len(aux) > 0:
        aux = aux + ["then"]

    inp = (cmd + " " + fen + "\n").encode("utf-8")
    solver.stdin.write(inp)
    solver.stdin.flush()
    nb_solutions = 0
    while True:
        output = solver.stdout.readline().strip().decode("utf-8")
        if "solution" in output:
            variation = output.split("solution")[1].strip()
            print(" ".join(aux + [variation]).ljust(80))
        elif "progress" in output and not "nsols" in output:
            words = output.split(" ")
            level = int(words[2])
            next_level_size = int(words[4])
            progress_bar[level+1] = [0, next_level_size]
            if level > 0:
                progress_bar[level][0] += 1
                print_bar(progress_bar)
        elif not "progress" in output and "nsols" in output:
            nb_solutions += int(output[5:])
            break
        elif "RuntimeError:" in output:
            print(output)
            exit()

    return nb_solutions

def solve(cmd, fens, solver):
    n = 0
    progress_bar = [[0, len(fens)]] + init_progress_bar(30)
    for (fen, aux) in fens:
        progress_bar[0][0] += 1
        n += solver_call(cmd, fen, aux, solver, progress_bar)
    return n

def process_cmd(fens, cmd, worker, mate_solver, draw_solver):
    if cmd[0] == "r":
        n = int(cmd[1:])
        for i in range(n):
            fens = retract(fens, worker, draw_solver)
        return (fens, len(fens))

    else:
        if "#" in cmd or "--fast" in sys.argv:
            n = solve(cmd, fens, mate_solver)
        else:
            n = solve(cmd, fens, draw_solver)
        return ([], n)

def main():
    try:
        MATE_SOLVER_PATH = sys.argv[sys.argv.index('-solver')+1]
    except:
        MATE_SOLVER_PATH = "./solver.exe"

    try:
        DRAW_SOLVER_PATH = sys.argv[sys.argv.index('-solver')+1]
    except:
        DRAW_SOLVER_PATH = "./solver.py"

    print("Deadpos Analyzer version 2.0")

    retractor = retractor_worker()
    mate_solver = create_solver(MATE_SOLVER_PATH)
    draw_solver = create_solver(DRAW_SOLVER_PATH)
    mate_solver.stdout.readline().strip().decode("utf-8")
    draw_solver.stdout.readline().strip().decode("utf-8")
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == "quit":
            break
        if len(line) < 2 or line[:2] == "//":
            continue

        print(">>>", line)
        words = line.split(">>=")
        fen = words[0].strip()
        nb_tokens = len(fen.split(" "))
        if nb_tokens < 6:
            fen += " ?" * (5 - nb_tokens) + " 1"
        cmds = [w.strip() for w in words[1:]]

        fen_parts = fen.split(" ")
        b = chess.Board(fen_parts[0] + " w - - 0 1")

        wL = str(b.piece_at(chess.A1)) == 'R' and str(b.piece_at(chess.E1)) == 'K'
        wS = str(b.piece_at(chess.H1)) == 'R' and str(b.piece_at(chess.E1)) == 'K'
        bL = str(b.piece_at(chess.A8)) == 'r' and str(b.piece_at(chess.E8)) == 'k'
        bS = str(b.piece_at(chess.H8)) == 'r' and str(b.piece_at(chess.E8)) == 'k'

        turns = ["w", "b"] if fen_parts[1] == "?" else [fen_parts[1]]
        fens = [fen]
        fens = [set_turn(fen, t) for fen in fens for t in turns]

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

        new_fens = []
        for f in fens:
            if fen_parts[3] != "?":
                new_fens.append(f)
                continue

            wtm = f.split(" ")[1] == "w"
            direction = -1 if wtm else 1
            turn_pawn = 'P' if wtm else 'p'
            other_pawn = 'p' if wtm else 'P'
            ep_sqs = range(8, 16) if not wtm else range(40, 48)
            ep_sqs = [s for s in ep_sqs if str(b.piece_at(s + direction * 8)) == other_pawn]
            ep_sqs = [s for s in ep_sqs if ((s % 8 > 0 and str(b.piece_at(s + direction * 8 - 1)) == turn_pawn) or
                                            (s % 8 < 7 and str(b.piece_at(s + direction * 8 + 1)) == turn_pawn))]
            ep_sqs = ["-"] + [chess.square_name(s) for s in ep_sqs]
            new_fens += [set_ep(f, s) for s in ep_sqs]

        fens = new_fens

        fens = [(f, []) for f in fens]

        for cmd in cmds:
            fens, n = process_cmd(fens, cmd, retractor, mate_solver, draw_solver)

        for (fen, aux) in fens:
            print(fen, " ".join(aux))

        print("nsols %d".ljust(80) % n)

    retractor.terminate()
    mate_solver.terminate()
    draw_solver.terminate()

if __name__ == '__main__':
    main()
