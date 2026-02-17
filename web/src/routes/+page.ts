import { getLatestScreening, getDeepAnalysisSymbols } from '$lib/api';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
	const [screening, symbols] = await Promise.all([
		getLatestScreening('layer1_dual', fetch),
		getDeepAnalysisSymbols(fetch),
	]);

	return { screening, symbols };
};
