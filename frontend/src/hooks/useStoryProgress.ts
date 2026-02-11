/**
 * useStoryProgress Hook
 *
 * Provides real-time story progress updates for a user with automatic polling.
 * Designed for use in the Story Beat Tool to keep UI synchronized with backend state.
 *
 * @example
 * ```tsx
 * const { data: progress, isLoading, refetch } = useStoryProgress('user_123', {
 *   refetchInterval: 3000, // Poll every 3 seconds
 * });
 * ```
 */

import { useQuery, type UseQueryResult } from '@tanstack/react-query';
import { apiClient, type ChapterProgressSummary } from '../services/api';

export interface UseStoryProgressOptions {
  /**
   * Polling interval in milliseconds. Set to false to disable polling.
   * @default 3000 (3 seconds)
   */
  refetchInterval?: number | false;

  /**
   * Whether to refetch on window focus
   * @default true
   */
  refetchOnWindowFocus?: boolean;

  /**
   * Whether the query is enabled (can be used to conditionally enable/disable)
   * @default true
   */
  enabled?: boolean;
}

/**
 * Fetches real-time story progress for a user with automatic polling.
 *
 * @param userId - The user ID to fetch progress for
 * @param options - Query options including polling interval
 * @returns Query result with progress data
 */
export function useStoryProgress(
  userId: string | null,
  options: UseStoryProgressOptions = {}
): UseQueryResult<ChapterProgressSummary, Error> {
  const {
    refetchInterval = 3000, // Default: poll every 3 seconds
    refetchOnWindowFocus = true,
    enabled = true,
  } = options;

  return useQuery<ChapterProgressSummary, Error>({
    queryKey: ['storyProgress', userId],
    queryFn: async () => {
      if (!userId) {
        throw new Error('User ID is required');
      }
      return apiClient.getUserStoryProgress(userId);
    },
    enabled: enabled && !!userId,
    refetchInterval,
    refetchOnWindowFocus,
    // Keep previous data while refetching to prevent UI flicker
    placeholderData: (previousData) => previousData,
    // Stale time: data is fresh for 2 seconds, then becomes stale
    staleTime: 2000,
    // Cache time: keep unused data for 5 minutes
    gcTime: 5 * 60 * 1000,
  });
}

/**
 * Hook variant that only fetches once (no polling).
 * Useful for components that don't need real-time updates.
 */
export function useStoryProgressOnce(
  userId: string | null,
  enabled: boolean = true
): UseQueryResult<ChapterProgressSummary, Error> {
  return useStoryProgress(userId, {
    refetchInterval: false,
    refetchOnWindowFocus: false,
    enabled,
  });
}
