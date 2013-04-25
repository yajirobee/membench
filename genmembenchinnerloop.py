#! /usr/bin/env python

import sys, os

archdict = {"ax" : "rax",
            "mov" : "movq",
            "addq" : "addq"}

def generate_rand(fo):
    num_ops = 1 << 8
    fo.write("#define MEM_INNER_LOOP_RANDOM_NUM_OPS {nops}\n"
             "__asm__ __volatile__(\n"
             '"#rand inner loop\\n\\t"\n'
             .format(nops = num_ops))
    fo.write(''.join(['"{mov}\\t(%%{ax}), %%{ax}\\n\\t"\n'.format(**archdict)
                      for i in range(num_ops)]))
    fo.write(': "=a" (ptr)\n'
             ': "0" (ptr)\n'
             ');\n')

if __name__ == "__main__":
    generate_rand(sys.stdout)
