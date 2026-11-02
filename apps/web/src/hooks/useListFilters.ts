import { useEffect, useMemo, useState } from 'react';
import { buildListQuery } from '../lib/listFilters';

export function useListFilters(options?: {
  pageSize?: number;
  debounceMs?: number;
  extra?: Record<string, string | undefined>;
}) {
  const pageSize = options?.pageSize ?? 100;
  const debounceMs = options?.debounceMs ?? 300;
  const extra = options?.extra;
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [filters, setFilters] = useState<Record<string, string>>({});

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedSearch(search), debounceMs);
    return () => window.clearTimeout(timer);
  }, [search, debounceMs]);

  const setFilter = (key: string, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const reset = () => {
    setSearch('');
    setDebouncedSearch('');
    setFilters({});
  };

  const queryString = useMemo(
    () =>
      buildListQuery({
        ...extra,
        search: debouncedSearch.trim() || undefined,
        page_size: pageSize,
        ...filters,
      }),
    [debouncedSearch, extra, filters, pageSize],
  );

  const hasActive =
    Boolean(search.trim()) || Object.values(filters).some(Boolean);

  return {
    search,
    setSearch,
    debouncedSearch,
    filters,
    setFilter,
    reset,
    queryString,
    hasActive,
  };
}
