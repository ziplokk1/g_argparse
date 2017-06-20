from argparse import ArgumentParser as _AP, _, Action, SUPPRESS, Namespace, _ArgumentGroup, _get_action_name, HelpFormatter, OPTIONAL, ZERO_OR_MORE, ONE_OR_MORE, REMAINDER, PARSER


SIBLING = 'SIB'


class SiblingHelpFormatter(HelpFormatter):
    def _format_args(self, action, default_metavar):
        get_metavar = self._metavar_formatter(action, default_metavar)

        if action.nargs is None:
            result = '%s' % get_metavar(1)
        elif action.nargs == OPTIONAL:
            result = '[%s]' % get_metavar(1)
        elif action.nargs == ZERO_OR_MORE:
            result = '[%s [%s ...]]' % get_metavar(2)
        elif action.nargs == ONE_OR_MORE:
            result = '%s [%s ...]' % get_metavar(2)
        elif action.nargs == REMAINDER:
            result = '...'
        elif action.nargs == PARSER:
            result = '%s ...' % get_metavar(1)
        elif action.nargs == SIBLING:
            _text = self._format_actions_usage(action.parser._actions, [])
            result = '{}'.format(_text)
        else:
            formats = ['%s' for _ in range(action.nargs)]
            result = ' '.join(formats) % get_metavar(action.nargs)
        return result


class _SiblingArgumentGroup(_ArgumentGroup):

    def __init__(self, container, title=None, description=None, **kwargs):
        super(_SiblingArgumentGroup, self).__init__(container, title, description, **kwargs)

    def add_parser(self, *args, **kwargs):
        psr_instance = kwargs.get('parser')
        if not psr_instance:
            raise ValueError("'parser' cannot be None")
        elif not isinstance(psr_instance, ArgumentParser):
            raise TypeError("'parser' must be an instance of ArgumentParser")

        kwargs['namespace'] = kwargs.pop('namespace', Namespace())
        kwargs['required'] = kwargs.pop('required', False)

        kw = self._get_optional_kwargs(*args, **kwargs)
        action = _SiblingParserAction(**kw)
        self._add_action(action)
        return action


class _SiblingParserAction(Action):

    def __init__(self, option_strings, parser, namespace=None, dest=None, required=False):
        self.parser = parser
        self.namespace = namespace
        self.actually_required = required
        super(_SiblingParserAction, self).__init__(option_strings, dest, required=False, nargs=SIBLING)

    def __call__(self, parser, namespace, values, option_string=None):
        parser_name = values[0]
        arg_strings = values[1:]

        # set the parser name if requested
        if self.dest is not SUPPRESS:
            setattr(namespace, self.dest, parser_name)

        subnamespace, arg_strings = self.parser.parse_known_args(arg_strings, None)
        raise NotImplementedError(_('.__call__() not completed'))


class ArgumentParser(_AP):
    def __init__(self, *args, sibling_prefix_chars=':', **kwargs):
        kwargs['formatter_class'] = kwargs.pop('formatter_class', SiblingHelpFormatter)
        super(ArgumentParser, self).__init__(*args, **kwargs)
        self.sibling_prefix_chars = sibling_prefix_chars
        self._optional_siblings = None
        self._required_siblings = None

        self.register('action', 'sibling', _SiblingParserAction)

    def add_argument_group(self, *args, **kwargs):
        GroupClass = kwargs.pop('group_class', _ArgumentGroup)
        group = GroupClass(self, *args, **kwargs)
        self._action_groups.append(group)
        return group

    def add_sibling(self, *args, **kwargs):
        required = kwargs.get('required', False)
        if required:
            if not self._required_siblings:
                self._required_siblings = self.add_argument_group(group_class=_SiblingArgumentGroup, title='required siblings', prefix_chars=self.sibling_prefix_chars)
            return self._required_siblings.add_parser(*args, **kwargs)
        if not self._optional_siblings:
            self._optional_siblings = self.add_argument_group(group_class=_SiblingArgumentGroup, title='optional siblings', prefix_chars=self.sibling_prefix_chars)
        return self._optional_siblings.add_parser(*args, **kwargs)

    def _split_args(self, arg_strings):
        from collections import defaultdict
        split = defaultdict(list)
        sibling = 'main'
        for arg in arg_strings:
            if not arg.startswith(self.sibling_prefix_chars):
                split[sibling].append(arg)
            else:
                sibling = arg
        return dict(split)

    def all_siblings(self):
        if self._optional_siblings and self._required_siblings:
            return self._optional_siblings._group_actions + self._required_siblings._group_actions
        elif self._optional_siblings:
            return self._optional_siblings._group_actions
        elif self._required_siblings:
            return self._required_siblings._group_actions
        return []

    def parse_known_args(self, args=None, namespace=None):
        if args is None:
            args = sys.argv[1:]
        else:
            args = list(args)

        args = self._split_args(args)

        # default Namespace built from parser defaults
        if namespace is None:
            namespace = Namespace()

        primary_ns = namespace
        print(args)
        required = []
        for sibling in self.all_siblings():
            action_name = _get_action_name(sibling)
            actn = action_name.split('/')
            act_short, act_long =
            if sibling.actually_required and not args.get(sibling.dest):
                required.append(_get_action_name(sibling))
            else:
                sibling_ns, extra = sibling.parser.parse_known_args(args[sibling.dest], sibling.namespace)
                if getattr(primary_ns, sibling.dest, None):
                    raise ValueError('dest already exists in primary namespace. dest={}'.format(sibling.dest))
                setattr(primary_ns, sibling.dest, sibling_ns)

        print(required)
        primary_ns, extra = super().parse_known_args(args.get('main', []), primary_ns)

        if required:
            self.error(_('the following arguments are required: %s') %
                       ', '.join(required))

        return primary_ns, extra

    def format_help(self):
        formatter = self._get_formatter()

        # usage
        formatter.add_usage(self.usage, self._actions,
                            self._mutually_exclusive_groups)

        # description
        formatter.add_text(self.description)

        # positionals, optionals and user-defined groups
        for action_group in self._action_groups:
            formatter.start_section(action_group.title)
            formatter.add_text(action_group.description)
            formatter.add_arguments(action_group._group_actions)
            formatter.end_section()

        # epilog
        formatter.add_text(self.epilog)

        # determine help from format above
        return formatter.format_help()


parsers = {
    'root': ArgumentParser()
}


root = (lambda: parsers['root'])()


def basic_config(*args, **kwargs):
    parsers['root'] = ArgumentParser(*args, **kwargs)


def add_sibling(*args, **kwargs):
    return root.add_sibling(*args, **kwargs)


def add_argument(*args, **kwargs):
    return root.add_argument(*args, **kwargs)


def get_argument_parser(name=None, *args, **kwargs):
    if not name:
        return root
    psr = ArgumentParser(*args, **kwargs)
    parsers[name] = psr
    return psr


def parse_args(args=None, namespace=None):
    return root.parse_args(args, namespace)


if __name__ == '__main__':
    add_argument('--main-flag', action='store_true', dest='main_flag')
    add_argument('--main-optional')

    sibling_parser = get_argument_parser('sibling')
    sibling_parser.add_argument('--sibling-flag', action='store_true')
    sibling_parser.add_argument('--sibling-optional')

    add_sibling(':sib', '::sibling', parser=sibling_parser, required=True)

    import sys
    sys.argv.extend([
        '--main-optional',
        'main optional value',
        '::sibling',
        '--sibling-flag',
        '--sibling-optional',
        'sibling optional value'
    ])

    sys.argv = sys.argv[:1]
    sys.argv.append(':sib')
    sys.argv.append('-h')

    ns = parse_args()
    print(ns)

