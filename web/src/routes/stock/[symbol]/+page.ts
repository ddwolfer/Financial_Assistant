import { getDeepAnalysis } from '$lib/api';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params, fetch }) => {
	const data = await getDeepAnalysis(params.symbol, fetch);
	return { analysis: data };
};
