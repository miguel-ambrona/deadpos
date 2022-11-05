#!/usr/bin/python3

from subprocess import Popen, PIPE, STDOUT
import os

def chessml_worker():
    my_env = os.environ.copy()
    my_env["CHA_PATH"] = "../lib/chessml/lib/D3-Chess/src/cha"
    p = Popen(["../lib/chessml/_build/default/retractor/retractor.exe"], \
              env=my_env, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
    return p

def create_solver():
    return Popen(["./solver.exe"], stdout=PIPE, stdin=PIPE, stderr=STDOUT)

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
            retractions.append((f.strip(), aux + [rmove.strip()]))
    return retractions

def solver_call(cmd, fen, aux, solver):
    inp = (cmd + " " + fen + "\n").encode("utf-8")
    solver.stdin.write(inp)
    solver.stdin.flush()
    nb_solutions = 0
    while True:
        output = solver.stdout.readline().strip().decode("utf-8")
        if "solution" in output:
            variation = output.split("solution")[1].strip()
            print(" ".join(aux + [variation]))
        elif "nsols" in output:
            nb_solutions += int(output[5:])
            break
    if nb_solutions > 0:
        print(fen, aux)
    return nb_solutions

def solve(cmd, fens, solver):
    n = 0
    for (fen, aux) in fens:
        n += solver_call(cmd, fen, aux, solver)
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
    worker = chessml_worker()
    solver = create_solver()
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == "quit":
            break
        if len(line) < 2 or line[:2] == "//":
            continue

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
