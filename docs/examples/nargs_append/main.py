from netargparse import NetArgumentParser


def main(args):
    if args._cmd == "main":
        print(vars(args))
    else:
        return vars(args)


nap = NetArgumentParser()
nap.parser.add_argument("-x", type=int, required=True, nargs="+")
nap.parser.add_argument("-y", type=int, required=True, action="append")
nap.parser.add_argument("-z", type=int, required=True, nargs="+", action="append")
nap(main)
