from netargparse import NetArgumentParser


def main(args):
    if args._cmd == "main":
        print(vars(args))
    else:
        return vars(args)


parser = NetArgumentParser()
parser.add_argument("-x", type=int, required=True, nargs="+")
parser.add_argument("-y", type=int, required=True, action="append")
parser.add_argument("-z", type=int, required=True, nargs="+", action="append")
parser(main)
