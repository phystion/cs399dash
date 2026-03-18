import { HF_TOKEN } from '$env/static/private';
import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

const HF_MODEL = 'distilbert-base-uncased-finetuned-sst-2-english';
const HF_API_URL = `https://api-inference.huggingface.co/models/${HF_MODEL}`;

export const POST: RequestHandler = async ({ request }) => {
	let body: unknown;
	try {
		body = await request.json();
	} catch {
		throw error(400, 'Invalid JSON');
	}

	if (!body || typeof body !== 'object' || !('text' in body)) {
		throw error(400, 'Missing text field');
	}

	const text = String((body as { text: unknown }).text).trim();
	if (!text) {
		throw error(400, 'text must not be empty');
	}

	const headers: Record<string, string> = { 'Content-Type': 'application/json' };
	if (HF_TOKEN && HF_TOKEN !== 'your_token_here') {
		headers['Authorization'] = `Bearer ${HF_TOKEN}`;
	}

	let resp: Response;
	try {
		resp = await fetch(HF_API_URL, {
			method: 'POST',
			headers,
			body: JSON.stringify({ inputs: text.slice(0, 512) })
		});
	} catch (e) {
		throw error(502, `HuggingFace API unreachable: ${e}`);
	}

	if (!resp.ok) {
		throw error(502, `HuggingFace API error: ${resp.status} ${resp.statusText}`);
	}

	const data: unknown = await resp.json();

	// HF returns [[{label, score}, ...]] for sequence classification
	let candidates: Array<{ label: string; score: number }>;
	if (Array.isArray(data) && Array.isArray(data[0])) {
		candidates = data[0];
	} else if (Array.isArray(data) && typeof data[0] === 'object') {
		candidates = data as Array<{ label: string; score: number }>;
	} else {
		throw error(502, 'Unexpected HuggingFace response shape');
	}

	const best = candidates.reduce((a, b) => (a.score >= b.score ? a : b));

	return json({
		label: best.label.toUpperCase() as 'POSITIVE' | 'NEGATIVE',
		score: Math.round(best.score * 10000) / 10000
	});
};
