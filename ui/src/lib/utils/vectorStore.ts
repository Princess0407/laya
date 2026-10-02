// Copyright 2026 Aayush Chawla
// SPDX-License-Identifier: Apache-2.0

import type { HealthResponse } from '$lib/api/types';

export type VectorStoreState = 'ready' | 'starting' | 'unavailable';

/**
 * Engine uptime (seconds) a vector store connect must outlast before the setup
 * banner appears. A warm launch connects within a few seconds of the engine
 * becoming ready, so it stays below this and never flashes the banner.
 */
export const SETUP_BANNER_MIN_UPTIME_S = 10;

/**
 * The vector store's state as reported by /health. An engine that does not
 * report the field is treated as ready, so the UI never warns about a store it
 * knows nothing about.
 */
export function vectorStoreState(health: HealthResponse | null): VectorStoreState {
	const status = health?.chromadb;
	if (status === 'starting') return 'starting';
	if (status === 'unhealthy') return 'unavailable';
	return 'ready';
}

/** True when the vector store is still connecting on a slow (cold) launch. */
export function showVectorStoreSetupBanner(health: HealthResponse | null): boolean {
	return (
		vectorStoreState(health) === 'starting' &&
		(health?.uptime_seconds ?? 0) >= SETUP_BANNER_MIN_UPTIME_S
	);
}
