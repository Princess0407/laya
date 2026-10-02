// Copyright 2026 Aayush Chawla
// SPDX-License-Identifier: Apache-2.0

import { describe, it, expect } from 'vitest';
import type { HealthResponse } from '$lib/api/types';
import {
	SETUP_BANNER_MIN_UPTIME_S,
	showVectorStoreSetupBanner,
	vectorStoreState
} from './vectorStore';

function health(overrides: Partial<HealthResponse> = {}): HealthResponse {
	return {
		engine: 'healthy',
		sqlite: 'healthy',
		chromadb: 'healthy',
		n8n: 'healthy',
		uptime_seconds: 60,
		...overrides
	};
}

describe('vectorStoreState', () => {
	it('maps the /health chromadb field', () => {
		expect(vectorStoreState(health({ chromadb: 'healthy' }))).toBe('ready');
		expect(vectorStoreState(health({ chromadb: 'starting' }))).toBe('starting');
		expect(vectorStoreState(health({ chromadb: 'unhealthy' }))).toBe('unavailable');
	});

	it('treats a missing field or missing health as ready', () => {
		expect(vectorStoreState(health({ chromadb: undefined }))).toBe('ready');
		expect(vectorStoreState(null)).toBe('ready');
	});
});

describe('showVectorStoreSetupBanner', () => {
	it('stays hidden while a connect is still within the warm-launch window', () => {
		expect(
			showVectorStoreSetupBanner(
				health({ chromadb: 'starting', uptime_seconds: SETUP_BANNER_MIN_UPTIME_S - 1 })
			)
		).toBe(false);
	});

	it('shows once the connect outlasts the warm-launch window', () => {
		expect(
			showVectorStoreSetupBanner(
				health({ chromadb: 'starting', uptime_seconds: SETUP_BANNER_MIN_UPTIME_S })
			)
		).toBe(true);
	});

	it('is hidden when the store is ready, unavailable, or health is unknown', () => {
		expect(showVectorStoreSetupBanner(health({ chromadb: 'healthy' }))).toBe(false);
		expect(showVectorStoreSetupBanner(health({ chromadb: 'unhealthy' }))).toBe(false);
		expect(showVectorStoreSetupBanner(null)).toBe(false);
	});
});
