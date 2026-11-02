import { useQuery } from '@tanstack/react-query';
import { api } from '../api';

export interface Site {
  id: string;
  code: string;
  name: string;
}

export function useSites() {
  return useQuery({
    queryKey: ['sites'],
    queryFn: () => api<Site[]>('/v1/sites'),
  });
}

export function useDefaultSiteId() {
  const { data: sites } = useSites();
  return sites?.[0]?.id;
}
