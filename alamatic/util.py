

class LinkedListSlot(object):
    def __init__(self, container, item, prev_slot=None, next_slot=None):
        self.container = container
        self.item = item
        self.prev_slot = prev_slot
        self.next_slot = next_slot

    def prepend(self, item):
        slot = LinkedListSlot(
            self.container,
            item,
            prev_slot=self.prev_slot,
            next_slot=self,
        )
        self.prev_slot = slot
        if slot.prev_slot is not None:
            slot.prev_slot.next_slot = slot
        if self.container.first_slot is self:
            self.container.first_slot = slot

    def append(self, item):
        slot = LinkedListSlot(
            self.container,
            item,
            prev_slot=self,
            next_slot=self.next_slot,
        )
        self.next_slot = slot
        if slot.next_slot is not None:
            slot.next_slot.prev_slot = slot
        if self.container.last_slot is self:
            self.container.last_slot = slot

    def remove(self):
        self.replace([])
        return self.item

    def replace(self, new_items):
        if len(new_items) == 0:
            # remove the current item
            if self.container.first_slot is self:
                self.container.first_slot = self.next_slot
            if self.container.last_slot is self:
                self.container.last_slot = self.prev_slot
            if self.next_slot is not None:
                self.next_slot.prev_slot = self.prev_slot
            if self.prev_slot is not None:
                self.prev_slot.next_slot = self.next_slot
        elif len(new_items) == 1:
            slot = LinkedListSlot(
                self.container,
                new_items[0],
                self.prev_slot,
                self.next_slot,
            )
            if self.container.first_slot is self:
                self.container.first_slot = slot
            if self.container.last_slot is self:
                self.container.last_slot = slot
            if self.next_slot is not None:
                self.next_slot.prev_slot = slot
            if self.prev_slot is not None:
                self.prev_slot.next_slot = slot
        else:
            slots = [
                LinkedListSlot(
                    self.container,
                    item,
                )
                for item in new_items
            ]

            first = slots[0]
            last = slots[-1]

            if self.container.first_slot is self:
                self.container.first_slot = first
            if self.container.last_slot is self:
                self.container.last_slot = last
            if self.next_slot is not None:
                self.next_slot.prev_slot = last
                last.next_slot = self.next_slot
            if self.prev_slot is not None:
                self.prev_slot.next_slot = first
                first.prev_slot = self.prev_slot

            for i, slot in enumerate(slots):
                if i > 0:
                    slot.prev_slot = slots[i - 1]
                    slots[i - 1].next_slot = slot
                if i < (len(slots) - 1):
                    slot.next_slot = slots[i + 1]
                    slots[i + 1].prev_slot = slot


class LinkedList(object):

    def __init__(self, initial_items=[]):
        self.first_slot = None
        self.last_slot = None

        self.extend(initial_items)

    def prepend(self, item):
        slot = LinkedListSlot(self, item)
        if self.last_slot is None:
            self.first_slot = slot
            self.last_slot = slot
        else:
            self.first_slot.prepend(item)

    def append(self, item):
        slot = LinkedListSlot(self, item)
        if self.last_slot is None:
            self.first_slot = slot
            self.last_slot = slot
        else:
            self.last_slot.append(item)

    def extend(self, items):
        for item in items:
            self.append(item)

    def __iter__(self):
        for slot in self.iterslots():
            yield slot.item

    def iterslots(self):
        current = self.first_slot
        while current is not None:
            yield current
            current = current.next_slot

    def __reversed__(self):
        current = self.last_slot
        while current is not None:
            yield current.item
            current = current.prev_slot
