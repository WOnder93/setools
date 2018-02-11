# Copyright 2014, Tresys Technology, LLC
# Copyright 2017-2018, Chris PeBenito <pebenito@ieee.org>
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

cdef class User(PolicySymbol):

    """A user."""

    cdef sepol.user_datum_t *handle

    @staticmethod
    cdef factory(SELinuxPolicy policy, sepol.user_datum_t *symbol):
        """Factory function for constructing User objects."""
        u = User()
        u.policy = policy
        u.handle = symbol
        return u

    def __str__(self):
        return intern(self.policy.handle.p.p.sym_val_to_name[sepol.SYM_USERS][self.handle.s.value - 1])

    def _eq(self, User other):
        """Low-level equality check (C pointers)."""
        return self.handle == other.handle

    @property
    def roles(self):
        # object_r is implicitly added to all roles by the compiler.
        # technically it is incorrect to skip it, but policy writers
        # and analysts don't expect to see it in results, and it
        # will confuse, especially for role set equality user queries.
        return set(r for r in RoleEbitmapIterator.factory(self.policy, &self.handle.roles.roles)
                   if r != "object_r")

    @property
    def mls_level(self):
        """The user's default MLS level."""
        if not self.policy.mls:
            raise MLSDisabled

        return Level.factory(self.policy, &self.handle.exp_dfltlevel)

    @property
    def mls_range(self):
        """The user's MLS range."""
        if not self.policy.mls:
            raise MLSDisabled

        return Range.factory(self.policy, &self.handle.exp_range)

    def statement(self):
        roles = list(str(r) for r in self.roles)
        stmt = "user {0} roles ".format(self)
        if len(roles) > 1:
            stmt += "{{ {0} }}".format(' '.join(roles))
        else:
            stmt += roles[0]

        try:
            stmt += " level {0.mls_level} range {0.mls_range};".format(self)
        except MLSDisabled:
            stmt += ";"

        return stmt


#
# Iterator Classes
#
cdef class UserIterator(HashtabIterator):

    """Iterate over users in the policy."""

    @staticmethod
    cdef factory(SELinuxPolicy policy, sepol.hashtab_t *table):
        """Factory function for creating User iterators."""
        i = UserIterator()
        i.policy = policy
        i.table = table
        i.reset()
        return i

    def __next__(self):
        super().__next__()
        return User.factory(self.policy, <sepol.user_datum_t *>self.curr.datum)