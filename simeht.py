#!/usr/bin/env python3

from sys import argv, exit
from re import compile, RegexFlag
from subprocess import run
from glob import glob
from os import path

if len(argv) < 2:
    exit("source file is not specified, quitting")

p = compile("^//( ?)@(?P<attr>pattern|in|out|time|mem|bin) (?P<val>.+)$", RegexFlag.ASCII)

class Constraints:
    time: float = 1.0;
    mem: int = 256;
    pattern: str | None = None;
    inp: str | None = None;
    out: str | None = None;
    bin: str | None = None;

c = Constraints()

with open(argv[1], "r") as f:
    l = f.readline()
    while l != "":
        m = p.search(l)
        if m == None:
            break
        mg = m.groupdict()
        match mg["attr"]:
            case "pattern":
                c.pattern = str(mg["val"])
            case "in":
                c.inp = str(mg["val"])
            case "out": c.out = str(mg["val"])
            case "bin": c.bin = str(mg["val"])
            case "time": c.time = float(mg["val"])
            case "mem": c.mem = int(mg["val"])
            case _: pass
        l = f.readline()
    if any(map(lambda x: x == None or x == "", [c.pattern, c.inp, c.out, c.bin])):
        exit("missing one of 'pattern', 'in', 'out', 'bin'")

paths = glob(str(c.pattern), recursive=False)

for p in paths:
    res = run(list(map(str, [
        "isolate",
        f"--dir=/wd={p}:norec",
        f"--dir={path.dirname(str(c.bin))}:norec",
        "-m", c.mem << 10,
        "-i", path.join("/wd", str(c.inp)),
        "-t", c.time,
        "--run", c.bin
    ])), text=True, capture_output=True)
    print(p)
    with open(path.join(p, str(c.out)), "r") as eout:
        el = eout.readline().strip()
        lns = res.stdout.splitlines()
        i = 0
        while True:
            if i >= len(lns):
                if el == "":
                    break
                exit(f"line {i}: expected '{el}', got eof")
            l = lns[i].strip()
            if el == "" and el != l:
                exit(f"line {i}: expected eof, got '{l}'")
            if el != l:
                exit(f"line {i}: expected '{el}', got '{l}'")
            el = eout.readline().strip()
            i += 1
    print(res.stderr)



