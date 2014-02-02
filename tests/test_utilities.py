
import unittest
from alamatic.util import *


class TestLinkedList(unittest.TestCase):

    def assertListContent(self, llist, expected):
        self.assertEqual(
            list(llist),
            expected,
        )
        self.assertEqual(
            list(reversed(llist)),
            list(reversed(expected)),
        )

    def test_init_empty(self):
        for llist in (LinkedList(), LinkedList([])):
            self.assertEqual(
                llist.first_slot,
                None,
            )
            self.assertEqual(
                llist.last_slot,
                None,
            )

    def test_init_one(self):
        llist = LinkedList([9])
        self.assertEqual(
            llist.first_slot,
            llist.last_slot,
        )
        self.assertEqual(
            type(llist.first_slot),
            LinkedListSlot,
        )
        self.assertEqual(
            llist.first_slot.item,
            9,
        )

    def test_init_two(self):
        llist = LinkedList([9, 8])
        self.assertNotEqual(
            llist.first_slot,
            llist.last_slot,
        )
        self.assertEqual(
            type(llist.first_slot),
            LinkedListSlot,
        )
        self.assertEqual(
            type(llist.last_slot),
            LinkedListSlot,
        )
        self.assertEqual(
            llist.first_slot.item,
            9,
        )
        self.assertEqual(
            llist.last_slot.item,
            8,
        )
        self.assertEqual(
            llist.first_slot.next_slot,
            llist.last_slot,
        )
        self.assertEqual(
            llist.last_slot.prev_slot,
            llist.first_slot,
        )

    def test_append(self):
        llist = LinkedList()
        llist.append(7)
        self.assertEqual(
            list(llist),
            [7],
        )
        llist.append(6)
        self.assertEqual(
            list(llist),
            [7, 6],
        )
        llist.append(5)
        self.assertEqual(
            list(llist),
            [7, 6, 5],
        )

    def test_extend(self):
        llist = LinkedList()
        llist.extend([4, 3])
        self.assertEqual(
            list(llist),
            [4, 3],
        )
        llist.extend([2, 1, 0])
        self.assertEqual(
            list(llist),
            [4, 3, 2, 1, 0],
        )

    def test_reverse(self):
        llist = LinkedList([2, 3, 4, 5])
        self.assertEqual(
            list(reversed(llist)),
            [5, 4, 3, 2],
        )

    def test_iterate_slots(self):
        llist = LinkedList([1, 2, 3])
        slots = list(llist.iterslots())
        self.assertEqual(
            len(slots),
            3,
        )
        self.assertEqual(
            slots[0],
            llist.first_slot,
        )
        self.assertEqual(
            slots[1],
            llist.first_slot.next_slot,
        )
        self.assertEqual(
            slots[2],
            llist.last_slot,
        )

    def test_prepend(self):
        llist = LinkedList([1, 2, 3])
        llist.prepend(0)
        self.assertListContent(
            llist,
            [0, 1, 2, 3],
        )

    def test_slot_prepend(self):
        llist = LinkedList([1, 2, 3])
        llist.first_slot.prepend(0)
        self.assertListContent(
            llist,
            [0, 1, 2, 3],
        )
        llist.last_slot.prepend(2.5)
        self.assertListContent(
            llist,
            [0, 1, 2, 2.5, 3],
        )

    def test_slot_append(self):
        llist = LinkedList([1, 2, 3])
        llist.first_slot.append(1.5)
        self.assertListContent(
            llist,
            [1, 1.5, 2, 3],
        )
        llist.last_slot.append(4)
        self.assertListContent(
            llist,
            [1, 1.5, 2, 3, 4],
        )

    def test_slot_remove(self):
        llist = LinkedList([1, 2, 3, 4])
        self.assertEqual(
            llist.first_slot.next_slot.remove(),
            2,
        )
        self.assertListContent(
            llist,
            [1, 3, 4],
        )
        llist.last_slot.remove()
        self.assertListContent(
            llist,
            [1, 3],
        )
        llist.first_slot.remove()
        self.assertListContent(
            llist,
            [3],
        )
        llist.last_slot.remove()
        self.assertListContent(
            llist,
            [],
        )

    def test_slot_replace_one(self):
        llist = LinkedList([1, 2, 3])
        llist.first_slot.replace([0])
        self.assertListContent(
            llist,
            [0, 2, 3],
        )

        llist.last_slot.replace([4])
        self.assertListContent(
            llist,
            [0, 2, 4],
        )

        llist.first_slot.next_slot.replace([1])
        self.assertListContent(
            llist,
            [0, 1, 4],
        )

    def test_slot_replace_two(self):
        llist = LinkedList([1, 2, 3])
        llist.first_slot.replace([-1, 0])
        self.assertListContent(
            llist,
            [-1, 0, 2, 3],
        )

        llist.last_slot.replace([4, 5])
        self.assertListContent(
            llist,
            [-1, 0, 2, 4, 5],
        )

        llist.first_slot.next_slot.replace([14, 15])
        self.assertListContent(
            llist,
            [-1, 14, 15, 2, 4, 5],
        )

    def test_slot_replace_many(self):
        llist = LinkedList([1, 2, 3])
        llist.first_slot.replace([1.1, 1.2, 1.3])
        self.assertListContent(
            llist,
            [1.1, 1.2, 1.3, 2, 3],
        )

        llist.last_slot.replace([3.1, 3.2, 3.3])
        self.assertListContent(
            llist,
            [1.1, 1.2, 1.3, 2, 3.1, 3.2, 3.3],
        )

        llist.first_slot.next_slot.replace([2.1, 2.2, 2.3, 2.4])
        self.assertListContent(
            llist,
            [1.1, 2.1, 2.2, 2.3, 2.4, 1.3, 2, 3.1, 3.2, 3.3],
        )


class TestOverloadable(unittest.TestCase):

    class Base(object):
        pass

    # Multiple inheritence with diamond
    class Child(Base, object):
        pass

    class Grandchild(Child):
        pass

    def test_func(self):

        @overloadable
        def try_it(what):
            return ("default", what)

        @try_it.overload(self.Base)
        def try_it(what):
            return ("base", what)

        @try_it.overload(self.Grandchild)
        def try_it(what):
            return ("grandchild", what)

        base = self.Base()
        child = self.Child()
        grandchild = self.Grandchild()

        self.assertEqual(
            try_it(None),
            ("default", None),
        )
        self.assertEqual(
            try_it(base),
            ("base", base),
        )
        # no overloaded implementation for Child
        self.assertEqual(
            try_it(child),
            ("base", child),
        )
        self.assertEqual(
            try_it(grandchild),
            ("grandchild", grandchild),
        )

    def test_method(self):

        class Visitor(object):

            @overloadable
            def visit(self, what):
                return ("default", self, what)

            @visit.overload(self.Base)
            def visit(self, what):
                return ("base", self, what)

            @visit.overload(self.Grandchild)
            def visit(self, what):
                return ("grandchild", self, what)

        base = self.Base()
        child = self.Child()
        grandchild = self.Grandchild()

        visitor = Visitor()

        self.assertEqual(
            visitor.visit(None),
            ("default", visitor, None),
        )
        self.assertEqual(
            visitor.visit(base),
            ("base", visitor, base),
        )
        # no overloaded implementation for Child
        self.assertEqual(
            visitor.visit(child),
            ("base", visitor, child),
        )
        self.assertEqual(
            visitor.visit(grandchild),
            ("grandchild", visitor, grandchild),
        )
