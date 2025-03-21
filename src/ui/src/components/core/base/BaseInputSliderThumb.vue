<template>
	<transition>
		<div
			v-show="isPopoverDisplayed"
			class="BaseInputRange__popover"
			:style="{ left: popoverLeft }"
		>
			<span class="BaseInputRange__popover__content">
				{{ displayValue }}
			</span>
		</div>
	</transition>
	<button
		ref="thumb"
		type="button"
		class="BaseInputRange__thumb"
		:style="{ left: thumbLeft }"
		aria-label="Use the arrow keys to increase or decrease the value."
		@keydown.left="updateValue(+model - step)"
		@keydown.right="updateValue(+model + step)"
		@mousedown="handleMouseDown"
	></button>
</template>

<script setup lang="ts">
import { computed, PropType, ref, toRef, useTemplateRef, watch } from "vue";
import { useNumberFormatByStep } from "./BaseInputSlider.utils";

const props = defineProps({
	min: { type: Number, default: 0 },
	max: { type: Number, default: 100 },
	step: { type: Number, default: 1 },
	sliderBoundingRect: {
		type: Object as PropType<DOMRect>,
		default: undefined,
	},
	popoverDisplayMode: {
		type: String as PropType<"always" | "onChange">,
		default: "onChange",
	},
});

defineExpose({ handleMouseDown, getOffsetLeft });

const model = defineModel("value", { type: Number, default: 50 });

const thumb = useTemplateRef("thumb");

const displayValue = useNumberFormatByStep(model, toRef(props, "step"));

const progress = computed(() => {
	if (typeof model.value !== "number") return 50;
	return ((model.value - props.min) / (props.max - props.min)) * 100;
});

const isPopoverDisplayed = ref(props.popoverDisplayMode === "always");
let popoverTimeout = null;

watch(toRef(props.popoverDisplayMode), () => {
	if (props.popoverDisplayMode === "always") isPopoverDisplayed.value = true;
});

function displayPopover() {
	if (props.popoverDisplayMode === "always") return;
	isPopoverDisplayed.value = true;

	if (popoverTimeout) {
		clearTimeout(popoverTimeout);
		popoverTimeout = null;
	}

	popoverTimeout = setTimeout(() => {
		isPopoverDisplayed.value = false;
		popoverTimeout = null;
	}, 1_000);
}

// clamp(0px, calc(62% - 9px), calc(100% - 18px))
const thumbLeft = computed(() => `${progress.value}%`);
const popoverLeft = computed(() => `${progress.value}%`);

function updateValue(value: number) {
	displayPopover();
	if (props.min !== undefined && value < props.min) return;
	if (props.max !== undefined && value > props.max) return;

	// round the value to the closest step
	const relativeValue = value - props.min;
	const stepIndex = Math.round(relativeValue / props.step);
	const roundedValue = props.min + stepIndex * props.step;

	if (model.value !== roundedValue) model.value = roundedValue;
}

function handleMouseDown(initialEvent: MouseEvent) {
	document.addEventListener("mousemove", onMouseMove);
	document.addEventListener("mouseup", onMouseUp);

	const sliderBoundingRect = props.sliderBoundingRect;

	// trigger immediate value update to handle user click
	onMouseMove(initialEvent);

	function onMouseMove(event: MouseEvent) {
		const progress =
			(event.x - sliderBoundingRect.left) /
			(sliderBoundingRect.right - sliderBoundingRect.left);

		if (progress > 1 || progress < 0) return;

		const value = (props.max - props.min) * progress + props.min;
		updateValue(value);
	}

	function onMouseUp() {
		document.removeEventListener("mouseup", onMouseUp);
		document.removeEventListener("mousemove", onMouseMove);
	}
}

function getOffsetLeft() {
	return thumb.value.offsetLeft;
}
</script>

<style scoped>
.BaseInputRange__thumb {
	border: none;

	height: 18px;
	width: 18px;
	border-radius: 50%;
	background-color: var(--thumb-color);

	position: absolute;
	top: 0;

	transition: box-shadow ease-in-out 0.5s;
	transform: translateX(-50%);
}

.BaseInputRange__thumb:active {
	box-shadow: 0 0 0 6px var(--thumb-shadow-color);
}

.BaseInputRange__thumb:focus-visible {
	box-shadow: 0 0 0 6px var(--thumb-shadow-color);
	outline: 1px solid blue;
	outline-offset: 2px;
}

.BaseInputRange__popover {
	position: absolute;
	top: -24px;
	font-size: 10px;
	z-index: 2;

	color: var(--popoverColor, white);

	background: var(--popover-bg-color);
	height: 18px;

	border-radius: 4px;

	display: flex;
	align-items: center;
	justify-content: center;
	padding: 0 4px;
	transform: translateX(-50%);

	min-width: 12px;
}

.BaseInputRange__popover::after {
	content: "";
	width: 0;
	height: 0;
	border-left: 4px solid transparent;
	border-right: 4px solid transparent;
	border-top: 5px solid var(--popover-bg-color);
	position: absolute;
	bottom: -5px;
	left: calc(50% - 4px);
}

.BaseInputRange__popover__content {
	overflow: hidden;
	text-overflow: ellipsis;
	text-align: center;
}

/* start invisible */
.v-enter-active,
.v-leave-active {
	transition: opacity 0.2s ease-in-out;
}

.v-enter-from,
.v-leave-to {
	opacity: 0;
}
</style>
