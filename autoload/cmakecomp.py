#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
Cmake complete.
"""

import sys
from subprocess import check_output
import subprocess
from pathlib import Path
import json

CMAKE_DICT = {}
CMAKE_DICT_LOADED = False
CMAKE_DICT_FILE = Path(__file__).parent / "cmake_dict.json"


def load_from_file():
    global CMAKE_DICT, CMAKE_DICT_LOADED
    if CMAKE_DICT_FILE.exists():
        try:
            CMAKE_DICT = json.loads(CMAKE_DICT_FILE.read_text("utf-8"))
            CMAKE_DICT_LOADED = True
            return True
        except Exception as e:
            print(str(e), file=sys.stderr)
    return False


def load_dict():
    if CMAKE_DICT_LOADED:
        return
    if not load_from_file():
        print("Cannot load dict file!", file=sys.stderr)


def store_to_file():
    CMAKE_DICT_FILE.write_text(json.dumps(CMAKE_DICT, indent=4), "utf-8")


def expand_name(name):
    if "<CONFIG>" in name:
        yield from expand_name(name.replace("<CONFIG>", "DEBUG"))
        yield from expand_name(name.replace("<CONFIG>", "RELEASE"))
        return
    if "<LANG>" in name:
        yield from expand_name(name.replace("<LANG>", "C"))
        yield from expand_name(name.replace("<LANG>", "CXX"))
        return
    yield name


def vim_escape(s):
    return s.replace("\\", "\\\\").replace('\n', '\\n').replace('"', '\\"')


def extract_subcommand(subcommand):
    ret = check_output(["cmake", f"--help-{subcommand}-list"]).decode("utf-8")
    names = [name.strip() for name in ret.split("\n") if name.strip()]
    total = len(names)
    for idx,name in enumerate(names):
        print(f"idx: {idx} / total: {total}, {name}")
        # awk NF remove blank lines
        # tail -n +3  from 3th line begins
        # head -n5 pick first 5lines, that is from 3 - 8 lines from the original document
        p1 = subprocess.Popen(['cmake',f"--help-{subcommand}",name],stdout=subprocess.PIPE)
        p2 = subprocess.Popen(['awk','NF'],stdin=p1.stdout,stdout=subprocess.PIPE)
        p1.stdout.close()
        p3 = subprocess.Popen(['tail','-n','+3'],stdin=p2.stdout,stdout=subprocess.PIPE)
        p2.stdout.close()
        p4 = subprocess.Popen(['head','-n7'],stdin=p3.stdout,stdout=subprocess.PIPE)
        #  info = check_output(["cmake", f"--help-{subcommand}",
        #                       name,'|awk NF','|tail -n +3','head -n5']).decode("utf-8")
        info = p4.communicate()[0].decode("utf-8")
        if(len(info) == 0):
            sys.exit(-1)
        for n in expand_name(name):
            CMAKE_DICT[n] = [vim_escape(info), subcommand]


def gen_dict():
    try:
        for subcommand in ["command", "property", "policy", "variable"]:
            extract_subcommand(subcommand)

        store_to_file()
    except Exception as e:
        print(str(e), file=sys.stderr)


def complete(base):
    import vim
    vim.command("let g:cmakecomp_dict = []")
    load_dict()
    for k, v in CMAKE_DICT.items():
        if k.startswith(base):
            try:
                vim.command(
                    r"""call add(g:cmakecomp_dict, {'word':'%s', 'info':"%s", 'menu':'[%s]', 'icase':0})"""
                    % (k, v[0], v[1]))
            except Exception as e:
                print(str(e), file=sys.stderr)


def main():
    gen_dict()


if __name__ == "__main__":
    main()
