/**
 * Utility functions for the web UI
 */

/**
 * Format a date string as "DD MMM YYYY"
 */
export function formatDate(dateStr: string): string {
	return new Date(dateStr).toLocaleDateString('en-GB', {
		day: 'numeric',
		month: 'short',
		year: 'numeric'
	});
}

/**
 * Format a datetime string as "HH:MM"
 */
export function formatTime(dateStr: string): string {
	return new Date(dateStr).toLocaleTimeString('en-GB', {
		hour: '2-digit',
		minute: '2-digit'
	});
}

/**
 * Calculate age from date of birth
 */
export function calculateAge(dob: string): number {
	const birthDate = new Date(dob);
	const today = new Date();
	let age = today.getFullYear() - birthDate.getFullYear();
	const monthDiff = today.getMonth() - birthDate.getMonth();
	if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
		age--;
	}
	return age;
}

/**
 * Format a timestamp as "X minutes/hours/days ago"
 */
export function timeAgo(timestamp: string): string {
	const now = new Date();
	const past = new Date(timestamp);
	const diffMs = now.getTime() - past.getTime();
	const diffMins = Math.floor(diffMs / 60000);
	const diffHours = Math.floor(diffMs / 3600000);
	const diffDays = Math.floor(diffMs / 86400000);

	if (diffMins < 1) return 'just now';
	if (diffMins < 60) return `${diffMins} minute${diffMins === 1 ? '' : 's'} ago`;
	if (diffHours < 24) return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;
	return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`;
}

/**
 * Get icon emoji for activity type
 */
export function getActivityIcon(activityType: string): string {
	const icons: Record<string, string> = {
		'work': '🏭',
		'education': '📚',
		'meal': '🍽️',
		'healthcare': '⚕️',
		'exercise': '🏃',
		'association': '👥',
		'gym': '🏋️',
		'visits': '👨‍👩‍👧',
		'chapel': '⛪',
		'programmes': '📋',
		'roll_check': '📋',
		'lock_up': '🔒',
		'unlock': '🔓'
	};
	return icons[activityType] || '📍';
}

/**
 * Get formatted name for activity type
 */
export function getActivityName(activityType: string): string {
	return activityType
		.split('_')
		.map(word => word.charAt(0).toUpperCase() + word.slice(1))
		.join(' ');
}

/**
 * Get day name from day number (0=Monday, 6=Sunday)
 */
export function getDayName(dayNum: number): string {
	const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
	return days[dayNum] || '';
}
