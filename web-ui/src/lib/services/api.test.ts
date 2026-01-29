import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import {
	getInmates,
	getInmate,
	createInmate,
	getLocations,
	getRollCalls,
	checkHealth,
	type Inmate,
	type Location,
	type RollCall,
	type HealthStatus
} from './api';

describe('API Service', () => {
	beforeEach(() => {
		// Mock global fetch
		global.fetch = vi.fn();
	});

	afterEach(() => {
		vi.restoreAllMocks();
	});

	describe('Health Check', () => {
		it('should fetch health status', async () => {
			const mockHealth: HealthStatus = {
				status: 'healthy',
				timestamp: '2026-01-28T17:00:00Z'
			};

			(global.fetch as any).mockResolvedValueOnce({
				ok: true,
				json: async () => mockHealth
			});

			const result = await checkHealth();

			expect(global.fetch).toHaveBeenCalledWith(
				'http://localhost:8000/api/v1/health',
				expect.objectContaining({
					headers: expect.objectContaining({
						'Content-Type': 'application/json'
					})
				})
			);
			expect(result).toEqual(mockHealth);
		});
	});

	describe('Inmates API', () => {
		it('should fetch all inmates', async () => {
			const mockInmates: Inmate[] = [
				{
					id: '1',
					inmate_number: 'A12345',
					first_name: 'John',
					last_name: 'Doe',
					date_of_birth: '1990-01-01',
					cell_block: 'A',
					cell_number: '101',
					is_enrolled: true,
					created_at: '2026-01-01T00:00:00Z',
					updated_at: '2026-01-01T00:00:00Z'
				}
			];

			(global.fetch as any).mockResolvedValueOnce({
				ok: true,
				json: async () => mockInmates
			});

			const result = await getInmates();

			expect(global.fetch).toHaveBeenCalledWith(
				'http://localhost:8000/api/v1/inmates',
				expect.any(Object)
			);
			expect(result).toEqual(mockInmates);
		});

		it('should fetch single inmate by id', async () => {
			const mockInmate: Inmate = {
				id: '1',
				inmate_number: 'A12345',
				first_name: 'John',
				last_name: 'Doe',
				date_of_birth: '1990-01-01',
				cell_block: 'A',
				cell_number: '101',
				is_enrolled: true,
				created_at: '2026-01-01T00:00:00Z',
				updated_at: '2026-01-01T00:00:00Z'
			};

			(global.fetch as any).mockResolvedValueOnce({
				ok: true,
				json: async () => mockInmate
			});

			const result = await getInmate('1');

			expect(global.fetch).toHaveBeenCalledWith(
				'http://localhost:8000/api/v1/inmates/1',
				expect.any(Object)
			);
			expect(result).toEqual(mockInmate);
		});

		it('should create new inmate', async () => {
			const newInmate = {
				inmate_number: 'A12346',
				first_name: 'Jane',
				last_name: 'Smith',
				date_of_birth: '1992-05-15',
				cell_block: 'B',
				cell_number: '202'
			};

			const mockResponse: Inmate = {
				id: '2',
				...newInmate,
				is_enrolled: false,
				created_at: '2026-01-28T17:00:00Z',
				updated_at: '2026-01-28T17:00:00Z'
			};

			(global.fetch as any).mockResolvedValueOnce({
				ok: true,
				json: async () => mockResponse
			});

			const result = await createInmate(newInmate);

			expect(global.fetch).toHaveBeenCalledWith(
				'http://localhost:8000/api/v1/inmates',
				expect.objectContaining({
					method: 'POST',
					body: JSON.stringify(newInmate)
				})
			);
			expect(result).toEqual(mockResponse);
		});

		it('should handle API errors', async () => {
			(global.fetch as any).mockResolvedValueOnce({
				ok: false,
				status: 500,
				text: async () => 'Internal Server Error'
			});

			await expect(getInmates()).rejects.toThrow('API Error (500): Internal Server Error');
		});
	});

	describe('Locations API', () => {
		it('should fetch all locations', async () => {
			const mockLocations: Location[] = [
				{
					id: '1',
					name: 'Block A',
					type: 'block',
					building: 'Main',
					floor: 1,
					capacity: 50,
					created_at: '2026-01-01T00:00:00Z',
					updated_at: '2026-01-01T00:00:00Z'
				}
			];

			(global.fetch as any).mockResolvedValueOnce({
				ok: true,
				json: async () => mockLocations
			});

			const result = await getLocations();

			expect(global.fetch).toHaveBeenCalledWith(
				'http://localhost:8000/api/v1/locations',
				expect.any(Object)
			);
			expect(result).toEqual(mockLocations);
		});
	});

	describe('Roll Calls API', () => {
		it('should fetch all roll calls', async () => {
			const mockRollCalls: RollCall[] = [
				{
					id: '1',
					name: 'Morning Roll Call',
					scheduled_time: '2026-01-28T09:00:00Z',
					status: 'pending',
					route: [],
					created_at: '2026-01-28T08:00:00Z',
					updated_at: '2026-01-28T08:00:00Z'
				}
			];

			(global.fetch as any).mockResolvedValueOnce({
				ok: true,
				json: async () => mockRollCalls
			});

			const result = await getRollCalls();

			expect(global.fetch).toHaveBeenCalledWith(
				'http://localhost:8000/api/v1/rollcalls',
				expect.any(Object)
			);
			expect(result).toEqual(mockRollCalls);
		});
	});
});
