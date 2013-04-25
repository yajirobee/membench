#! /usr/bin/env python

import sys, os, sqlite3
import plotutil as pu

if __name__ == "__main__":
    if len(sys.argv) == 2:
        dbpath = os.path.abspath(sys.argv[1])
        terminaltype = "png"
    elif len(sys.argv) == 3:
        dbpath = os.path.abspath(sys.argv[1])
        terminaltype = sys.argv[2]
    else:
        sys.stdout.write("Usage : {0} dbpath [eps|png]\n".format(sys.argv[0]))
        sys.exit(1)

    if terminaltype != "png" and terminaltype != "eps":
        sys.stdout.write("wrong terminal type\n")
        sys.exit(1)

    conn = sqlite3.connect(dbpath)
    tables = ["random"]
    cols = [{"name" : "clk_per_op", "unit" : "cycle/op"},
            {"name" : "usec_per_op", "unit" : "us/op"}]
    fpath = os.path.dirname(dbpath) + "/" + os.path.splitext(os.path.basename(dbpath))[0]

    gp = pu.gpinit(terminaltype)
    gp('set grid')
    gp('set logscale x')

    #draw access_size-latency graph
    alloc_nodeslist = [[r[0] for r in
                        conn.execute("select distinct alloc_node from {0}".format(tbl))]
                       for tbl in tables]
    gp('set title "latency"')
    gp.xlabel("access\_size (KB)")
    for col in cols:
        gp.ylabel("{0} ({1})".format(col["name"].replace("_", "\\_"),
                                     col["unit"].replace("_", "\\_")))
        gp('set key left top')
        figpath = "{0}_{1}.{2}".format(fpath, col["name"], terminaltype)
        gp('set output "{0}"'.format(figpath))
        gds = []
        for tbl, nodes in zip(tables, alloc_nodeslist):
            query = ("select access_size/1024,avg({0}) from {1} "
                     "where alloc_node={{alloc_node}} group by access_size"
                     .format(col["name"], tbl))
            gds.extend(pu.query2data(conn, query, alloc_node = nodes,
                                     title = "alloc\_node = {alloc_node}",
                                     with_ = "linespoints"))
        sys.stdout.write('draw : {0}\n'.format(figpath))
        gp.plot(*gds)
    gp.close()
    conn.close()
