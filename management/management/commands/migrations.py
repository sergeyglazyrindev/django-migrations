from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from ._migrations import Migrations


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-m', default=False, help='Please specify description for migration. For create action'),
        make_option('--to', default=False, help='Please specify migration name we should downgrade db to')
    )

    def handle(self, *args, **options):
        if not args:
            return None
        action = args[0]
        needed_options_per_action = {
            'create': (('m', 'Please specify description for migration. For create action'), )
        }
        if needed_options_per_action.get(action):
            for option in needed_options_per_action.get(action):
                if not options.get(option[0]):
                    raise CommandError('The option -{} is missed. {}'.format(option[0], option[1]))
        getattr(Migrations, action)(**options)
