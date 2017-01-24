import sys
if len(sys.argv) > 1:
	fname = sys.argv[1]
	with open(fname) as f:
		line = f.readline()
		print line
