/**
 * API Client for Prison Roll Call Backend
 * 
 * Communicates with FastAPI backend at http://localhost:8000/api/v1
 */

const API_BASE = 'http://localhost:8000/api/v1';

/**
 * Generic fetch wrapper with error handling
 */
async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
	const url = `${API_BASE}${endpoint}`;
	
	try {
		const response = await fetch(url, {
			...options,
			headers: {
				'Content-Type': 'application/json',
				...options?.headers
			}
		});

		if (!response.ok) {
			const errorText = await response.text();
			throw new Error(`API Error (${response.status}): ${errorText}`);
		}

		return await response.json();
	} catch (error) {
		if (error instanceof Error) {
			throw error;
		}
		throw new Error('Unknown API error');
	}
}

// ============================================================================
// INMATES / PRISONERS
// ============================================================================

export interface Inmate {
	id: string;
	inmate_number: string;
	first_name: string;
	last_name: string;
	date_of_birth: string;
	cell_block: string;
	cell_number: string;
	is_enrolled: boolean;
	created_at: string;
	updated_at: string;
}

export interface CreateInmateRequest {
	inmate_number: string;
	first_name: string;
	last_name: string;
	date_of_birth: string;
	cell_block: string;
	cell_number: string;
}

export async function getInmates(): Promise<Inmate[]> {
	return fetchAPI<Inmate[]>('/inmates');
}

export async function getInmate(id: string): Promise<Inmate> {
	return fetchAPI<Inmate>(`/inmates/${id}`);
}

export async function createInmate(data: CreateInmateRequest): Promise<Inmate> {
	return fetchAPI<Inmate>('/inmates', {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

export async function updateInmate(id: string, data: Partial<CreateInmateRequest>): Promise<Inmate> {
	return fetchAPI<Inmate>(`/inmates/${id}`, {
		method: 'PUT',
		body: JSON.stringify(data)
	});
}

export async function deleteInmate(id: string): Promise<void> {
	await fetchAPI<void>(`/inmates/${id}`, {
		method: 'DELETE'
	});
}

// ============================================================================
// LOCATIONS
// ============================================================================

export interface Location {
	id: string;
	name: string;
	type: string;
	building: string;
	floor: number;
	capacity: number;
	parent_id?: string;
	created_at: string;
	updated_at: string;
}

export interface CreateLocationRequest {
	name: string;
	type: string;
	building: string;
	floor: number;
	capacity: number;
	parent_id?: string;
}

export async function getLocations(): Promise<Location[]> {
	return fetchAPI<Location[]>('/locations');
}

export async function getLocation(id: string): Promise<Location> {
	return fetchAPI<Location>(`/locations/${id}`);
}

export async function createLocation(data: CreateLocationRequest): Promise<Location> {
	return fetchAPI<Location>('/locations', {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

export async function updateLocation(id: string, data: Partial<CreateLocationRequest>): Promise<Location> {
	return fetchAPI<Location>(`/locations/${id}`, {
		method: 'PUT',
		body: JSON.stringify(data)
	});
}

export async function deleteLocation(id: string): Promise<void> {
	await fetchAPI<void>(`/locations/${id}`, {
		method: 'DELETE'
	});
}

// ============================================================================
// ROLL CALLS
// ============================================================================

export interface RouteStop {
	id: string;
	location_id: string;
	order: number;
	expected_inmates: string[];
	status?: 'pending' | 'current' | 'completed' | 'skipped';
}

export interface RollCall {
	id: string;
	name: string;
	scheduled_time: string;
	status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
	officer_id?: string;
	route: RouteStop[];
	started_at?: string;
	completed_at?: string;
	notes?: string;
	created_at: string;
	updated_at: string;
}

export interface RollCallSummary {
	id: string;
	name: string;
	status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled';
	scheduled_at: string;
	started_at?: string;
	completed_at?: string;
	officer_id: string;
	notes: string;
	// Statistics
	total_stops: number;
	expected_inmates: number;
	verified_inmates: number;
	progress_percentage: number;
}

export interface CreateRollCallRequest {
	name: string;
	scheduled_at: string;
	officer_id: string;
	route: RouteStop[];
	notes?: string;
}

export async function getRollCalls(): Promise<RollCallSummary[]> {
	return fetchAPI<RollCallSummary[]>('/rollcalls');
}

export async function getRollCall(id: string): Promise<RollCall> {
	return fetchAPI<RollCall>(`/rollcalls/${id}`);
}

export async function createRollCall(data: CreateRollCallRequest): Promise<RollCall> {
	return fetchAPI<RollCall>('/rollcalls', {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

export async function startRollCall(id: string): Promise<RollCall> {
	return fetchAPI<RollCall>(`/rollcalls/${id}/start`, {
		method: 'POST'
	});
}

export async function completeRollCall(id: string): Promise<RollCall> {
	return fetchAPI<RollCall>(`/rollcalls/${id}/complete`, {
		method: 'POST'
	});
}

// ============================================================================
// ROLL CALL GENERATION
// ============================================================================

export interface GenerateRollCallRequest {
	location_ids: string[];
	scheduled_at: string;
	include_empty?: boolean;
	name?: string;
	officer_id?: string;
}

export interface RouteStopSummary {
	order: number;
	location_id: string;
	location_name: string;
	location_type: string;
	building: string;
	floor: number;
	is_occupied: boolean;
	expected_count: number;
	walking_distance_meters: number;
	walking_time_seconds: number;
}

export interface GeneratedRollCallResponse {
	location_ids: string[];
	location_names: string[];
	scheduled_at: string;
	route: RouteStopSummary[];
	summary: {
		total_locations: number;
		occupied_locations: number;
		empty_locations: number;
		total_prisoners_expected: number;
		estimated_time_seconds: number;
	};
}

export async function generateRollCall(data: GenerateRollCallRequest): Promise<GeneratedRollCallResponse> {
	return fetchAPI<GeneratedRollCallResponse>('/rollcalls/generate', {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

// ============================================================================
// FACE ENROLLMENT
// ============================================================================

export interface EnrollmentResponse {
	success: boolean;
	inmate_id: string;
	embedding_id: string;
	quality_score: number;
	message: string;
}

export async function enrollFace(inmateId: string, imageData: string): Promise<EnrollmentResponse> {
	// Convert base64 to blob
	const base64Data = imageData.split(',')[1];
	const blob = await fetch(`data:image/jpeg;base64,${base64Data}`).then(r => r.blob());
	
	const formData = new FormData();
	formData.append('image', blob, 'enrollment.jpg');

	const response = await fetch(`${API_BASE}/enrollment/${inmateId}`, {
		method: 'POST',
		body: formData
	});

	if (!response.ok) {
		const errorText = await response.text();
		throw new Error(`Enrollment failed (${response.status}): ${errorText}`);
	}

	return await response.json();
}

// ============================================================================
// FACE VERIFICATION
// ============================================================================

export interface VerificationResult {
	matched: boolean;
	inmate_id?: string;
	inmate_name?: string;
	confidence: number;
	threshold: number;
	message: string;
}

export async function verifyFace(locationId: string, imageData: string): Promise<VerificationResult> {
	// Convert base64 to blob
	const base64Data = imageData.split(',')[1];
	const blob = await fetch(`data:image/jpeg;base64,${base64Data}`).then(r => r.blob());
	
	const formData = new FormData();
	formData.append('image', blob, 'verification.jpg');
	formData.append('location_id', locationId);

	const response = await fetch(`${API_BASE}/verify/quick`, {
		method: 'POST',
		body: formData
	});

	if (!response.ok) {
		const errorText = await response.text();
		throw new Error(`Verification failed (${response.status}): ${errorText}`);
	}

	return await response.json();
}

// ============================================================================
// VERIFICATION RECORDING
// ============================================================================

export interface RecordVerificationRequest {
	rollcall_id: string;
	location_id: string;
	inmate_id: string;
	verification_method: 'face_recognition' | 'manual_override';
	confidence_score?: number;
	notes?: string;
}

export interface VerificationRecord {
	id: string;
	rollcall_id: string;
	location_id: string;
	inmate_id: string;
	verification_method: string;
	confidence_score?: number;
	verified_at: string;
	notes?: string;
}

export async function recordVerification(data: RecordVerificationRequest): Promise<VerificationRecord> {
	return fetchAPI<VerificationRecord>(`/rollcalls/${data.rollcall_id}/verification`, {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

// ============================================================================
// VERIFICATION RECORDS
// ============================================================================

export interface Verification {
	id: string;
	roll_call_id: string;
	inmate_id: string;
	location_id: string;
	status: 'verified' | 'not_found' | 'wrong_location' | 'manual' | 'pending';
	confidence: number;
	photo_uri?: string;
	timestamp: string;
	is_manual_override: boolean;
	manual_override_reason?: string;
	notes: string;
}

export async function getRollCallVerifications(rollCallId: string): Promise<Verification[]> {
	return fetchAPI<Verification[]>(`/verifications/roll-call/${rollCallId}`);
}

// ============================================================================
// SCHEDULES
// ============================================================================

export interface ScheduleEntry {
	id: string;
	inmate_id: string;
	location_id: string;
	day_of_week: number; // 0=Monday, 6=Sunday
	start_time: string; // "HH:MM"
	end_time: string;
	activity_type: string; // "work", "education", "meal", etc.
	is_recurring: boolean;
	effective_date?: string;
	source: string;
	source_id?: string;
	created_at: string;
	updated_at: string;
}

export async function getInmateSchedule(inmateId: string): Promise<ScheduleEntry[]> {
	return fetchAPI<ScheduleEntry[]>(`/schedules/inmate/${inmateId}`);
}

// ============================================================================
// VERIFICATION RECORDS
// ============================================================================

export interface Verification {
	id: string;
	roll_call_id: string;
	inmate_id: string;
	location_id: string;
	status: 'verified' | 'not_found' | 'wrong_location' | 'manual' | 'pending';
	confidence: number;
	photo_uri?: string;
	timestamp: string;
	is_manual_override: boolean;
	manual_override_reason?: string;
	notes: string;
}

export async function getInmateVerifications(
	inmateId: string,
	limit?: number
): Promise<Verification[]> {
	const params = limit ? `?limit=${limit}` : '';
	return fetchAPI<Verification[]>(`/verifications/inmate/${inmateId}${params}`);
}

// ============================================================================
// HEALTH CHECK
// ============================================================================

export interface HealthStatus {
	status: string;
	timestamp: string;
}

export async function checkHealth(): Promise<HealthStatus> {
	return fetchAPI<HealthStatus>('/health');
}
