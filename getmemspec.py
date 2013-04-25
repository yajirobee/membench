#! /usr/bin/env python

import sys, os, subprocess, shlex, re, sqlite3, itertools, time

class membenchmarker(object):
    respatterns = {
        "alloc_node" : re.compile(r"node\s(\d+)"),
        "elapsed_time" : re.compile(r"elapsed_time\s(\d+(?:\.\d*)?)"),
        "total_ops" : re.compile(r"total_ops\s(\d+)"),
        "total_clk" : re.compile(r"total_clk\s(\d+)"),
        "ops_per_sec" : re.compile(r"ops_per_sec\s((?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"),
        "clk_per_op" : re.compile(r"clk_per_op\s((?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"),
        "usec_per_op" : re.compile(r"\(usec_per_op\s(\d+(?:\.\d*)?)\)")
        }
    perfcmd = "perf stat -a -o {perfout} -- "

    def __init__(self, perfoutdir = None, statoutdir = None):
        self.perfoutdir = perfoutdir
        self.statoutdir = statoutdir
        self.cmdtmp = None

    def run(self, valdict):
        if not self.cmdtmp:
            sys.stderr.write("Command template must be set.\n")
            return None
        bname = '_'.join([str(k) + str(v) for k, v in valdict.items()]) if valdict else "record"
        cmd = self.cmdtmp.format(**valdict)
        if self.perfoutdir:
            perfout = "{0}/{1}.perf".format(self.perfoutdir, bname)
            cmd = self.perfcmd.format(perfout = perfout) + cmd
        sys.stderr.write("start : {0}\n".format(cmd))
        if self.statoutdir:
            iostatout = "{0}/{1}.io".format(self.statoutdir, bname)
            mpstatout = "{0}/{1}.cpu".format(self.statoutdir, bname)
            pio = subprocess.Popen(["iostat", "-x", "1"],
                                   stdout = open(iostatout, "w"))
            pmp = subprocess.Popen(["mpstat", "-P", "ALL", "1"],
                                   stdout = open(mpstatout, "w"))
        try:
            p = subprocess.Popen(shlex.split(cmd), stdout = subprocess.PIPE)
            if p.wait() != 0:
                sys.stderr.write("measure failed : {0}\n".format(p.returncode))
                sys.exit(1)
        finally:
            if self.statoutdir:
                pio.kill()
                pmp.kill()
        reslist = []
        res = {}
        for line in p.stdout:
            sys.stderr.write("  {0}".format(line))
            line = line.rstrip()
            for k, pat in self.respatterns.items():
                match = pat.match(line)
                if match:
                    if k == "alloc_node":
                        if res:
                            reslist.append(res)
                        res = {}
                    res[k] = float(match.group(1))
                    break
        if res:
            reslist.append(res)
        return reslist

class membenchrecorder(object):
    typedict = {"core" : "integer",
                "access_size" : "integer",
                "alloc_node" : "integer",
                "elapsed_time" : "real",
                "total_ops" : "integer",
                "total_clk" : "integer",
                "ops_per_sec" : "real",
                "clk_per_op" : "real",
                "usec_per_op" : "real"}

    def __init__(self, dbpath):
        self.conn = sqlite3.connect(dbpath)
        self.tbldict = {}
        for r in self.conn.execute("select name, sql from sqlite_master where type = 'table'"):
            match = re.search(".*\((.*)\).*", r[1])
            columns = match.group(1).split(',')
            self.tbldict[r[0]] = [v.strip().split()[0] for v in columns]

    def createtable(self, tblname, columns):
        if tblname in self.tbldict:
            sys.stderr.write("table already exist : {0}\n".format(tblname))
            return
        schema = ','.join(["{0} {1}".format(k, self.typedict.get(k, ""))
                           for k in columns])
        self.conn.execute("create table {0}({1})".format(tblname, schema))
        self.tbldict[tblname] = columns

    def insert(self, tblname, valdict):
        columns = self.tbldict[tblname]
        orderedvals = [0 for i in columns]
        for k, v in valdict.items():
            orderedvals[columns.index(k)] = v
        self.conn.execute(("insert into {0} values ({1})"
                           .format(tblname, ','.join('?' * len(columns)))),
                          orderedvals)
        self.conn.commit()

def clear_cache():
    ret = subprocess.call(["clearcache"])
    if ret != 0:
        sys.stderr.write("cache clear error\n")
        sys.exit(1)

def randommembench(outdir, valdicts):
    mbench = membenchmarker()
    mbench.cmdtmp = "./membench {core} {access_size}"
    recorder = membenchrecorder("{0}/memspec.db".format(outdir))
    tblname = "random"
    if tblname in recorder.tbldict:
        columns = recorder.tbldict[tblname]
    else:
        columns = ("core", "access_size",
                   "alloc_node", "elapsed_time", "total_ops", "total_clk",
                   "ops_per_sec", "clk_per_op", "usec_per_op")
        recorder.createtable(tblname, columns)
    for valdict in valdicts:
        clear_cache()
        res = mbench.run(valdict)
        for r in res:
            r.update(valdict)
            recorder.insert(tblname, r)

sizelist = [2 ** i for i in range(14, 33)]
valdicts = []
for size in sizelist:
    valdicts.append({"core" : 1, "access_size" : size})

if __name__ == "__main__":
    if len(sys.argv) != 1:
        sys.stdout.write("Usage : {0}\n".format(sys.argv[0]))
        sys.exit(0)
    outdir = "/data/local/keisuke/{0}".format(time.strftime("%Y%m%d%H%M%S", time.gmtime()))
    os.mkdir(outdir)

    for i in range(5):
        # random read
        sys.stdout.write("memory random bench : {0}\n".format(i))
        randommembench(outdir, valdicts)
        time.sleep(30)
