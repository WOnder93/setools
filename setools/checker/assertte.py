# Copyright 2020, Microsoft Corporation
#
# This file is part of SETools.
#
# SETools is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 2.1 of
# the License, or (at your option) any later version.
#
# SETools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with SETools.  If not, see
# <http://www.gnu.org/licenses/>.
#

import logging

from ..exception import InvalidCheckValue, InvalidClass
from ..terulequery import TERuleQuery
from .checkermodule import CheckerModule
from .util import config_list_to_class, config_list_to_perms, config_list_to_types_or_attrs, \
    config_to_type_or_attr


SOURCE_OPT = "source"
TARGET_OPT = "target"
CLASS_OPT = "tclass"
PERMS_OPT = "perms"
EXEMPT_SRC_OPT = "exempt_source"
EXEMPT_TGT_OPT = "exempt_target"


class AssertTE(CheckerModule):

    """Checker module for asserting a type enforcement allow rule exists (or not)."""

    check_type = "assert_te"
    check_config = frozenset((SOURCE_OPT, TARGET_OPT, CLASS_OPT, PERMS_OPT, EXEMPT_SRC_OPT,
                             EXEMPT_TGT_OPT))

    def __init__(self, policy, checkname, config):
        super().__init__(policy, checkname, config)
        self.log = logging.getLogger(__name__)

        self.source = config_to_type_or_attr(self.policy, config.get(SOURCE_OPT))
        self.target = config_to_type_or_attr(self.policy, config.get(TARGET_OPT))
        self.tclass = config_list_to_class(self.policy, config.get(CLASS_OPT))
        self.perms = config_list_to_perms(self.policy, config.get(PERMS_OPT), self.tclass)

        self.exempt_source = config_list_to_types_or_attrs(self.log,
                                                           self.policy,
                                                           config.get(EXEMPT_SRC_OPT),
                                                           strict=False,
                                                           expand=True)

        self.exempt_target = config_list_to_types_or_attrs(self.log,
                                                           self.policy,
                                                           config.get(EXEMPT_TGT_OPT),
                                                           strict=False,
                                                           expand=True)

        if not any((self.source, self.target, self.tclass, self.perms)):
            raise InvalidCheckValue(
                "At least one of source, target, tclass, or perms options must be set.")

    def run(self):
        assert any((self.source, self.target, self.tclass, self.perms)), \
            "AssertTe no options set, this is a bug."

        self.log.info("Checking TE allow rule assertion.")

        query = TERuleQuery(self.policy,
                            source=self.source,
                            target=self.target,
                            tclass=self.tclass,
                            perms=self.perms,
                            ruletype=("allow",))

        failures = []
        for rule in sorted(query.results()):
            srcs = set(rule.source.expand())
            tgts = set(rule.target.expand())
            if (srcs - self.exempt_source) and (tgts - self.exempt_target):
                self.log_fail(str(rule))
                failures.append(rule)
            else:
                self.log_ok(str(rule))

        self.log.debug("{} failure(s)".format(failures))
        return failures
