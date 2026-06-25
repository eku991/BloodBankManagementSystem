"""
Data Structures for Blood Bank Management System
- Queue (FIFO): ensures oldest blood is used first
- HashMap: indexes blood units by blood group for fast lookup
- Sorting: sorts blood units by expiry date
"""

from collections import deque


# ==================== QUEUE (FIFO) ====================
class BloodQueue:
    """
    A Queue (First-In, First-Out) data structure for blood units.
    Blood donated first should be used first to prevent expiry/wastage.
    """

    def __init__(self):
        self._queue = deque()

    def enqueue(self, blood_unit):
        """Add a blood unit to the back of the queue."""
        self._queue.append(blood_unit)

    def dequeue(self):
        """Remove and return the oldest blood unit (front of queue)."""
        if self.is_empty():
            return None
        return self._queue.popleft()

    def peek(self):
        """View the oldest blood unit without removing it."""
        if self.is_empty():
            return None
        return self._queue[0]

    def is_empty(self):
        return len(self._queue) == 0

    def size(self):
        return len(self._queue)

    def get_all(self):
        """Return all items in queue order (oldest first)."""
        return list(self._queue)


# ==================== HASH MAP ====================
class BloodGroupHashMap:
    """
    A Hash Map that indexes blood units by blood group.
    Allows O(1) average lookup of all units for a given blood group.

    Internal structure:
        key = blood group string (e.g., "A+", "O-")
        value = list of blood unit records
    """

    def __init__(self, size=8):
        self._size = size
        self._buckets = [[] for _ in range(self._size)]
        self._count = 0

    def _hash(self, key):
        """Simple hash function: sum of character codes mod table size."""
        hash_value = 0
        for char in str(key):
            hash_value += ord(char)
        return hash_value % self._size

    def put(self, blood_group, blood_unit):
        """Insert a blood unit under its blood group key."""
        index = self._hash(blood_group)
        bucket = self._buckets[index]

        for entry in bucket:
            if entry[0] == blood_group:
                entry[1].append(blood_unit)
                self._count += 1
                return

        bucket.append([blood_group, [blood_unit]])
        self._count += 1

    def get(self, blood_group):
        """Retrieve all blood units for a given blood group."""
        index = self._hash(blood_group)
        bucket = self._buckets[index]

        for entry in bucket:
            if entry[0] == blood_group:
                return entry[1]
        return []

    def remove_unit(self, blood_group, unit_id):
        """Remove a specific blood unit by ID from a blood group."""
        index = self._hash(blood_group)
        bucket = self._buckets[index]

        for entry in bucket:
            if entry[0] == blood_group:
                entry[1] = [u for u in entry[1] if u['id'] != unit_id]
                self._count -= 1
                return True
        return False

    def get_all_groups(self):
        """Return a dictionary of all blood groups and their unit counts."""
        result = {}
        for bucket in self._buckets:
            for entry in bucket:
                result[entry[0]] = len(entry[1])
        return result

    def total_units(self):
        return self._count


# ==================== SORTING (by Expiry Date) ====================
def merge_sort_by_expiry(blood_units):
    """
    Merge Sort implementation to sort blood units by expiry date.
    Units expiring soonest come first (ascending order).

    Time Complexity: O(n log n)
    Space Complexity: O(n)
    """
    if len(blood_units) <= 1:
        return blood_units

    mid = len(blood_units) // 2
    left_half = merge_sort_by_expiry(blood_units[:mid])
    right_half = merge_sort_by_expiry(blood_units[mid:])

    return _merge(left_half, right_half)


def _merge(left, right):
    """Merge two sorted lists into one sorted list by expiry_date."""
    result = []
    i = j = 0

    while i < len(left) and j < len(right):
        if left[i]['expiry_date'] <= right[j]['expiry_date']:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    result.extend(left[i:])
    result.extend(right[j:])
    return result
