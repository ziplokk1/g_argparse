from argparse import ArgumentParser, HelpFormatter

root = ArgumentParser()
parsers = {}


def get_argument_parser(prog=None, usage=None, description=None, epilog=None, parents=[], formatter_class=HelpFormatter,
                        prefix_chars='-', fromfile_prefix_chars=None, argument_default=None, conflict_handler='error',
                        add_help=True):
    parents.append(root)
    parser = ArgumentParser(prog, usage, description, epilog, parents, formatter_class,
                            prefix_chars, fromfile_prefix_chars, argument_default, conflict_handler,
                            add_help)
    return parser
