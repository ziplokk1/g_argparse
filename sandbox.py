import sys

sys.argv.extend(['positional_main', '--foo', 'arg', '::mod', 'positional_secondary', '--optional1', 'optional1-value'])

from global_argparse._module_parser import ArgumentParser

extra_parser = ArgumentParser()
extra_parser.add_argument('positional_secondary', action='store_true')
extra_parser.add_argument('--optional1')

parser = ArgumentParser()
parser.add_argument('positional_main', action='store_true')
parser.add_argument('--foo', help='foo help')
parser.add_parser('::mod', extra_parser)

args = parser.parse_args()
print(args)

