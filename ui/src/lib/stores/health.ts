// Copyright 2026 Aayush Chawla
// SPDX-License-Identifier: Apache-2.0

import { writable } from 'svelte/store';
import type { HealthResponse } from '$lib/api/types';
import { getEngineUrl, waitForEngineToken } from '$lib/config';
import { vectorStoreState } from '$lib/utils/vectorStore';

const ENGINE_URL = getEngineUrl();

const FAST_POLL_MS = 1500;
const SLOW_POLL_MS = 30000;

export const health = writable<HealthResponse | null>(null);
export const healthError = writable<boolean>(false);

/** True once the engine reports healthy (engine + sqlite) AND token is available. Stays true once set. */
export const startupReady = writable<boolean>(false);

/**
 * Set while the engine is healthy but this page has no engine API token, so
 * startup cannot complete. Holds the message the startup screen shows.
 */
export const engineAuthError = writable<string | null>(null);

const ENGINE_AUTH_ERROR_MESSAGE =
	'Laya could not get its engine access token. Try restarting the app.' +
	(import.meta.env?.DEV
		? " Browser dev mode: set VITE_LAYA_ENGINE_TOKEN in ui/.env.local to the engine's LAYA_ENGINE_TOKEN."
		: '');

let pollInterval: ReturnType<typeof setInterval> | null = null;
let pollMs = FAST_POLL_MS;
let startupMode = true;
// One token wait at a time: a wait can outlast the poll interval, and
// overlapping polls would otherwise each start their own.
let tokenWaitInFlight = false;
let tokenErrorLogged = false;

function setPollRate(ms: number) {
	if (!pollInterval || ms === pollMs) return;
	clearInterval(pollInterval);
	pollMs = ms;
	pollInterval = setInterval(fetchHealth, ms);
}

async function fetchHealth() {
	try {
		const resp = await fetch(`${ENGINE_URL}/health`);
		if (resp.ok) {
			const data: HealthResponse = await resp.json();
			health.set(data);
			healthError.set(false);

			// Once engine + sqlite are healthy, ensure token is ready before marking startup complete
			if (
				startupMode &&
				!tokenWaitInFlight &&
				data.engine === 'healthy' &&
				data.sqlite === 'healthy'
			) {
				tokenWaitInFlight = true;
				try {
					await waitForEngineToken();
					engineAuthError.set(null);
					startupReady.set(true);
					startupMode = false;
				} catch (err) {
					// Stay in startupMode; the next poll retries.
					if (!tokenErrorLogged) {
						tokenErrorLogged = true;
						console.error('Engine is healthy but no engine API token is available', err);
					}
					engineAuthError.set(ENGINE_AUTH_ERROR_MESSAGE);
				} finally {
					tokenWaitInFlight = false;
				}
			}

			// Poll fast during startup and while the vector store is still
			// connecting, so the UI reflects its completion promptly; otherwise
			// poll slowly.
			const settling = startupMode || vectorStoreState(data) === 'starting';
			setPollRate(settling ? FAST_POLL_MS : SLOW_POLL_MS);
		} else {
			healthError.set(true);
		}
	} catch {
		health.set(null);
		healthError.set(true);
	}
}

export function startHealthPolling() {
	stopHealthPolling();
	startupMode = true;
	fetchHealth(); // immediate first check
	pollMs = FAST_POLL_MS;
	pollInterval = setInterval(fetchHealth, pollMs);
}

export function stopHealthPolling() {
	if (pollInterval) {
		clearInterval(pollInterval);
		pollInterval = null;
	}
}
