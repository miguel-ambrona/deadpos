#!/usr/bin/python3

from subprocess import Popen, PIPE, STDOUT
import chess
import os
import sys

def init_progress_bar(n):
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

def chessml_worker():
    my_env = os.environ.copy()
    my_env["CHA_PATH"] = "../lib/chessml/lib/D3-Chess/src/cha"
    p = Popen(["../lib/chessml/_build/default/retractor/retractor.exe"], \
              env=my_env, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
    return p

def create_solver(solver_path):
    progress_bar = ["--progress-bar"] if "--progress-bar" in sys.argv else []
    return Popen([solver_path] + progress_bar,
                 stdout=PIPE, stdin=PIPE, stderr=STDOUT)

def chessml_call(cmd, fen, worker):
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

def retract(fens, worker):
    retractions = []
    for (fen, aux) in fens:
        outputs = chessml_call("retract", fen, worker)
        for out in outputs:
            f, rmove = out.split('retraction')
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

    inp = (cmd + " " + fen + "\n").encode("utf-8")
    solver.stdin.write(inp)
    solver.stdin.flush()
    nb_solutions = 0
    while True:
        output = solver.stdout.readline().strip().decode("utf-8")
        if "solution" in output:
            variation = output.split("solution")[1].strip()
            print(" ".join(aux + [variation]))
        elif "progress" in output:
            words = output.split(" ")
            level = int(words[2])
            next_level_size = int(words[4])
            progress_bar[level+1] = [0, next_level_size]
            if level > 0:
                progress_bar[level][0] += 1
                # print(progress_bar)
                print ("progress", get_progress(progress_bar), flush=True)
        elif "nsols" in output:
            nb_solutions += int(output[5:])
            break
    return nb_solutions

def solve(cmd, fens, solver):
    n = 0
    progress_bar = [[0, len(fens)]] + init_progress_bar(30)
    for (fen, aux) in fens:
        progress_bar[0][0] += 1
        n += solver_call(cmd, fen, aux, solver, progress_bar)
    return n

def process_cmd(fens, cmd, worker, solver):
    if cmd == "d":
        return (fens, len(fens))

    elif cmd[0] == "r":
        n = int(cmd[1:])
        for i in range(n):
            fens = retract(fens, worker)
        return (fens, len(fens))

    else:
        n = solve(cmd, fens, solver)
        return ([], n)

def main():
    try:
        SOLVER_PATH = sys.argv[sys.argv.index('-solver')+1]
    except:
        SOLVER_PATH = "./solver.exe"

    worker = chessml_worker()
    solver = create_solver(SOLVER_PATH)
    output = solver.stdout.readline().strip().decode("utf-8")
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
        if len(fen.split(" ")) == 4:
            fen += " ? 1"
        cmds = [w.strip() for w in words[1:]]
        # If turn, castling or ep are unspecified, complete the FEN
        fen_parts = fen.split(" ")
        if fen_parts[1] == "?" or fen_parts[2] == "?" or fen_parts[3] == "?":
            fens = chessml_call("complete", fen, worker)
        else:
            fens = [fen]

        fens = [(f, []) for f in fens]
        for cmd in cmds:
            fens, n = process_cmd(fens, cmd, worker, solver)

        for (fen, aux) in fens:
            print(fen, " ".join(aux))

        print("nsols %d" % n)

    worker.terminate()
    solver.terminate()

if __name__ == '__main__':
    main()
