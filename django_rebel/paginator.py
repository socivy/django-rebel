from math import ceil

from django.core.paginator import Paginator


# Modified version of a GIST I found in a SO thread
from django.db import connection


class LargeListPaginator(Paginator):
    """
    Warning: Postgresql only hack
    Overrides the count method of QuerySet objects to get an estimate instead of actual count when not filtered.
    However, this estimate can be stale and hence not fit for situations where the count of objects actually matter.
    """

    def __init__(self, max_num_pages=100, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.max_num_pages = max_num_pages

    def _get_count(self):
        if getattr(self, '_count', None) is not None:
            return self._count

        query = self.object_list.query
        if not query.where:
            try:
                cursor = connection.cursor()
                cursor.execute("SELECT reltuples FROM pg_class WHERE relname = %s",
                               [query.model._meta.db_table])
                self._count = int(cursor.fetchone()[0])
            except:
                self._count = self.object_list.count()
        else:
            self._count = self.object_list.count()

        return self._count

    count = property(_get_count)

    def _get_num_pages(self):
        """Return the total number of pages."""
        if self.count == 0 and not self.allow_empty_first_page:
            return 0
        hits = max(1, self.count - self.orphans)
        normal_value = ceil(hits / self.per_page)

        return min(self.max_num_pages, normal_value)

    num_pages = property(_get_num_pages)