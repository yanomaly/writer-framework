<template>
	<div class="SharedControlBar">
		<button
			v-if="props.copyStructuredContent"
			class="control-button"
			@click="copyToClipboard({ text: props.copyStructuredContent })"
		>
			Copy JSON
		</button>
		<button
			v-if="props.copyRawContent"
			class="control-button"
			@click="copyToClipboard({ text: props.copyRawContent })"
		>
			Copy
		</button>
	</div>
</template>

<script setup lang="ts">
import { useLogger } from "@/composables/useLogger";

const props = defineProps<{
	copyRawContent?: string;
	copyStructuredContent?: string;
}>();

function copyToClipboard({ text = "" }: { text?: string }) {
	try {
		navigator.clipboard.writeText(text);
	} catch (error) {
		useLogger().error(error);
	}
}
</script>

<style scoped>
.SharedControlBar {
	margin-top: 8px;
	display: flex;
	flex-direction: row;
	justify-content: flex-end;
	gap: 8px;
}

.control-button {
	background-color: var(--buttonColor);
	border: none;
	border-radius: 8px;
	color: white;
	cursor: pointer;
	font-size: 11px;
	padding: 4px 8px;

	&:hover {
		opacity: 0.9;
	}
}
</style>
