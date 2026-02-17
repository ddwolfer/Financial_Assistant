import { getLatestScreening } from '$lib/api';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
	const screening = await getLatestScreening('layer1_dual', fetch);
	return { screening };
};
