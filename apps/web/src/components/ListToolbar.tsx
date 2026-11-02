import type { ListFilterDef } from '../lib/listFilters';

interface ListToolbarProps {
  search: string;
  onSearchChange: (value: string) => void;
  searchPlaceholder?: string;
  filters?: ListFilterDef[];
  filterValues?: Record<string, string>;
  onFilterChange?: (key: string, value: string) => void;
  onReset?: () => void;
  resultCount?: number;
  totalCount?: number;
}

export default function ListToolbar({
  search,
  onSearchChange,
  searchPlaceholder = 'Search…',
  filters = [],
  filterValues = {},
  onFilterChange,
  onReset,
  resultCount,
  totalCount,
}: ListToolbarProps) {
  const showCount = resultCount != null && totalCount != null;

  return (
    <div className="list-toolbar">
      <div className="list-toolbar-main">
        <div className="list-toolbar-search">
          <svg className="list-toolbar-search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="search"
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder={searchPlaceholder}
            aria-label="Search list"
          />
        </div>
        {filters.map((filter) => (
          <div key={filter.key} className="list-toolbar-filter">
            <label htmlFor={`filter-${filter.key}`}>{filter.label}</label>
            <select
              id={`filter-${filter.key}`}
              value={filterValues[filter.key] ?? ''}
              onChange={(e) => onFilterChange?.(filter.key, e.target.value)}
            >
              <option value="">All</option>
              {filter.options.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        ))}
        {onReset && (
          <button type="button" className="btn btn-secondary btn-sm list-toolbar-reset" onClick={onReset}>
            Clear
          </button>
        )}
      </div>
      {showCount && (
        <div className="list-toolbar-meta">
          Showing {resultCount} of {totalCount}
        </div>
      )}
    </div>
  );
}
