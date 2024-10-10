from netargparse import NetArgumentParser


def main(args):
    if args._cmd == "main":
        print(vars(args))
    else:
        return vars(args)


nap = NetArgumentParser()
nap.parser.add_argument("-x", type=str, required=True)
nap.parser.add_argument("-y", type=int, required=True)
nap.parser.add_argument("-z", action="store_true")
nap(main)
