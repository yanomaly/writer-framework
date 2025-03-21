<template>
	<div ref="trigger" class="BuilderMoreDropdown">
		<WdsButton
			variant="neutral"
			size="smallIcon"
			:disabled="disabled"
			:custom-size="triggerCustomSize"
			@click="isOpen = !isOpen"
		>
			<i class="material-symbols-outlined">more_horiz</i>
		</WdsButton>
		<WdsDropdownMenu
			v-if="isOpen"
			ref="dropdown"
			class="BuilderMoreDropdown__dropdown"
			:options="options"
			:style="floatingStyles"
			@select="onSelect"
		/>
	</div>
</template>

<script lang="ts">
export type { WdsDropdownMenuOption as Option } from "@/wds/WdsDropdownMenu.vue";
</script>

<script setup lang="ts">
import {
	defineAsyncComponent,
	nextTick,
	PropType,
	ref,
	useTemplateRef,
	watch,
} from "vue";
import { useFloating, autoPlacement } from "@floating-ui/vue";
import type { WdsDropdownMenuOption } from "@/wds/WdsDropdownMenu.vue";
import { useFocusWithin } from "@/composables/useFocusWithin";
import WdsButton from "@/wds/WdsButton.vue";

const WdsDropdownMenu = defineAsyncComponent(
	() => import("@/wds/WdsDropdownMenu.vue"),
);

defineProps({
	options: {
		type: Array as PropType<WdsDropdownMenuOption[]>,
		default: () => [],
	},
	triggerCustomSize: { type: String, default: "smallIcon" },
	disabled: { type: Boolean },
	hideIcons: { type: Boolean, required: false },
});

const emits = defineEmits({
	select: (value: string) => typeof value === "string",
});

const isOpen = ref(false);
const trigger = useTemplateRef("trigger");
const dropdown = useTemplateRef("dropdown");

const { floatingStyles } = useFloating(trigger, dropdown, {
	placement: "bottom-end",
	middleware: [
		autoPlacement({ allowedPlacements: ["bottom-end", "top-end"] }),
	],
});

// close the dropdown when clicking outside
const hasFocus = useFocusWithin(trigger);
watch(
	hasFocus,
	() => {
		if (!hasFocus.value) {
			// wait next tick to let event propagate
			nextTick().then(() => (isOpen.value = false));
		}
	},
	{ immediate: true },
);

function onSelect(value: string) {
	isOpen.value = false;
	emits("select", value);
}
</script>

<style scoped>
.BuilderMoreDropdown {
	position: relative;
}
.BuilderMoreDropdown__dropdown {
	min-width: 150px;
}
</style>
