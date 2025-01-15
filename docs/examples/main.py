from netargparse import NetArgumentParser


def main(args):
    if args._cmd == "main":
        print(vars(args))
    else:
        return vars(args)


parser = NetArgumentParser()
parser.add_argument("-x", type=str, required=True)
parser.add_argument("-y", type=int, required=True)
parser.add_argument("-z", action="store_true")
parser(main)
