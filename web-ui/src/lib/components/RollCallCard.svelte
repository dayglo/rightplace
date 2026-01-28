<script lang="ts">
	import type { RollCall } from '$lib/services/api';

	interface Props {
		rollCall: RollCall;
		verifiedCount: number;
		totalCount: number;
	}

	let { rollCall, verifiedCount, totalCount }: Props = $props();

	function formatDateTime(dateString: string): string {
		const date = new Date(dateString);
		return date.toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			hour: 'numeric',
			minute: '2-digit'
		});
	}

	function getStatusText(status: string): string {
		switch (status) {
			case 'completed':
				return 'Completed';
			case 'in_progress':
				return 'In Progress';
			case 'pending':
				return 'Pending';
			case 'cancelled':
				return 'Cancelled';
			default:
				return status;
		}
	}

	function getStatusColor(status: string): string {
		switch (status) {
			case 'completed':
				return 'text-green-600';
			case 'in_progress':
				return 'text-blue-600';
			case 'pending':
				return 'text-gray-600';
			case 'cancelled':
				return 'text-red-600';
			default:
				return 'text-gray-600';
		}
	}
</script>

<div class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
	<div class="flex items-start justify-between mb-2">
		<h4 class="text-lg font-semibold text-gray-900">{rollCall.name}</h4>
		<span class="text-sm font-medium {getStatusColor(rollCall.status)}">
			{getStatusText(rollCall.status)}
		</span>
	</div>
	<div class="flex items-center gap-4 text-sm text-gray-600">
		<span>{verifiedCount}/{totalCount} verified</span>
		<span>|</span>
		<span>{formatDateTime(rollCall.scheduled_time)}</span>
	</div>
</div>
